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
| Model | Six dated frontier endpoints: 2 OpenAI, 2 Anthropic, 1 Google, 1 local/open-weight |
| Harness | temperature ∈ {0, 0.7, 1.0}; reasoning effort where supported; memory on/off |
| Instructions | 24 structured profiles, 5 semantic paraphrases, realistic families, pressure factorial |
| Information set | identical observations (default) vs differentiated news subsets |
| Seed | ≥10 seeds per cell (finalized by power analysis, see 06-preregistration) |

A **run** = one (market, dataset, cohort spec, independent block, seed). A **sweep** = grid of runs. Cells are
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
news/events, its own portfolio, and cash. It must return structured JSON with orders, a concise
rationale, evidence references, calibrated confidence, and uncertainties. Strict runs reject
unsupported evidence references and record grounding failures separately from parse failures.
Malformed responses are retried once, then recorded as `hold` with a parse-failure flag
(exclusion rules in 06-preregistration).

## Complete experiment program

The authoritative catalog is [`configs/research-program.yaml`](../../configs/research-program.yaml):

- `exp-000`–`002`: calibration and confirmatory equity/prediction replay.
- `exp-003`–`009`: real-investor anchor, convergence breadth, provider/profile/information,
  all 32 MPHIQ schemes, and robustness.
- `exp-010`–`012`: exchange calibration, AI-capital-share dose response, and microstructure.
- `exp-013`–`015`: human trust, advisor execution, and conditional adoption forecasts.
- `exp-016`–`017`: API black-box attribution and local mechanistic interventions.
- `exp-018`–`020`: signature transport, real-market detection, and causal attribution.
- `exp-021`–`024`: actionable data products, complete prompt pressure, safeguards, and final
  confirmatory replication.

`executable`, `scaffolded`, and `blocked_external` are intentionally distinct. A protocol is not
called execution-ready merely because its YAML exists. `flock validate` reports both scaffold
validity and missing data/approval/exposure blockers.

## Factorial assignment

MPHIQ uses bits `M P H I Q`, where `1 = same` and `0 = balanced different`. All 32 codes are
enumerated in [`configs/designs/mphiq.yaml`](../../configs/designs/mphiq.yaml). Prompt pressure is
a 24-cell `3 stakes × 2 urgency × 2 emotion × 2 forced-action` design. Prompt paraphrases are
nested robustness repetitions, not independent market evidence. See [09](09-mphiq-factorial-design.md)
and [11](11-prompt-pressure-protocol.md).

## Threats to validity (and responses)

- *Data contamination:* models may "remember" historical prices. Response: synthetic regimes and
  post-cutoff windows as robustness sets; report both.
- *Prompt-induced convergence:* a shared prompt template could itself cause agreement. Response:
  paraphrase battery; persona axis; report template sensitivity.
- *Baseline strawman:* a too-narrow algo cohort inflates H1. Response: hyperparameter-randomized
  baseline families and the external real-world anchor (H2).
- *Metric gaming:* single metrics can mislead. Response: pre-registered metric hierarchy with
  Holm–Bonferroni across the family.
- *Pseudoreplication:* model calls, steps, agent pairs, and prompt paraphrases are dependent.
  Response: paired inference over independent market-window/seed blocks; whole-market units in
  Phase 2; participant-clustered inference for H6.
- *Fabrication:* free-text claims can invent evidence. Response: immutable evidence IDs, strict
  grounding, injection sentinels, fail-closed quality gates, and no rationale-as-mechanism claim.
