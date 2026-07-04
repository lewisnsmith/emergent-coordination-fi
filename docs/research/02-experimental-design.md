# 02 — Experimental Design

## Topology (two phases)

```
Phase 1 (Replay):                      Phase 2 (Shared exchange):
  data ──▶ Agent A ──▶ trades_A          Agent A ─┐
  data ──▶ Agent B ──▶ trades_B          Agent B ─┼─▶ [order book] ─▶ price impact
  data ──▶ Agent C ──▶ trades_C          Agent C ─┘        ▲              │
                                                           └── feedback ──┘
```

- **Phase 1 — historical replay.** N agents independently trade the *same* replayed market data
  with no interaction and no price impact. Fills at next-bar prices with fees/slippage. This
  isolates *strategy convergence*: any decision correlation comes from the agents themselves,
  not from market feedback.
- **Phase 2 — shared exchange.** The same cohorts trade in one continuous double auction; their
  orders set prices. This tests *emergent coordination*: herding with impact, cascades,
  liquidity withdrawal, tacit coordination.

Phase 1 results are the paper's primary evidence (clean identification); Phase 2 results are the
mechanism/consequence evidence.

## Experimental axes

| Axis | Levels (initial) |
|---|---|
| Market type | equities (daily bars), binary prediction contracts |
| Data regime | trending, mean-reverting, crisis (synthetic); multiple historical windows (real) |
| Model | Claude (≥2 tiers), GPT (≥2 tiers), Gemini, ≥1 open-weights via OpenAI-compatible endpoint |
| Harness | temperature ∈ {0, 0.7, 1.0}; reasoning effort where supported; memory on/off |
| Instructions | neutral mandate + persona set (retail/institutional/demographic variants) + risk mandates |
| Information set | identical observations (default) vs differentiated news subsets |
| Seed | ≥10 seeds per cell (finalized by power analysis, see 06-preregistration) |

A **run** = one (market, dataset, cohort spec, seed). A **sweep** = grid of runs. Cells are
addressed by config hash so sweeps are resumable and exactly reproducible.

## Cohorts

Every experiment includes at least:

1. **LLM cohort** — n agents drawn from the model/persona grid for that experiment.
2. **Baseline algo cohort** — equal-size cohort spanning momentum, mean-reversion,
   market-making, buy-and-hold, and random agents with randomized hyperparameters (so the
   baseline has *within-family* heterogeneity comparable to real algo populations).
3. **Null cohort** — random agents only; calibrates chance-level agreement for every metric.

External anchor (not a run cohort): real-world dispersion panels — 13F institutional holdings
overlap, prediction-market trader positioning — computed with the same overlap/herding
statistics (see 03 and 04).

## Controls and identification

- **Identical information sets** within a run (unless the axis under study is information).
  Observations are byte-identical rendered prompts modulo persona blocks.
- **Chance calibration.** All agreement metrics are reported relative to the null cohort and to
  an analytic chance floor (marginal-preserving permutation).
- **Capital & constraints equalized.** Same initial cash, position limits, fee schedule.
- **Order of presentation fixed.** No cross-agent leakage: agents never see each other's trades
  in Phase 1; in Phase 2 they see only the anonymous public book/tape.
- **Prompt paraphrase robustness.** Each headline result is replicated under k paraphrases of
  the task prompt; paraphrase sensitivity is itself reported.
- **Determinism.** Every stochastic component is seeded; LLM calls are cached content-addressed
  (model, params, prompt) so analyses re-run bit-identically offline.

## Decision protocol (what agents actually do)

Each step an agent receives an observation: recent OHLCV window (or contract prices), optional
news/events, its own portfolio, and cash. It must return structured JSON:
`{"orders": [{"symbol", "side", "quantity", "limit_price"?}], "rationale": "..."}`.
Malformed responses are retried once, then recorded as `hold` with a parse-failure flag
(exclusion rules in 06-preregistration).

## Phasing of evidence

1. **exp-000 (smoke).** Mock models + baselines on synthetic data; validates the pipeline and
   calibrates metric behavior on cohorts with *known* convergence (mock momentum cohort ≈ fully
   convergent; random cohort ≈ chance).
2. **exp-001/002 (replay, real data).** Equities and prediction markets; H1–H4.
3. **exp-010 (shared exchange).** H5 — coordination with price impact.

## Threats to validity (and responses)

- *Data contamination:* models may "remember" historical prices. Response: synthetic regimes and
  post-cutoff windows as robustness sets; report both.
- *Prompt-induced convergence:* a shared prompt template could itself cause agreement. Response:
  paraphrase battery; persona axis; report template sensitivity.
- *Baseline strawman:* a too-narrow algo cohort inflates H1. Response: hyperparameter-randomized
  baseline families and the external real-world anchor (H2).
- *Metric gaming:* single metrics can mislead. Response: pre-registered metric hierarchy with
  Holm–Bonferroni across the family.
