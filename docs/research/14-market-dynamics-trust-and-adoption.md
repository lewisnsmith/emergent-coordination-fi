# 14 — Market Dynamics, Trust, and Adoption

This protocol separates three related but different questions:

- H5: does AI-controlled capital causally change simulated market dynamics?
- H6: do people trust AI to advise or autonomously manage their investments?
- H7: under explicit adoption scenarios, when might AI-controlled capital cross an H5 threshold?

Their experiment contracts are `exp-010` through `exp-015` in
[`configs/research-program.yaml`](../../configs/research-program.yaml). Only the mock exchange
calibration currently has an executable config:
[`exp-010-shared-exchange.yaml`](../../configs/experiments/exp-010-shared-exchange.yaml).

## Claim boundaries

| Evidence | Allowed claim | Prohibited claim |
|---|---|---|
| Mock shared exchange | Exchange and metrics respond to known synthetic behavior | Frontier AI changes real markets |
| Randomized frontier-agent market replicas | AI share changes this simulated environment | The same threshold holds in real markets |
| Simulated human-execution layer | Effects survive specified compliance/noise assumptions | Real people will follow AI at that rate |
| Consented randomized human study | Treatment changes measured trust/delegation in sampled people | Simulated personas demonstrate human trust |
| Adoption forecast plus H5 threshold | Conditional threshold-crossing distribution | AI will change markets by a definite date |

H6 cannot be answered by asking models to imitate investors. It requires actual human participants,
ethics/IRB or equivalent review, informed consent, recruitment, deidentification, and an approved
human-study runner. H7 is a conditional forecast joining uncertain adoption data to an uncertain
simulation threshold; it is not a fact about the future.

## H5: Does AI share change market dynamics?

### Inputs and design

`exp-010` calibrates the continuous double auction using synthetic data and known mock cohorts. It
tests book mechanics, fills, cascades, and deterministic replay, not the frontier-model hypothesis.

`exp-011` must create independently initialized market replicas at a frozen AI-capital-share grid,
recommended as `0%, 5%, 10%, 20%, 40%, 60%, 80%, 100%` for threshold resolution. Each share receives
the same total capital, endowments, exogenous news, fundamental path, fee/tick rules, background
liquidity ecology, and common random numbers. AI share changes through a capital allocator, not by
adding total wealth. Frontier agents are balanced across eligible API and local model families.

`exp-012` holds total flow or submitted volume fixed where possible and varies AI participation or
AI market-making. Placebo cohorts, exogenous market makers, and matched no-AI replicas distinguish
model behavior from mechanical volume effects. Order-book state must be logged deeply enough to
reconstruct best bid/ask, spread, depth, cancellations, fills, and price-time priority.

The independent unit is an independently randomized shared-market replica. Traders, orders, book
updates, calls, and timestamps are nested—not independent replications.

### Estimands and thresholds

For each share, estimate the paired change from the zero-AI replica in:

- implementation shortfall and permanent/transient price impact;
- realized and downside volatility;
- bid-ask spread and depth around the mid;
- volume, turnover, price efficiency, and deviation from the simulated fundamental;
- LSV/Sias herding, cascade frequency/length/depth, and liquidity withdrawal; and
- H2b capital-, participant-, symbol-, and time-coverage of synchronized behavior.

Fit a preregistered monotone or flexible dose-response model with simultaneous confidence bands.
The H5 threshold is the smallest AI share whose simultaneous interval crosses a frozen practical
effect boundary, not the first noisy point with `p < 0.05`. Default boundaries are 0.20 control-SD
for a market-dynamics endpoint and 0.05 absolute for synchronized-capital breadth; freeze raw-unit
alternatives where economically interpretable. Report uncertainty in both threshold share and
effect size. Holm-correct the H5 endpoint family and show all shares even if no threshold is found.

### Outputs and viewing

Exact research outputs are:

- `h5_share_outcomes.parquet`: one replica-share outcome row;
- `h5_share_curve.parquet`: fitted effects and simultaneous bands by share;
- `h5_thresholds.json`: SESOI crossings, uncertainty, and no-crossing cases;
- `h5_microstructure.parquet`: spread/depth/impact/efficiency outcomes;
- `h5_cascades.parquet`: event definitions and cascade records; and
- `h5_inference.json`: estimates, multiplicity, sensitivity, and independent `n`.

Users should see dose-response plots with confidence bands, spread/depth panels, cascade timelines,
capital-weighted synchronization curves, and replica-level effect plots in the study report. They
verify results by reconstructing the book and trades, checking total-capital equality, rerunning
placebo labels, and matching every plotted point to `h5_share_outcomes.parquet`.

The currently executable calibration can be inspected with:

```bash
uv run flock run configs/experiments/exp-010-shared-exchange.yaml
uv run flock verify-run results/<run-id> > results/<run-id>/run-verification.json
uv run flock analyze <run-id>
```

No `exp-011` or `exp-012` experiment YAML exists yet, so those studies remain scaffolded rather
than runnable.

## H6: Will people trust AI with investments?

### Human-subject requirement

`exp-013` is correctly marked `blocked_external`. Before data collection it requires ethics/IRB or
equivalent approval, consent language, eligibility criteria, recruitment and compensation plan,
power analysis, privacy/deidentification plan, adverse-event/contact procedure, preregistration, and
a human-study application that cannot place real trades.

The independent unit is the consented participant. Repeated vignettes and choices are clustered
within participant. The primary outcome should be incentive-compatible delegated capital share,
supplemented by advice acceptance, autonomous-management choice, confidence, comprehension, and
revocation behavior. Pure attitude ratings are secondary.

Randomize, in balanced order:

- AI identity disclosure versus human-adviser control;
- advice-only, human-review, and autonomous execution;
- independently audited versus asserted performance evidence;
- explanation availability and uncertainty disclosure;
- ordinary versus stressed market conditions; and
- reversible versus locked delegation.

Use identical fees, historical evidence, risk, and outcome distributions across labels. Include
attention/comprehension checks without conditioning the primary effect on post-treatment variables.
Analyze at participant assignment level with participant-clustered intervals and nonresponse/
attrition sensitivity. Test heterogeneous effects only in frozen families.

Required outputs are `h6_deidentified_choices.parquet`, `h6_effects.parquet`, and
`h6_inference.json`, plus `human_study_verification.json` containing approval identifier, consent
version, randomization audit, exclusions, deidentification checks, and sample reconciliation. Raw
identifiers and free text must never enter the public repository.

`exp-014` is a simulation of recommendation compliance, latency, and sizing noise. Its outputs,
`advisor_transmission.parquet` and `advisor_thresholds.json`, answer how convergence survives stated
executor assumptions. They do not answer whether humans trust AI.

## H7: Will adoption cross a market-impact threshold soon?

`exp-015` joins a verified adoption time series to the full distribution of H5 thresholds. Inputs
must identify what is measured—AI advice exposure, assets with AI recommendations, or autonomous
AI-controlled capital. These quantities are not interchangeable. Sources need retrieval dates,
definitions, coverage, revisions, and uncertainty; vendor marketing estimates are sensitivity
inputs, not ground truth.

Use multiple diffusion/forecast models, rolling forecast origins, and backtests at historical
origins. Combine adoption and H5 threshold uncertainty by simulation without replacing either with
a point estimate. Publish named scenarios rather than a single deterministic curve. “Soon” must be
fixed before analysis, for example within 1, 3, or 5 years.

The estimand is the conditional probability and date distribution for crossing the simulated H5
threshold under each adoption definition and scenario. Report calibration, interval coverage,
model weights, threshold-not-reached probability, and sensitivity to structural breaks. The claim
must read:

> Under scenario S, adoption measure A, and simulated threshold definition T, the estimated
> crossing probability within horizon H is P with interval I.

It must not read “AI will change markets by date D.”

Exact outputs are `adoption_scenarios.parquet`, `threshold_forecasts.parquet`, and
`forecast_calibration.json`. Users see scenario fans, rolling-origin errors, calibration plots, and
threshold-crossing probability curves. They verify source hashes, reproduce each forecast origin,
and confirm that scenario labels are never presented as observed facts.

## Readiness and verification

Run `uv run flock validate --output readiness.json` and inspect both `scaffold_ok` and
`execution_ready`. The verifier exposes human-study and adoption-data dependencies as blockers.
H5–H7 claims are releasable only when their exact research-program outputs exist, independent units
reconcile, practical thresholds were frozen, and the study-specific verification file passes.
