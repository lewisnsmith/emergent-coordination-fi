# 04 — Datasets

Two kinds of datasets: **inputs** (market data agents trade on; reference panels) and
**outputs** (decision logs — the publishable "agents in finance" datasets).

All datasets are local, versioned, and content-hashed. `datasets/manifests.json` is the
checked-in registry; payloads under `datasets/` are gitignored. Builders live in
`src/flock/data/builders/` and are invoked via `flock data build <builder>`.

## Input datasets

### `synthetic` — regime-switching synthetic market (offline, free, seeded)
- Regime-switching price process: trending / mean-reverting / crisis regimes with Markov
  transitions; per-symbol idiosyncratic + common factor components; templated news events with
  known sentiment attached to regime shifts.
- Purpose: pipeline validation, metric calibration on cohorts of *known* convergence,
  contamination-free robustness sets.
- Schema: `bars` (ts, symbol, open, high, low, close, volume) + `events` (ts, symbol, headline,
  sentiment).

### `equities` — US daily bars (yfinance)
- Daily OHLCV for a configurable symbol list and window. Multiple windows spanning distinct
  regimes (e.g., 2020 crash, 2021 melt-up, 2022 drawdown, post-cutoff periods for
  contamination robustness).

### `polymarket` / `kalshi` — binary prediction contracts
- Historical resolved markets: contract metadata, price history, resolution outcome.
- Rendered for agents as binary contracts with price ∈ (0,1).

### `refs13f` — real-world reference panels (external anchor, H2)
- 13F quarterly holdings for a panel of institutional managers (SEC EDGAR, descriptive
  User-Agent required); used to compute empirical portfolio overlap and LSV herding among real
  managers.
- Prediction-market positioning panels where obtainable.
- These are *reference* datasets: they feed the analysis layer directly, not the replay engine.

## Output datasets (deliverables)

### Decision logs — `results/<run-id>/decisions.jsonl`
One record per agent-step:

```json
{
  "run_id": "...", "step": 42, "ts": "2024-03-01",
  "agent_id": "llm-claude-x-neutral-0", "cohort": "llm",
  "kind": "llm", "model": "claude-x", "persona": "neutral",
  "temperature": 0.7, "seed": 7,
  "observation_digest": "sha256:...",
  "prompt_hash": "sha256:...",
  "orders": [{"symbol": "AAPL", "side": "buy", "quantity": 10, "limit_price": null}],
  "rationale": "...", "parse_ok": true,
  "usage": {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0},
  "latency_s": 0.0
}
```

### Trade/portfolio history — `results/<run-id>/fills.parquet`, `portfolio.parquet`
Fills with prices/fees; per-step per-agent cash, positions, equity.

### Run manifest — `results/<run-id>/manifest.json`
Config (inline + hash), code git SHA, dataset name/hash, model params, seeds, timing, cost.

Together these form the publishable dataset: (observation, agent parameterization, decision,
rationale, outcome) tuples suitable for studying LLM financial decision-making beyond this
paper's question.

## Provenance & licensing notes

- yfinance data is for research use; published artifacts include derived decision logs, not
  redistributed raw vendor data.
- EDGAR data is public domain; Polymarket/Kalshi historical data via their public APIs, cached
  with retrieval timestamps in the manifest.
