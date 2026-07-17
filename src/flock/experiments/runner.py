"""Experiment runner: one config + one seed -> results/<run-id>/.

Loop per step: identical market state -> per-agent Observation (portfolio
attached) -> decide -> constraint clipping -> submit -> market.step() fills ->
ledgers updated -> portfolio snapshot logged.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from flock.agents.baselines import make_baseline
from flock.agents.cache import ResponseCache
from flock.agents.llm_agent import LLMAgent
from flock.agents.prompts import resolve_prompt
from flock.agents.providers.base import make_chat_model
from flock.core.config import ExperimentConfig, load_experiment, load_models, load_persona
from flock.core.types import Observation
from flock.data import schemas
from flock.data.registry import Registry
from flock.experiments.budget import RuntimeBudgetGuard
from flock.experiments.ledger import Ledger
from flock.experiments.treatments import apply_information_policy
from flock.logging_.decisions import RESULTS_DIR, RunWriter, git_sha
from flock.markets.exchange import ExchangeMarket
from flock.markets.replay import ReplayMarket


@dataclass
class RunResult:
    run_id: str
    run_dir: Path
    n_steps: int
    n_agents: int


def resolved_config_hash(cfg: ExperimentConfig) -> str:
    """Hash config plus resolved model specs and persona content."""
    models = load_models()
    model_keys = sorted(
        {
            group.model
            for cohort in cfg.cohorts
            for group in cohort.agents
            if group.kind == "llm" and group.model is not None
        }
    )
    persona_keys = sorted(
        {
            group.persona
            for cohort in cfg.cohorts
            for group in cohort.agents
            if group.kind == "llm" and group.persona is not None
        }
    )
    payload = {
        "config": cfg.model_dump(),
        "models": {key: models[key].model_dump() for key in model_keys},
        "personas": {key: load_persona(key).model_dump() for key in persona_keys},
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode()).hexdigest()


def make_run_id(cfg: ExperimentConfig) -> str:
    return f"{cfg.name}-s{cfg.seed}-{resolved_config_hash(cfg)[:8]}"


def build_market(cfg: ExperimentConfig, registry: Registry):
    entry = registry.get(cfg.dataset)
    ds_dir = registry.dataset_dir(entry.name)
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
        market = ExchangeMarket(
            bars,
            events,
            observation_window=cfg.observation_window,
            fee_bps=cfg.market.fee_bps,
            tick_size=cfg.market.tick_size,
            max_steps=cfg.steps,
            seed=cfg.seed,
        )
    return market, entry


def build_agents(
    cfg: ExperimentConfig,
    cache: ResponseCache | None,
    budget: RuntimeBudgetGuard | None = None,
):
    """Instantiate all cohorts; deterministic per-agent seeding from cfg.seed."""
    models = load_models()
    agents = []
    for ci, cohort in enumerate(cfg.cohorts):
        id_offsets: dict[tuple[str, str | None, str | None], int] = {}
        for gi, group in enumerate(cohort.agents):
            id_key = (group.kind, group.model, group.persona)
            id_offset = id_offsets.get(id_key, 0)
            for i in range(group.count):
                agent_seed = np.random.SeedSequence([cfg.seed, ci, gi, i])
                rng = np.random.default_rng(agent_seed)
                instance_index = id_offset + i
                if group.kind == "llm":
                    if group.model is None or group.persona is None:
                        raise ValueError("llm agent groups need 'model' and 'persona'")
                    spec = models[group.model]
                    if cfg.model_policy == "frontier_only" and not spec.frontier_eligible:
                        raise ValueError(f"model '{group.model}' is not frontier eligible")
                    if cfg.model_policy == "mock_only" and spec.provider != "mock":
                        raise ValueError(f"model '{group.model}' is not a mock model")
                    agent_id = (
                        f"{cohort.name}-{group.model}-{group.persona}-{instance_index}"
                    )
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
                            grounding_mode=group.grounding_mode,
                            prompt_id=group.prompt_id,
                            task_prompt=resolve_prompt(group.prompt_id),
                            information_policy=group.information_policy,
                            harness_id=group.harness_id,
                            cache=cache,
                            before_request=budget.before_request if budget else None,
                            record_response=budget.record_response if budget else None,
                            record_failure=budget.record_failure if budget else None,
                        )
                    )
                else:
                    agent_id = f"{cohort.name}-{group.kind}-{instance_index}"
                    agents.append(
                        make_baseline(group.kind, agent_id, cohort.name, rng, group.params or None)
                    )
            id_offsets[id_key] = id_offset + group.count
    return agents


def log_exchange_events(writer: RunWriter, market: ExchangeMarket) -> None:
    """Persist enough exchange state to reconstruct the tape and endogenous bars."""
    for trade in market.last_step_trades:
        writer.log_market_event({"event_type": "trade", **asdict(trade)})
    for symbol, sides in market.last_book_snapshot.items():
        for side, orders in sides.items():
            for order in orders:
                payload = asdict(order)
                writer.log_market_event(
                    {
                        "event_type": "resting_order_snapshot",
                        "step": market.last_completed_step,
                        **payload,
                    }
                )
                writer.log_market_event(
                    {
                        "event_type": "expiry",
                        "reason": "step_end",
                        "step": market.last_completed_step,
                        "symbol": symbol,
                        "side": side,
                        **payload,
                    }
                )
    for bar in market.last_step_bars:
        writer.log_market_event(
            {
                "event_type": "endogenous_bar",
                "step": market.last_completed_step,
                **asdict(bar),
            }
        )


def run_experiment(
    config_path: Path,
    seed_override: int | None = None,
    results_root: Path = RESULTS_DIR,
    use_cache: bool = True,
) -> RunResult:
    cfg = load_experiment(config_path)
    if seed_override is not None:
        cfg = cfg.model_copy(update={"seed": seed_override})
    return run_config(cfg, results_root=results_root, use_cache=use_cache)


def run_config(
    cfg: ExperimentConfig,
    results_root: Path = RESULTS_DIR,
    use_cache: bool = True,
) -> RunResult:
    run_id = make_run_id(cfg)
    completed_manifest = results_root / run_id / "manifest.json"
    if completed_manifest.exists():
        manifest = json.loads(completed_manifest.read_text())
        return RunResult(
            run_id,
            completed_manifest.parent,
            manifest["n_steps"],
            manifest["n_agents"],
        )

    registry = Registry()
    market, dataset_entry = build_market(cfg, registry)
    cache = ResponseCache() if use_cache else None
    budget = RuntimeBudgetGuard(cfg.runtime_budget) if cfg.runtime_budget else None
    agents = build_agents(cfg, cache, budget)
    ledgers = {
        a.agent_id: Ledger(cfg.initial_cash, cfg.max_position_per_symbol, cfg.market.fee_bps)
        for a in agents
    }
    if cfg.initial_position_per_symbol > 0:
        prices0 = market.state().prices
        for ledger in ledgers.values():
            for symbol, price in prices0.items():
                ledger.qty[symbol] = cfg.initial_position_per_symbol
                ledger.avg_price[symbol] = price

    writer = RunWriter(run_id, results_root)
    t_start = time.time()

    n_steps = 0
    total_cost = 0.0
    try:
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
                if getattr(agent, "kind", "") == "llm":
                    obs = apply_information_policy(obs, agent.information_policy)
                decision = agent.decide(obs)
                total_cost += decision.usage.cost_usd
                clipped = ledger.clip_orders(decision.orders, state.prices)
                market.submit(agent.agent_id, clipped)
                writer.log_decision(decision, obs, agent.describe(), agent.cohort, clipped)

            fills = market.step()
            if isinstance(market, ExchangeMarket):
                log_exchange_events(writer, market)
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
            writer.checkpoint(n_steps, total_cost)
    except BaseException as error:
        if budget is not None:
            writer.checkpoint(n_steps, budget.snapshot().cost_usd)
        writer.fail(error)
        raise

    manifest = {
        "run_id": run_id,
        "config": cfg.model_dump(),
        "config_hash": cfg.config_hash(),
        "resolved_config_hash": resolved_config_hash(cfg),
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
        "runtime_budget": budget.manifest_payload() if budget is not None else None,
    }
    writer.finalize(manifest)
    return RunResult(run_id, writer.run_dir, n_steps, len(agents))
