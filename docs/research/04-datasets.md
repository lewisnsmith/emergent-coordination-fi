# 04 — Datasets

The project uses **inputs** (market data and reference panels) to produce **outputs** (the
publishable agent-decision datasets). Input payloads are local and gitignored;
`datasets/manifests.json` versions each dataset and hashes its primary file. Builders live in
`src/flock/data/builders/` and run through `flock data build <builder>`.

## Input datasets

| Builder | Contents | Purpose |
|---|---|---|
| `synthetic` | Seeded Markov transitions among trending, mean-reverting, and crisis regimes; common and per-symbol idiosyncratic factors; known-sentiment templated news at regime shifts. Schema: `bars` (`ts`, `symbol`, OHLCV) + `events` (`ts`, `symbol`, `headline`, `sentiment`). | Free, offline pipeline validation, known-convergence metric calibration, and contamination-free robustness. |
| `equities` | yfinance daily OHLCV for configurable symbols across multiple windows, including the 2020 crash, 2021 melt-up, 2022 drawdown, and post-cutoff periods. | Historical equity replay and contamination robustness. |
| `polymarket`, `kalshi` | Historical resolved binary contracts: metadata, price history, and outcome, rendered at prices in `(0,1)`. | Prediction-market replay. |
| `refs13f` | SEC EDGAR quarterly holdings for institutional-manager panels (with a descriptive User-Agent), plus prediction-market positioning where obtainable. | H2 external anchors for portfolio overlap and LSV herding. These feed analysis directly, not replay. |

## Output datasets (deliverables)

| Artifact | Unit and contents |
|---|---|
| `results/<run-id>/decisions.jsonl` | One record per agent-step: agent metadata, observation digest, requested and clipped orders, rationale, parse status, usage, and latency. |
| `results/<run-id>/fills.parquet` | Executed fills with prices and fees. |
| `results/<run-id>/portfolio.parquet` | Per-step, per-agent cash, positions, and equity. |
| `results/<run-id>/manifest.json` | Inline config and hash, code git SHA, dataset name/version/hash, agent model parameters and seeds, run seed, timing, and cost. |

Representative LLM decision record:

```json
{
  "run_id": "...", "step": 42, "ts": "2024-03-01",
  "agent_id": "llm-claude-x-neutral-0", "cohort": "llm",
  "kind": "llm", "model": "claude-x", "model_id": "...", "persona": "neutral",
  "temperature": 0.7, "seed": 7,
  "observation_digest": "0123456789abcdef", "action": "buy",
  "orders": [{"symbol": "AAPL", "side": "buy", "quantity": 10, "limit_price": null}],
  "orders_clipped": [{"symbol": "AAPL", "side": "buy", "quantity": 10, "limit_price": null}],
  "rationale": "...", "parse_ok": true,
  "usage": {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0},
  "latency_s": 0.0
}
```

Together, the artifacts provide publishable `(observation, agent parameterization, decision,
rationale, outcome)` tuples for studying LLM financial decision-making beyond this paper.

## Provenance & licensing notes

- Published artifacts contain derived decision logs, not redistributed raw yfinance/vendor data.
- SEC EDGAR and public Polymarket/Kalshi APIs supply reference inputs. Verify source-specific
  licensing and redistribution terms before publishing raw payloads.
