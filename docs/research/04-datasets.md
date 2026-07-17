# 04 — Datasets

Two kinds of datasets: **inputs** (market data agents trade on; reference panels) and
**outputs** (decision logs — the publishable "agents in finance" datasets).

All datasets are local, versioned, and content-hashed. `datasets/manifests.json` is the
checked-in registry; payloads under `datasets/` are gitignored. Builders live in
`src/flock/data/builders/` and are invoked via `flock data build <builder>`.

## Acquisition status (2026-07-13)

Only `synthetic-equities-v1` is currently registered and acquired. Equity, prediction-market,
13F, participant trust/delegation, AI-exposure/adoption, and causal-event datasets are required
but not acquired. `flock validate` reports these as execution blockers; documentation or a
builder does not count as acquired data.

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

### Human trust/delegation panel — H6

- Requires ethics/IRB review as applicable, consent, deidentification, recruitment, randomized
  disclosure/oversight/performance treatments, and incentive-compatible delegation outcomes.
- Synthetic personas or model answers cannot substitute for human trust data.

### AI exposure and adoption registry — H7/H10

- Time-stamped, source-verifiable records of AI advice/autonomy, assets or order flow exposed,
  deployment date, model/vendor, oversight, and confidence in attribution.
- H10 additionally needs assignment timing or a credible natural-experiment counterfactual.
  Market-pattern resemblance is never stored as verified exposure.

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
  "raw_response_hash": "sha256:...",
  "evidence_refs": ["price:AAPL"],
  "grounding_ok": true,
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

Study outputs add `assignments.parquet`, `contrasts.parquet`, `verification.json`,
`safety_failures.parquet`, and `claims.json`. Real-market data products keep four labels
separate: simulation truth, AI-like signature, verified AI exposure, and causally verified AI
event. See [17 — Data products](17-data-products-and-verification.md).

## Provenance & licensing notes

- yfinance data is for research use; published artifacts include derived decision logs, not
  redistributed raw vendor data.
- EDGAR data is public domain; Polymarket/Kalshi historical data via their public APIs, cached
  with retrieval timestamps in the manifest.
