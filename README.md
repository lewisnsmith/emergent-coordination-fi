# flock

**Do LLM-powered trading agents converge on similar trading strategies to a greater extent than
current market infrastructure?**

flock is an experiment zone for measuring *strategy convergence* and *emergent coordination* in
LLM trading agents, compared against classical algorithmic baselines and empirical dispersion of
real-world traders. It sweeps across markets (equities, prediction markets), model providers,
harness parameters, personas/demographic instructions, and information sets — and produces
publishable decision-log datasets for agents in finance.

See [`docs/research/`](docs/research/) for the full research design:

- [01 – Research question](docs/research/01-research-question.md)
- [02 – Experimental design](docs/research/02-experimental-design.md)
- [03 – Metrics](docs/research/03-metrics.md)
- [04 – Datasets](docs/research/04-datasets.md)
- [05 – Follow-up questions](docs/research/05-follow-up-questions.md)
- [06 – Pre-registration](docs/research/06-preregistration.md)
- [07 – Related work](docs/research/07-related-work.md)

## Quickstart (no API keys required)

The whole pipeline runs offline with deterministic mock models:

```bash
uv sync
uv run flock data build synthetic          # build a seeded synthetic equities dataset
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
| `configs/` | Experiment, persona, and model registry YAML |
| `docs/research/` | Research question, design, metrics, pre-registration |
| `paper/` | LaTeX skeleton; figures regenerated via `flock analyze <run> --paper` |

## Reproducibility

Every run writes a manifest (config hash, git SHA, dataset hashes, model params, seeds) under
`results/<run-id>/`. LLM responses are cached content-addressed in `.flock-cache/` so published
results can be re-derived offline. Decision logs are JSONL with full rationales, token usage,
and cost.

## Development

```bash
uv run pytest
uv run ruff check .
```
