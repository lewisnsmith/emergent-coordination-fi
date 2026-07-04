# flock — repo guide for Claude sessions

Experiment zone measuring strategy convergence / emergent coordination in LLM trading agents.
Read `docs/research/01-research-question.md` and `02-experimental-design.md` before touching
experiment logic — the code exists to serve that design.

## Stack

Python 3.12, `uv` (run everything via `uv run`), pydantic v2 configs, pandas+pyarrow data,
typer CLI, pytest, ruff (no mypy configured — don't claim type-check success, run
`uv run ruff check .` instead).

## Commands

```bash
uv sync                                   # install (mock pipeline needs no API keys)
uv sync --extra providers --extra data    # real models + real data builders
uv run flock data build synthetic         # build seeded synthetic dataset
uv run flock run configs/experiments/exp-000-smoke.yaml
uv run flock analyze latest [--paper]
uv run pytest && uv run ruff check .      # required before claiming done
```

## Architecture (one line each)

- `core/types.py` — Bar, Observation, Order, Fill, Decision, Position. Everything speaks these.
- `core/config.py` — pydantic schemas for experiment/sweep YAML in `configs/`.
- `agents/base.py` — `TradingAgent` protocol: `decide(Observation) -> Decision`.
- `agents/baselines/` — momentum, mean-reversion, market-maker, buy-hold, random.
- `agents/llm_agent.py` — prompt assembly (persona + rendered market state) + JSON parsing;
  malformed → retry once → `hold` with `parse_ok=false` (pre-registered rule, don't change).
- `agents/providers/` — `ChatModel` interface; mock (deterministic), anthropic, openai, google,
  openai_compatible. SDKs are lazy-imported; core pipeline must run without them.
- `agents/cache.py` — content-addressed LLM response cache in `.flock-cache/`.
- `markets/replay.py` — Phase 1: no interaction, no impact, next-bar fills.
- `markets/exchange.py` — Phase 2: continuous double auction, price-time priority.
- `experiments/runner.py` — one run: cohort × market × steps → `results/<run-id>/`.
- `analysis/` — convergence + coordination metrics, stats (permutation/bootstrap/Holm), report.

## Hard rules

- **Determinism is a feature, not a nicety.** Every random draw takes a seed derived from the
  run seed. Never add unseeded randomness or wall-clock-dependent behavior to the pipeline.
- **Pre-registration discipline.** After `docs/research/06-preregistration.md` is frozen
  (tag `prereg-v1`), metric/exclusion-rule changes require an amendment entry there.
- **Offline-first.** `flock run` + `flock analyze` must work with zero API keys and zero
  network. Network happens only in `flock data build` and real-provider calls.
- **Manifests over memory.** Anything a result depends on (config, dataset hash, git SHA,
  model params) goes in the run manifest.
- Datasets/results payloads are gitignored; manifests are checked in.
- `src/flock/logging_/` has the underscore to avoid shadowing stdlib `logging`.
- **Python is pinned to 3.12 (`.python-version`) — do not bump to 3.13.** This repo lives in an
  iCloud-synced folder; iCloud propagates macOS's `hidden` flag into `.venv`, and Python 3.13's
  site.py silently skips hidden `.pth` files, breaking the editable install
  (`ModuleNotFoundError: flock`). If that ever bites: `chflags -R nohidden .venv`.
