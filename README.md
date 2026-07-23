# flock

**Do LLM-powered trading agents converge on similar trading strategies to a greater extent than
current market infrastructure?**

flock measures *strategy convergence* and *emergent coordination* in LLM trading agents against
classical algorithmic baselines and real-world trader dispersion. It varies markets, models,
harness parameters, personas, and information sets, producing publishable decision logs.

See [`docs/research/`](docs/research/) for the full research design:

- [01 – Research question](docs/research/01-research-question.md)
- [02 – Experimental design](docs/research/02-experimental-design.md)
- [03 – Metrics](docs/research/03-metrics.md)
- [04 – Datasets](docs/research/04-datasets.md)
- [05 – Follow-up questions](docs/research/05-follow-up-questions.md)
- [06 – Pre-registration](docs/research/06-preregistration.md)
- [07 – Related work](docs/research/07-related-work.md)

## Quickstart (no API keys required)

The pipeline runs offline with deterministic mock models:

```bash
uv sync
uv run flock data build synthetic          # seeded synthetic equities
uv run flock run configs/experiments/exp-000-smoke.yaml
uv run flock analyze latest                # convergence report with bootstrap CIs
```

Real-model runs need provider keys (`cp .env.example .env`) and the extras:

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

Each run compares an **LLM cohort** with a matched **baseline cohort** (momentum,
mean-reversion, market-making, buy-and-hold, random), measuring within-cohort dispersion in
decisions, positions, and strategy fingerprints. 13F overlap and prediction-market trader data
provide external anchors.

## Repo map

| Path | What |
|---|---|
| `src/flock/agents/` | Agent protocol, LLM harness, provider adapters, baseline strategies |
| `src/flock/markets/` | Replay engine (Phase 1), shared exchange / matching engine (Phase 2) |
| `src/flock/data/` | Dataset builders, schemas, versioned registry |
| `src/flock/experiments/` | Run orchestration, sweeps, portfolio ledger |
| `src/flock/analysis/` | Convergence/coordination metrics, statistics, reports |
| `configs/` | Experiment, persona, and model registry YAML |
| `docs/research/` | Research question, design, metrics, pre-registration |
| `paper/` | LaTeX skeleton; figures regenerated via `flock analyze <run> --paper` |

## Reproducibility

Each run writes a local manifest (config hash, git SHA, dataset hashes, model params, seeds) to
`results/<run-id>/`; `datasets/manifests.json` is the checked-in input registry. Content-addressed
LLM responses in `.flock-cache/` make analyses reproducible offline. JSONL decision logs retain
rationales, token usage, and cost.

## Development

```bash
uv run pytest && uv run ruff check .
```

In iCloud-synced folders (for example, `~/Documents`), export `UV_NO_EDITABLE=1` before running
uv. iCloud can hide editable-install `.pth` files, causing intermittent `ModuleNotFoundError`
failures; `.claude/settings.json` sets this automatically for Claude Code sessions.
