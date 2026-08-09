# Statistical Analysis Plan

This document is the operational statistical contract for the expanded research program. It
extends [Metrics](metrics.md) and must be reconciled with and frozen through
[Preregistration](preregistration.md) before confirmatory provider calls. If the documents
conflict after freeze, the tagged preregistration and its dated amendments control.

## Core principles

1. Define the scientific question, estimand, independent unit, and assignment before choosing a
   test.
2. Randomize and infer at the level where treatment is independently assigned.
3. Preserve paired structure through common market randomness.
4. Treat agents, pairs, steps, assets, paraphrases, retries, and calls as nested observations.
5. Report effect sizes and uncertainty; a p-value is not a measure of practical importance.
6. Use equivalence and noninferiority tests for sameness and safety claims.
7. Freeze confirmatory families and margins before outcomes are inspected.
8. Separate simulated causation, real-market detection, and real-market causal attribution.

## Question-to-analysis registry

Every executable experiment must have one frozen registry row with these fields:

| Field | Required content |
|---|---|
| `question_id` | H1–H13 or named secondary question |
| `population` | Exact markets, windows, models, profiles, and prompts covered |
| `treatment` / `control` | Fully rendered and hashed conditions |
| `estimand` | Mathematical contrast and aggregation weights |
| `independent_unit` | Unit independently assigned or sampled |
| `blocking` | Market, model, provider, regime, profile, and seed strata |
| `endpoint` | Primary, secondary, diagnostic, or safety role |
| `SESOI` | Smallest practically important benefit/harm |
| `equivalence_margin` | Symmetric or asymmetric negligible-effect interval |
| `noninferiority_margin` | Maximum acceptable adverse safety/suitability change |
| `missingness_rule` | Failure, retry, safeguard, and partial-block handling |
| `inference` | Randomization test/model and confidence interval |
| `multiplicity_family` | Family name and correction/gatekeeping order |
| `output` | Artifact and table/figure destination |

An analysis without this row is exploratory regardless of the language used in its report.

## Independent units

| Design | Independent unit | Nested, non-independent observations |
|---|---|---|
| Historical or synthetic replay | Nonoverlapping market-window-by-seed block | Agents, pairs, symbols, steps, calls, prompts |
| Shared exchange | Independently initialized market replica | Traders, orders, fills, book updates, calls |
| MPHIQ or pressure pairing | Block receiving all paired conditions | Scheme/cell observations and Hamming pairs |
| Real-investor panel | Independently sampled manager/trader cluster and nonoverlapping period, subject to panel dependence model | Holdings, assets, quarters, trades |
| Human trust/delegation | Consented participant | Vignettes, repeated choices, response items |
| Adoption forecast | Independent forecast origin/source series | Horizons and scenarios from that origin |
| Local mechanistic study | Held-out observation-by-checkpoint intervention block | Layers, heads/features, tokens, patches |
| H13 financial-chain study | Held-out template family, company/document cluster, or market block paired across model/precision conditions | Generated items, numerical variants, chain steps, tokens, calls, reset horizons |
| Real-market causal study | Unit assigned/exposed under the identification design | Trades and timestamps within that unit |

Nonoverlapping market windows are preferred. Overlapping windows share a dependence cluster and do
not independently increase `n`. A model sampling seed alone does not create a new market replicate.
Repeated API calls answer response-variability questions; they do not create independent evidence
that market dynamics changed.

## Prohibited pseudoreplication

The following practices are invalid:

- using agent-step rows as the sample size for a market-level treatment;
- treating every pairwise similarity as independent when pairs share agents;
- treating prompt paraphrases, retries, cache misses, or repeated calls as independent blocks;
- treating assets inside one common market shock as independent replications without clustering;
- counting overlapping historical windows as independent;
- pooling simulated agents and human participants into one inferential sample; or
- training and evaluating a detector on replicas from the same market seed or trajectory family.

Pairwise metrics must be aggregated to the independent block or modeled with a preregistered dyadic
or multi-membership structure. Cluster-robust standard errors with very few clusters are not a
substitute for adequate replication; use randomization inference and small-sample corrections.

## Primary estimands

| Program question | Primary estimand | Unit-level contrast |
|---|---|---|
| H1 frontier LLM convergence | LLM minus matched baseline kappa | Paired market block |
| H2 real-investor comparison | LLM minus matched real-panel convergence | Matched-frequency/activity panel block |
| H2b convergence breadth | AI-share effect on synchronized capital/participant/asset coverage | Market replica or matched panel period |
| H3 lineage | Within-lineage minus cross-lineage similarity | Block-aggregated dyadic contrast |
| H4 profile versus information | Information decorrelation minus profile decorrelation | MPHIQ block |
| H5 market dynamics | AI-capital-share dose response and threshold | Shared-market replica |
| H6 trust/delegation | Randomized disclosure/oversight effect on delegated share | Participant |
| H7 near-term crossing | Calibrated probability/date distribution for H5 threshold crossing | Forecast origin |
| H8 causal inputs/mechanisms | Paired output change under input or activation intervention | Intervention block |
| H9 signature transport | Locked detector discrimination/calibration on held-out domain | Held-out replica or period |
| H10 real AI causation | Assignment/exposure effect under a credible counterfactual | Design-specific exposure unit |
| H11 actionable dataset | Predefined data-quality, calibration, and utility metrics | Independently held-out dataset unit |
| H12 pressure | Factorial pressure effect on quality, safety, behavior, and convergence | Pressure block |
| H13 local fidelity | Local-versus-frontier equivalence and same-checkpoint precision-by-depth propagation | Held-out template/document/market block |

Real-market pattern resemblance estimates detection, not cause. H10 causal language requires
verified AI exposure plus randomized deployment, a defensible natural experiment, or another
specified counterfactual. Without that, results must be labeled “AI-like,” never “AI-caused.”

H13 contains two nonexchangeable analyses. The cross-model bridge estimates descriptive
equivalence or difference between deliberately sampled local and frontier endpoints; model class
is not randomized. The quantization analysis uses paired variants of one immutable checkpoint to
estimate precision effects, with a deterministic executable oracle for correctness. The primary
propagation model estimates precision×dependency-depth×family effects on conditional step-error
hazard and chain survival, then a paired endogenous-minus-shadow-state contrast for replay
amplification. Generalization beyond sampled models requires an untouched family-level test, not a
significant pooled model coefficient.

## Randomization inference

For paired market experiments, calculate one treatment contrast per independent block. Under the
sharp null, perform exact sign-flip inference when the number of blocks permits; otherwise use at
least 10,000 seeded Monte Carlo sign assignments and the finite-sample correction
`p = (extreme + 1) / (draws + 1)`. Report the randomization seed and attainable minimum p-value.

For multi-arm or dose-response experiments, permute treatment according to the actual blocked
assignment mechanism, not unrestricted row labels. For human studies, preserve participant-level
assignment and cluster repeated choices by participant. For observational panels, randomization
inference is unavailable unless justified by the design; use a prespecified panel model and report
identification assumptions and sensitivity analyses.

Confidence intervals must resample independent blocks or use a compatible hierarchical model.
Bootstrap resampling of calls, steps, or pair rows is prohibited. BCa intervals require enough
independent blocks for stable acceleration; otherwise use randomization intervals, wild-cluster
bootstrap, or a clearly labeled small-sample alternative.

## Practical thresholds

These defaults apply until replaced before preregistration freeze using synthetic calibration,
domain expertise, and power simulation:

| Endpoint | Benefit/harm SESOI | Equivalence margin | Safety noninferiority margin |
|---|---:|---:|---:|
| Cohen's kappa | 0.10 absolute | ±0.05 | — |
| Portfolio overlap | 0.05 absolute | ±0.03 | — |
| Capital-weighted synchronization/breadth | 0.05 absolute | ±0.03 | — |
| Normalized regret, 0–1 | 0.05 | ±0.025 | +0.025 adverse |
| Goal-attainment or shortfall probability | 0.05 absolute | ±0.025 | 0.025 adverse |
| Trade/abstention probability | 0.05 absolute | ±0.03 | — |
| Hard-constraint/fabrication/unsupported-claim rate | — | ±0.005 | +0.01 adverse |
| Executable program or terminal-answer accuracy | 0.05 absolute | ±0.03 | +0.03 adverse |
| First-step error hazard or chain survival | 0.05 absolute | ±0.03 | +0.03 adverse |
| Spread, depth, volatility, or price impact | 0.20 baseline SD | ±0.10 SD | 0.10 SD adverse when a safety endpoint |
| Human delegated-capital share | 0.10 absolute | ±0.05 | — |

Raw-unit thresholds take precedence over standardized thresholds when interpretation is clearer.
Margins must not be chosen from observed confirmatory effects. Report estimates against zero, the
SESOI, and all equivalence/noninferiority boundaries.

## Significance, equivalence, and noninferiority

- **Difference/superiority:** reject the null and show the confidence interval exceeds the SESOI in
  the prespecified direction for a practically important claim.
- **Equivalence:** perform TOST at the family-adjusted alpha and require the entire compatible
  interval to fall inside the frozen lower and upper equivalence bounds.
- **Noninferiority:** test the one-sided adverse bound; all mandatory safety/suitability endpoints
  must pass.
- **Inconclusive:** use when intervals include meaningful benefit and harm, or when a difference is
  nonsignificant but equivalence was not established.

“No significant difference,” `p > 0.05`, overlapping confidence intervals, or low power never prove
sameness. A quality benefit with failed safety noninferiority is not a successful treatment.

## Multiple testing

Before unblinding, create named families with one row per planned contrast:

- H1–H5 core confirmatory family: Holm control unless the frozen preregistration uses a stricter
  hierarchical gate.
- MPHIQ main effects: one five-contrast Holm family.
- MPHIQ interactions: separate preregistered Holm family; higher-order discovery uses BH-FDR.
- H12 pressure: six-contrast Holm family defined in
  [Prompt and Pressure Protocol](prompt-pressure-protocol.md).
- Profile matched sets: one nine-contrast Holm family per endpoint tier.
- Safety: conjunctive noninferiority; every required endpoint must pass.
- Mechanistic features: discovery and confirmation must use separate data; discovery uses FDR and
  held-out confirmation uses Holm over the frozen feature set.
- H13 behavioral fidelity, chain propagation, customization, and mechanistic transfer are four
  separate frozen families. Model sizes, precisions, depths, contexts, error positions, replay
  reset horizons, outcomes, and feature sites all count toward their declared family.
- Detector feature selection: nested inside training folds; the locked test set is evaluated once.

Always report the family name, number of hypotheses, raw p-value, adjusted p-value, adjusted alpha
or interval, effect, and margin. Creating narrower post-hoc families is prohibited. Exploratory
results must remain labeled exploratory even if small p-values survive FDR control.

## Power and replication

Determine independent-block counts by simulation using the full assignment, within-block
correlation, model/provider heterogeneity, dyadic aggregation, missingness, and intended correction.
Do not infer power from agent or call count. The pilot may estimate nuisance variance but must not
select confirmatory endpoints or favorable models based on outcomes.

Use a blinded stop/go rule based on data completeness, variance, cost, and safety failure rates.
Re-estimation of sample size may use blinded pooled variance. If effect estimates are examined,
adaptation requires a preregistered group-sequential rule and alpha accounting. Confirmatory data
must use windows, seeds, and model revisions held out from design development where feasible.

For H13, use 8–12 discovery clusters only for engineering and nuisance estimates, simulate power
for roughly 24–32 paired confirmatory clusters, and allow a blinded interval-width re-estimation to
a hard cap near 48 only if frozen in advance. A 25–50-item-per-depth local screen is a nested
precision diagnostic, not 25–50 independent replications. Stop a cell for futility only when the
attainable interval cannot resolve its frozen difference/equivalence claim; failure to establish
equivalence remains inconclusive.

## Missingness and failures

Every planned unit receives one terminal status: complete, provider failure, parse failure,
safeguard rejection, infeasible order, or missing. Retries remain linked to the original call.
Voluntary hold, parse-failure hold, safeguard hold, and constraint-forced hold are distinct outcomes.

Partial independent blocks are not silently analyzed. The default is to rerun the missing cell under
the frozen retry policy or mark the block incomplete. Any complete-case analysis and inverse-
probability sensitivity must be prespecified. Report failure rates by treatment, model, provider,
and block because treatment-dependent failure is itself an outcome.

## Model and population scope

Provider/model effects are fixed effects when the tested releases were deliberately selected. A
claim about the broader frontier-model population requires an explicit sampling frame, multiple
independent model families, random or defensible selection, and provider-family sensitivity.
Changing API revisions during a study creates a new model level. Cached responses preserve
reproducibility but do not remove model-release scope limitations.

Real-investor comparisons must match time aggregation, eligible assets, activity thresholds, long
versus short treatment, and capital weighting. If direct matching is impossible, report separate
estimands and avoid ranking them as though identical.

## Required statistical outputs

Every confirmatory study writes:

- `estimand_registry.json`: frozen question and analysis rows.
- `randomization_plan.json` and `realized_assignments.parquet`.
- `independent_units.parquet`: one row per actual replication unit and terminal status.
- `block_effects.parquet`: unit-level contrasts used for inference.
- `effects.parquet`: estimates, intervals, SESOIs, and equivalence/noninferiority margins.
- `multiplicity.json`: family membership, raw and adjusted results.
- `equivalence_noninferiority.json`: TOST and one-sided safety decisions.
- `missingness_failures.parquet` and `sensitivity_results.parquet`.
- `statistical_verification.json`: automated audit verdicts.
- `claims.json`: each claim linked to its estimand, data hashes, table, and figure.

Reports must show independent `n`, nested observation counts separately, unit-level effect plots,
raw action/failure distributions, adjusted and unadjusted results, and robustness across model,
provider, market, regime, and profile blocks.

## Statistical verification checklist

Release fails closed unless an automated audit confirms:

- every confirmatory claim resolves to one frozen estimand row;
- the reported independent `n` equals the independent-unit artifact;
- block IDs are unique and overlapping windows share a dependence cluster;
- assignment and analysis permutations reproduce the actual randomization;
- paired cells share required market paths and non-treatment hashes;
- no agent, pair, call, step, paraphrase, or retry is counted as independent evidence;
- all planned cells and failures reconcile;
- margins were frozen before outcome access;
- equivalence uses TOST and safety uses the declared noninferiority direction;
- multiplicity families include every planned contrast;
- held-out, discovery, and confirmatory datasets are disjoint by trajectory lineage;
- causal language matches the identification design; and
- all tables and figures regenerate from hashed analysis inputs.

The audit output must include executable reproduction commands, package/code versions, random
seeds, data/config hashes, and an explicit pass/fail status. A failed gate blocks confirmatory
release; it may be reported only as a labeled diagnostic or failed-run artifact.
