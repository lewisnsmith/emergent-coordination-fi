# flock — repo guide for Claude sessions

Experiment zone measuring strategy convergence and emergent coordination in LLM trading agents.
Before changing experiment logic, read `docs/research/research-question.md` and
`docs/research/experimental-design.md`; the code serves that design.

## Stack

Python 3.12; `uv`; pydantic v2; pandas + pyarrow; typer; pytest; ruff; pyright. Run tools via
`uv run`.

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
- `markets/exchange.py` — Phase 2: step-synchronous intra-step order book; H5 remains gated.
- `experiments/runner.py` — one run: cohort × market × steps → `results/<run-id>/`.
- `experiments/design.py` — complete MPHIQ and prompt-pressure generators.
- `experiments/verify.py` — scaffold readiness and fail-closed run verification.
- `analysis/` — convergence + coordination metrics, stats (permutation/bootstrap/Holm), report.
- `interpretability/` — black-box input interventions and local causal activation hooks.

## Hard rules

- **Determinism is a feature, not a nicety.** Every random draw takes a seed derived from the
  run seed. Never add unseeded randomness or wall-clock-dependent behavior to the pipeline.
- **Pre-registration discipline.** After `docs/research/preregistration.md` is frozen
  (tag `prereg-v1`), metric/exclusion-rule changes require an amendment entry there.
- **Offline-first.** `flock run` + `flock analyze` must work with zero API keys and zero
  network. Network happens only in `flock data build` and real-provider calls.
- **Manifests over memory.** Record every result dependency (config, dataset hash, git SHA,
  model params) in the local run manifest. Payloads and run manifests are gitignored;
  `datasets/manifests.json` is the checked-in input registry.
- **No pseudoreplication.** Calls, steps, agent pairs, prompt paraphrases, and overlapping windows
  are not independent evidence. Confirmatory inference starts from independent blocks/markets.
- **No causal inflation.** Rationale is not a mechanism; an AI-like signature is not AI exposure;
  exposure without a credible counterfactual is not real-market causation.
- `src/flock/logging_/` has the underscore to avoid shadowing stdlib `logging`.
- **iCloud quirk — `UV_NO_EDITABLE=1` is load-bearing.** Hidden `.pth` files make editable
  installs fail intermittently, so `.claude/settings.json` selects non-editable installs and
  human shells must export the variable too. Wheel rebuilds after source changes are normal.
  If iCloud evicts a file (`Operation canceled` or timeout), run `brctl download <path>`.
