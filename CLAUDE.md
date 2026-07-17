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
uv run flock validate
uv run flock design --output results/design.json
uv run flock estimate --scenario pilot
uv run flock verify-run results/<run-id>
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
- `experiments/design.py` — complete MPHIQ and prompt-pressure generators.
- `experiments/verify.py` — scaffold readiness and fail-closed run verification.
- `analysis/` — convergence + coordination metrics, stats (permutation/bootstrap/Holm), report.
- `interpretability/` — black-box input interventions and local causal activation hooks.

## Hard rules

- **Determinism is a feature, not a nicety.** Every random draw takes a seed derived from the
  run seed. Never add unseeded randomness or wall-clock-dependent behavior to the pipeline.
- **Pre-registration discipline.** After `docs/research/06-preregistration.md` is frozen
  (tag `prereg-v1`), metric/exclusion-rule changes require an amendment entry there.
- **Offline-first.** `flock run` + `flock analyze` must work with zero API keys and zero
  network. Network happens only in `flock data build` and real-provider calls.
- **Manifests over memory.** Anything a result depends on (config, dataset hash, git SHA,
  model params) goes in the run manifest.
- **No pseudoreplication.** Calls, steps, agent pairs, prompt paraphrases, and overlapping windows
  are not independent evidence. Confirmatory inference starts from independent blocks/markets.
- **No causal inflation.** Rationale is not a mechanism; an AI-like signature is not AI exposure;
  exposure without a credible counterfactual is not real-market causation.
- Datasets/results payloads are gitignored; manifests are checked in.
- `src/flock/logging_/` has the underscore to avoid shadowing stdlib `logging`.
- **iCloud quirk — `UV_NO_EDITABLE=1` is load-bearing.** This repo lives in an iCloud-synced
  folder. iCloud keeps re-applying macOS's `hidden` flag to files in `.venv`, and modern
  CPython's site.py silently skips hidden `.pth` files, which breaks *editable* installs
  intermittently (`ModuleNotFoundError: flock` from `uv run`). Fix: install non-editable.
  `.claude/settings.json` sets `UV_NO_EDITABLE=1` for Claude sessions; human shells should
  export it too (see README). Consequence: uv rebuilds the wheel on source changes — normal.
  iCloud can also evict repo files under disk pressure (reads fail with "Operation canceled"
  or time out); `brctl download <path>` re-materializes them.
