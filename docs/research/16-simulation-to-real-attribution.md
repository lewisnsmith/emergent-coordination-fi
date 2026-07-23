# 16 — Simulation-to-Real Detection and Attribution

This protocol defines the path from a causal effect inside the configurable simulation to a
carefully bounded statement about real markets. The contracts are `exp-018` through `exp-021` in
[`configs/research-program.yaml`](../../configs/research-program.yaml).

## The evidentiary ladder

| Tier | Question | Allowed label | Causal status |
|---|---|---|---|
| 1. Simulation truth | What changes when AI participation is randomized in simulation? | Simulated AI effect | Causal inside the specified simulator |
| 2. Signature discovery | Which public features distinguish simulated AI/no-AI replicas? | Simulation signature | Predictive, held-out within simulation |
| 3. Transport | Does the locked signature retain calibration out of domain? | Transported signature | Predictive in validated domains |
| 4. Real detection | Where does the signature appear in real market windows? | AI-like event | Observational, not causal |
| 5. Exposure attribution | Does verified AI exposure change the outcome versus a credible counterfactual? | AI-caused effect | Causal only under the stated design assumptions |

An AI-like pattern is not evidence that AI caused it. Common strategies, shared news, index flows,
funding shocks, execution algorithms, market structure, or chance can produce similar signatures.
Detection is a prerequisite for some attribution designs, never a substitute for exposure and a
counterfactual.

## H9: Discovering simulation signatures

### Inputs and split discipline

`exp-018` requires verified shared-market replicas with randomized AI participation, complete
order/book/tape logs, known treatment labels, market regimes, agent/capital shares, and all
simulation seeds. Candidate public features may include herding, flow persistence, synchronized
capital breadth, order timing, size discretization, cancellation behavior, price impact, spreads,
depth, volatility, and cascade structure.

Split by entire trajectory lineage before feature selection. Replicas sharing a market seed,
fundamental path, prompt cache, or derived perturbation family stay in one fold. Nested cross-
validation performs feature selection and tuning inside training folds. The locked test set is used
once. Placebo labels and classical-crowding controls measure how easily the detector mistakes
ordinary convergence for AI.

The independent unit is the held-out market replica. Orders, agents, events, and windows within a
replica are nested. Primary metrics are discrimination, precision-recall at frozen prevalence,
calibration error, Brier/log loss, false-positive rate on non-AI crowded controls, and stability
across regimes and model families.

Exact outputs are `signature_library.parquet`, `simulation_predictions.parquet`, and
`discovery_metrics.json`. `signature_library.parquet` freezes feature IDs, transformations,
lookbacks, model coefficients/parameters, training hashes, intended market domain, and thresholds.

## H9: Transport validation

`exp-019` applies the locked signature without refitting to unseen simulated regimes and then a
real-market feature panel. Temporal separation must be strict. The real panel needs instrument,
venue, timestamp, corporate-action, trade/quote, and data-cleaning provenance appropriate to each
feature. Domain-shift diagnostics compare feature support, missingness, dependence, and calibration.

The independent unit is a nonoverlapping held-out market window; overlapping windows share a
dependence cluster. Estimate external discrimination where labels exist, calibration drift,
prediction-set coverage, and change from simulation performance. If labels do not exist in real
markets, calibration cannot be claimed from score distributions alone.

Exact outputs are `transport_predictions.parquet`, `transport_metrics.json`, and
`domain_shift.json`. A failed transport gate ends population use of that signature; it may remain a
simulation-only result.

## H10: Real-market AI-like detection

`exp-020` applies only transport-approved, preregistered signatures to nonoverlapping real windows.
It estimates calibrated score and event prevalence where calibration support exists. Every detected
row must include:

- event/window ID, venue, instrument universe, and time bounds;
- locked signature/version and input-feature hashes;
- score, threshold, uncertainty, calibration domain, and domain-shift flag;
- negative-control and data-quality results; and
- `causal_status: ai_like_not_attributed`.

Outputs are `ai_like_events.parquet` and `detection_calibration.json`. The report shows timelines,
score distributions, expected false positives, negative-control periods, feature contributions, and
domain-shift warnings. It must not rank an institution or trader as AI-operated without verified
exposure evidence and an authorized disclosure basis.

## H10: Causal attribution to AI

`exp-021` is blocked until both requirements exist:

1. **Verified exposure:** independently documented model deployment/advice or AI-controlled capital,
   with institution/desk/product scope, start/end time, autonomy, affected assets, capital, model
   family/revision when available, and provenance/permission.
2. **Credible counterfactual:** randomized or staggered rollout, an externally caused natural
   experiment, a defensible discontinuity/instrument, or another preregistered design that estimates
   what would have occurred without that exposure.

The exposure definition must precede outcome inspection. Self-reported “uses AI,” generic software
procurement, or an AI-like detector score is not verified exposure. Exposure timing must precede the
outcome and cannot be backfilled from the detected event.

The independent unit and estimator follow the identification design, for example institution-
market-time rollout clusters in a randomized/staggered deployment. Mandatory falsifications include
pretrend/event-study diagnostics, placebo dates, placebo assets/outcomes, negative-control exposure,
spillover/interference checks, anticipation windows, concurrent-policy/deployment checks, and
unmeasured-confounding sensitivity. Standard errors cluster at the assignment/exposure level, not
the trade row.

Required outputs are:

- `causal_analysis_panel.parquet`: exposure, outcome, covariates, assignment, cluster, and provenance;
- `causal_effects.parquet`: frozen estimands, effects, intervals, and multiplicity;
- `falsifications.json`: every planned placebo, pretrend, spillover, and sensitivity result;
- `exposure_provenance.jsonl`: source, permission, timestamp, and verification records; and
- `causal_attribution_verification.json`: identification and claim-language verdict.

A causal claim is permitted only when exposure provenance passes, the counterfactual design is
credible, temporal order is correct, required falsifications do not invalidate the design, and the
effect survives frozen sensitivity/multiplicity rules. Otherwise publish the score as AI-like or
the analysis as inconclusive.

## Existing repository support and missing pieces

The repository currently computes herding/cascade features in
[`analysis/coordination.py`](../../src/flock/analysis/coordination.py), convergence features in
[`analysis/convergence.py`](../../src/flock/analysis/convergence.py), and strategy fingerprints in
[`analysis/strategy.py`](../../src/flock/analysis/strategy.py). The SEC 13F reference builder in
[`data/builders/real_world_refs.py`](../../src/flock/data/builders/real_world_refs.py) can create a
quarterly institutional-holdings anchor with:

```bash
export EDGAR_USER_AGENT='flock research your-email@example.com'
uv run flock data build refs13f
```

That 13F panel is an external convergence anchor; it is not an AI exposure registry and cannot
identify AI causation. There is currently no detector-training, real-market feature-panel,
exposure-registry, or causal-estimator CLI. `exp-018` is scaffolded; `exp-019`–`exp-021` are blocked
on the declared external data and runner dependencies.

## How users verify and see results

Run `uv run flock validate --output readiness.json` to see the explicit blockers rather than a
silent readiness pass. For each completed tier, users should:

1. verify input and split hashes and confirm trajectory-lineage separation;
2. reproduce nested cross-validation and the one-time locked test evaluation;
3. compare calibration and false positives against placebo/crowding controls;
4. inspect `domain_shift.json` before interpreting a real score;
5. confirm every real event says `ai_like_not_attributed` unless exposure verification passes;
6. reproduce pretrends, placebos, spillover tests, and sensitivity for any causal effect; and
7. trace each report figure/table to its exact prediction/effect row and signature/exposure version.

The final report should visibly separate simulation truth, transported performance, AI-like real
events, and causally attributed effects into different sections and colors. They must never be
merged into one “AI events” count.
