"""Experiment runner: one config + one seed -> results/<run-id>/.

Loop per step: identical market state -> per-agent Observation (portfolio
attached) -> decide -> constraint clipping -> submit -> market.step() fills ->
ledgers updated -> portfolio snapshot logged.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from flock.agents.baselines import make_baseline
from flock.agents.cache import ResponseCache
from flock.agents.llm_agent import LLMAgent
from flock.agents.providers.base import make_chat_model
from flock.core.config import ExperimentConfig, load_experiment, load_models, load_persona
from flock.core.types import Observation
from flock.data import schemas
from flock.data.registry import Registry
from flock.experiments.ledger import Ledger
from flock.logging_.decisions import RESULTS_DIR, RunWriter, git_sha
from flock.markets.replay import ReplayMarket


@dataclass
class RunResult:
    run_id: str
    run_dir: Path
    n_steps: int
    n_agents: int


def make_run_id(cfg: ExperimentConfig) -> str:
    return f"{cfg.name}-s{cfg.seed}-{cfg.config_hash()[:8]}"


def build_market(cfg: ExperimentConfig, registry: Registry):
    entry = registry.get(cfg.dataset)
    ds_dir = Path(entry.path)
    bars = schemas.read_bars(ds_dir)
    events = schemas.read_events(ds_dir)
    if cfg.market.kind == "replay":
        market = ReplayMarket(
            bars,
            events,
            observation_window=cfg.observation_window,
            fee_bps=cfg.market.fee_bps,
            slippage_bps=cfg.market.slippage_bps,
            max_steps=cfg.steps,
        )
    else:
        from flock.markets.exchange import ExchangeMarket

        market = ExchangeMarket(
            bars,
            events,
            observation_window=cfg.observation_window,
            fee_bps=cfg.market.fee_bps,
            tick_size=cfg.market.tick_size,
            max_steps=cfg.steps,
        )
    return market, entry


def build_agents(cfg: ExperimentConfig, cache: ResponseCache | None):
    """Instantiate all cohorts; deterministic per-agent seeding from cfg.seed."""
    models = load_models()
    agents = []
    for ci, cohort in enumerate(cfg.cohorts):
        for gi, group in enumerate(cohort.agents):
            for i in range(group.count):
                agent_seed = np.random.SeedSequence([cfg.seed, ci, gi, i])
                rng = np.random.default_rng(agent_seed)
                if group.kind == "llm":
                    if group.model is None or group.persona is None:
                        raise ValueError("llm agent groups need 'model' and 'persona'")
                    spec = models[group.model]
                    agent_id = f"{cohort.name}-{group.model}-{group.persona}-{i}"
                    agents.append(
                        LLMAgent(
                            agent_id,
                            cohort.name,
                            make_chat_model(group.model, spec),
                            load_persona(group.persona),
                            temperature=group.temperature,
                            seed=int(rng.integers(0, 2**31)),
                            max_tokens=spec.max_tokens,
                            memory=group.memory,
                            cache=cache,
                        )
                    )
                else:
                    agent_id = f"{cohort.name}-{group.kind}-{i}"
                    agents.append(
                        make_baseline(group.kind, agent_id, cohort.name, rng, group.params or None)
                    )
    return agents


def run_experiment(
    config_path: Path,
    seed_override: int | None = None,
    results_root: Path = RESULTS_DIR,
    use_cache: bool = True,
) -> RunResult:
    cfg = load_experiment(config_path)
    if seed_override is not None:
        cfg = cfg.model_copy(update={"seed": seed_override})

    registry = Registry()
    market, dataset_entry = build_market(cfg, registry)
    cache = ResponseCache() if use_cache else None
    agents = build_agents(cfg, cache)
    ledgers = {
        a.agent_id: Ledger(cfg.initial_cash, cfg.max_position_per_symbol, cfg.market.fee_bps)
        for a in agents
    }

    run_id = make_run_id(cfg)
    writer = RunWriter(run_id, results_root)
    t_start = time.time()

    n_steps = 0
    total_cost = 0.0
    while not market.done:
        state = market.state()
        for agent in agents:
            ledger = ledgers[agent.agent_id]
            obs = Observation(
                step=state.step,
                ts=state.ts,
                symbols=state.symbols,
                bars=state.bars,
                prices=state.prices,
                news=state.news,
                portfolio=ledger.view(state.prices),
            )
            decision = agent.decide(obs)
            total_cost += decision.usage.cost_usd
            clipped = ledger.clip_orders(decision.orders, state.prices)
            market.submit(agent.agent_id, clipped)
            writer.log_decision(decision, obs, agent.describe(), agent.cohort, clipped)

        fills = market.step()
        for fill in fills:
            ledgers[fill.agent_id].apply(fill)
            writer.log_fill(fill)

        mark_prices = state.prices if market.done else market.state().prices
        mark_ts = state.ts if market.done else market.state().ts
        for agent in agents:
            ledger = ledgers[agent.agent_id]
            writer.log_portfolio(
                n_steps,
                mark_ts,
                agent.agent_id,
                agent.cohort,
                ledger.cash,
                ledger.equity(mark_prices),
                ledger.weights(mark_prices),
            )
        n_steps += 1

    manifest = {
        "run_id": run_id,
        "config": cfg.model_dump(),
        "config_hash": cfg.config_hash(),
        "git_sha": git_sha(),
        "dataset": {
            "name": dataset_entry.name,
            "version": dataset_entry.version,
            "sha256": dataset_entry.sha256,
        },
        "n_steps": n_steps,
        "n_agents": len(agents),
        "agents": {a.agent_id: {"cohort": a.cohort, **a.describe()} for a in agents},
        "wall_time_s": round(time.time() - t_start, 2),
        "total_cost_usd": total_cost,
    }
    writer.finalize(manifest)
    return RunResult(run_id, writer.run_dir, n_steps, len(agents))
