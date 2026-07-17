# flock

**Do LLM-powered trading agents converge on similar trading strategies to a greater extent than
current market infrastructure?**

flock is an experiment zone for measuring *strategy convergence* and *emergent coordination* in
LLM trading agents, compared against classical algorithmic baselines and empirical dispersion of
real-world traders. It sweeps across markets (equities, prediction markets), model providers,
harness parameters, personas/demographic instructions, and information sets — and produces
publishable decision-log datasets for agents in finance.

See [`docs/research/`](docs/research/) and the machine-readable
[`configs/research-program.yaml`](configs/research-program.yaml) for the full H1–H12 program:

- [01 – Research question](docs/research/01-research-question.md)
- [02 – Experimental design](docs/research/02-experimental-design.md)
- [03 – Metrics](docs/research/03-metrics.md)
- [04 – Datasets](docs/research/04-datasets.md)
- [05 – Follow-up questions](docs/research/05-follow-up-questions.md)
- [06 – Pre-registration](docs/research/06-preregistration.md)
- [07 – Related work](docs/research/07-related-work.md)
- [09–12 – MPHIQ, profiles, prompt pressure, and statistics](docs/research/09-mphiq-factorial-design.md)
- [13–17 – safeguards, markets/trust, interpretability, attribution, outputs](docs/research/13-grounding-and-logical-verification.md)
- [18 – cost and execution runbook](docs/research/18-cost-and-execution-runbook.md)

## Current readiness

The research scaffold covers 13 hypotheses (H1–H12 plus H2b), 25 experiment protocols, all 32
MPHIQ schemes, 24 prompt-pressure cells, 24 diverse profiles, and six frontier endpoints. Only
the synthetic dataset is currently acquired. Run the preflight rather than inferring readiness
from the presence of config files:

```bash
uv run flock validate
uv run flock design --output results/design.json
uv run flock estimate --scenario pilot
```

`scaffold_ok=true` means the repository contracts are internally consistent.
`execution_ready=false` lists missing real datasets, approvals, exposure evidence, or runners.

## Quickstart (no API keys required)

The whole pipeline runs offline with deterministic mock models:

```bash
uv sync
uv run flock data build synthetic          # build a seeded synthetic equities dataset
uv run flock run configs/experiments/exp-000-smoke.yaml
uv run flock verify-run results/<run-id>
uv run flock analyze latest                # convergence report with bootstrap CIs
```

Do not start a real-model sweep until `flock validate` has no relevant blocker and the draft
preregistration is frozen. Real-model runs need provider keys and the extras:

```bash
uv sync --extra providers --extra data
uv run flock data build equities --symbols AAPL,MSFT,NVDA --start 2023-01-01 --end 2024-12-31
uv run flock run configs/experiments/exp-001-replay-equities.yaml
```

## How it works

```
Phase 1 (Replay):                      Phase 2 (Shared exchange):
  data ──▶ Agent A ──▶ trades_A          Agent A ─┐
  data ──▶ Agent B ──▶ trades_B          Agent B ─┼─▶ [order book] ─▶ price impact
  data ──▶ Agent C ──▶ trades_C          Agent C ─┘        ▲              │
  (no interaction; isolates                                └── feedback ──┘
   strategy convergence)               (herding has price impact; tests
                                        emergent coordination)
```

Every run pits an **LLM cohort** against a **baseline cohort** (momentum, mean-reversion,
market-making, buy-and-hold, random) under identical conditions, then measures within-cohort
dispersion of decisions, positions, and strategy fingerprints. Real-world reference data
(13F overlap, prediction-market traders) anchors the comparison externally.

## Repo map

| Path | What |
|---|---|
| `src/flock/agents/` | Agent protocol, LLM harness, provider adapters, baseline strategies |
| `src/flock/markets/` | Replay engine (Phase 1), shared exchange / matching engine (Phase 2) |
| `src/flock/data/` | Dataset builders, schemas, versioned registry |
| `src/flock/experiments/` | Run orchestration, sweeps, portfolio ledger |
| `src/flock/analysis/` | Convergence/coordination metrics, statistics, reports |
| `src/flock/interpretability/` | API input interventions and local activation-patching contracts |
| `configs/research-program.yaml` | All hypotheses, experiments, dependencies, outputs, verification |
| `configs/designs/`, `prompts/`, `personas/` | MPHIQ, pressure, wording, and profile treatments |
| `configs/budgets/` | Dated official prices and staged call/credit assumptions |
| `docs/research/` | Research question, design, metrics, pre-registration |
| `paper/` | LaTeX skeleton; figures regenerated via `flock analyze <run> --paper` |

## Reproducibility

Every run writes a manifest (resolved config/persona/model hash, git SHA, dataset hash, seeds)
under
`results/<run-id>/`. LLM responses are cached content-addressed in `.flock-cache/` so published
results can be re-derived offline. Decision logs include full observation, prompt and raw-response
hashes, evidence references, grounding verdicts, token usage, and cost. Study inference aggregates
independent blocks with `flock analyze-study`; it does not treat calls or agent pairs as replicates.

## Development

```bash
uv run pytest
uv run ruff check .
```

**If this repo lives in an iCloud-synced folder** (e.g. `~/Documents`), export
`UV_NO_EDITABLE=1` in your shell before running uv: iCloud re-hides `.venv` `.pth` files and
modern CPython skips hidden `.pth` files, which intermittently breaks editable installs with
`ModuleNotFoundError: flock`. Non-editable installs are immune. (Claude Code sessions get this
automatically via `.claude/settings.json`.)
