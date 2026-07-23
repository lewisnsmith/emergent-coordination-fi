# 04 — Datasets

The project uses **inputs** (market data and reference panels) to produce **outputs** (the
candidate agent-decision research artifacts). Input payloads are local and gitignored;
`datasets/manifests.json` versions each dataset and hashes its complete file bundle. Builders live in
`src/flock/data/builders/` and run through `flock data build <builder>`.

## Acquisition status (2026-07-23)

Only the seeded `synthetic-equities-v1` dataset is acquired; its latest registry entry is bundle-
hashed version 2. Equity, prediction-market, 13F, participant trust/delegation,
AI-exposure/adoption, and causal-event datasets are not acquired. `flock validate` reports required
missing inputs as execution blockers; documentation or a builder does not count as acquired data.

## Input datasets

| Source/builder | Contents | Purpose |
|---|---|---|
| `synthetic` | Seeded Markov transitions among trending, mean-reverting, and crisis regimes; common and per-symbol idiosyncratic factors; known-sentiment templated news at regime shifts. Schema: `bars` (`ts`, `symbol`, OHLCV) + `events` (`ts`, `symbol`, `headline`, `sentiment`). | Free, offline pipeline validation, known-convergence metric calibration, and contamination-free robustness. |
| `equities` | yfinance daily OHLCV for configurable symbols across multiple windows, including the 2020 crash, 2021 melt-up, 2022 drawdown, and post-cutoff periods. | Historical equity replay and contamination robustness. |
| `polymarket`, `kalshi` | Historical resolved binary contracts: metadata, price history, and outcome, rendered at prices in `(0,1)`. | Prediction-market replay. |
| `refs13f` | SEC EDGAR quarterly holdings for institutional-manager panels (with a descriptive User-Agent). | H2 external anchors for portfolio overlap and LSV herding. These feed analysis directly, not replay. |
| Planned trader panels | Prediction-market positioning where lawfully obtainable and reproducibly sampled. | Optional descriptive H2 context; no builder or acquired dataset exists yet. |

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

| Artifact | Unit and contents |
|---|---|
| `results/<run-id>/decisions.jsonl` | One record per agent-step: agent metadata, observation digest, requested and clipped orders, rationale, parse status, usage, and latency. |
| `results/<run-id>/fills.parquet` | Executed fills with prices and fees. |
| `results/<run-id>/portfolio.parquet` | Per-step, per-agent cash, equity, and JSON-encoded portfolio weights. |
| `results/<run-id>/manifest.json` | Inline config and hash, code git SHA, dataset name/version/hash, agent model parameters and seeds, run seed, timing, and cost. |

Representative LLM decision record:

```json
{
  "run_id": "...", "step": 42, "ts": "2024-03-01",
  "agent_id": "llm-claude-x-neutral-0", "cohort": "llm",
  "kind": "llm", "model": "claude-x", "model_id": "...", "persona": "neutral",
  "temperature": 0.7, "seed": 7,
  "observation_digest": "sha256:...",
  "action": "buy",
  "prompt_hash": "sha256:...",
  "raw_response_hash": "sha256:...",
  "evidence_refs": ["price:AAPL"],
  "grounding_ok": true,
  "orders": [{"symbol": "AAPL", "side": "buy", "quantity": 10, "limit_price": null}],
  "orders_clipped": [{"symbol": "AAPL", "side": "buy", "quantity": 10, "limit_price": null}],
  "rationale": "...", "parse_ok": true,
  "usage": {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0},
  "latency_s": 0.0
}
```

After licensing and release verification, the artifacts can provide `(observation, agent
parameterization, decision, rationale, outcome)` tuples for research beyond the proposed study.

Study outputs add `assignments.parquet`, `contrasts.parquet`, `verification.json`,
`safety_failures.parquet`, and `claims.json`. Real-market data products keep four labels
separate: simulation truth, AI-like signature, verified AI exposure, and causally verified AI
event. See [17 — Data products](17-data-products-and-verification.md).

## Provenance & licensing notes

- Published artifacts contain derived decision logs, not redistributed raw yfinance/vendor data.
- SEC EDGAR and public Polymarket/Kalshi APIs supply reference inputs. Verify source-specific
  licensing and redistribution terms before publishing raw payloads.
