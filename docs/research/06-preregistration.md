# 06 — Pre-registration

**Status: DRAFT; not frozen, not registered, and not eligible to freeze yet.** The offline smoke
run validates plumbing only. Real inputs, top-level units, the matched technology-by-ecology
benchmark, exact model lineage, and simulation-based power must pass the gates below before the
first confirmatory frontier-model call. After freeze, changes require a dated amendment and an
untouched confirmatory split.

## Confirmatory structure

The first paper contains one confirmatory family: **H1/H3/H4**. Its exact ordered contrasts and
Holm correction are frozen before confirmatory outcomes are generated. H1 is the primary
technology-by-ecology comparison; H3 is the provider/model-lineage contrast; H4 is the balanced
MPHIQ component contrast. Unlisted interactions and high-dimensional MPHIQ screening are
exploratory and require untouched confirmation.

- **H2** is a conditional descriptive anchor with intervals, not a causal comparison and not part
  of the first-paper confirmatory p-value family. It is omitted if harmonization fails.
- **H5** is a separate confirmatory family randomized at the independent shared-market-replica
  level. Causal language is limited to the validated simulator.
- **H2b and H6–H12** are future-program protocols. They cannot be promoted into the first-paper
  family by an amendment after first-paper outcomes are inspected.

## Primary H1 outcome

The primary benchmark is a matched
`technology (LLM, classical) × ecology (homogeneous, heterogeneous)` design. For top-level unit
`u`, convergence is first aggregated within provider or strategy family and then combined using
frozen family weights to form `κ[t,e,u]`. The H1 family includes:

- the ecology-averaged technology contrast
  `Δtech = ½[(κ[LLM,hom] − κ[classical,hom]) + (κ[LLM,het] − κ[classical,het])]`; and
- the technology-by-ecology interaction
  `Δint = (κ[LLM,hom] − κ[LLM,het]) − (κ[classical,hom] − κ[classical,het])`.

The complete `(step, symbol)` grid contributes to each unit-level estimate, but does not determine
the inferential sample size. The top-level independent unit is an independently generated
synthetic trajectory or a nonoverlapping historical window. Windows that overlap or share a
material common shock use a frozen dependence-cluster identifier. Seeds, agents, pairs, calls,
steps, symbols, retries, and prompts are nested observations.

Technology labels are not randomized, so label permutation or paired sign flipping is **not
design-based randomization inference** for H1. The primary interval and test will use the frozen
top-level-unit model selected by outcome-blind simulation—for example, a paired cluster-aware
model with a small-sample or wild-cluster procedure. A sign-flip test may appear only as a
sensitivity analysis under an explicit symmetry assumption. H5 may use design-based
randomization inference only according to its actual blocked AI-share assignment mechanism.

H1 succeeds only if all are true:

1. the Holm-adjusted first-paper-family test is below 0.05;
2. the 95% interval is entirely above zero;
3. the relevant technology contrast reaches the frozen SESOI or is reported as statistically
   detectable but practically small;
4. parse, grounding, leakage, balance, and ledger quality gates pass;
5. the frozen family weights, activity and marginal-action balance, and dependency reconciliation
   pass; and
6. the held-out market-type replication has the same sign and no preregistered material
   contradiction, if that replication's data gate passed before freeze.

Portfolio overlap and strategy-fingerprint dispersion are ordered secondary outcomes. Rationale
similarity is exploratory and never mechanistic evidence.

## Parameters that must be locked

Nothing in this section is frozen yet. The preregistration artifact must resolve and hash all of
the following before any confirmatory call:

- **Models and lineage:** exact immutable model releases, provider, checkpoint/revision date,
  open-weight checkpoint hash, alias-resolution evidence, and the same-model/same-provider/
  cross-provider lineage map used by H3.
- **Technology × ecology construction:** eligible LLM and classical families; homogeneous-family
  selection/rotation; heterogeneous family count; within-family variation; equal or justified
  population family weights; agent counts; activity targets; marginal-action handling; capital,
  information, action-space, cost, and constraint matching.
- **Prompts and harnesses:** fully rendered system/task prompts and hashes, all five MPHIQ bits,
  profile assignments, information partitions, paraphrase role, temperature, reasoning effort,
  memory, retry policy, and provider-specific differences. Prompt pressure remains future H12.
- **Trajectories and windows:** generator version and parameters, independent synthetic trajectory
  identifiers, exact nonoverlapping historical windows and content hashes, overlap/common-shock
  cluster map, leakage cutoffs, and held-out market-type split.
- **Analysis:** primary/secondary outcomes, family-weighted estimands, final SESOIs and equivalence
  margins, top-level sample size, model and interval procedure, missingness and partial-unit rule,
  balance tolerances, ordered H1/H3/H4 multiplicity family, and all H5 family contrasts.
- **Data lineage:** source URLs and retrieval dates, licenses, raw and transformed hashes,
  transformation code/version, schema, exclusions, and manifest-to-paper table/figure lineage.

The pilot may estimate nuisance variance and failure rates without inspecting confirmatory data.
Power simulations must use the full assignment, family weighting, within-unit dependence,
overlap/common-shock clusters, model/provider heterogeneity, missingness, and multiplicity. Power
and sample-size claims use counts of independent trajectories/windows or H5 market replicas—not
seeds, agents, pairs, calls, steps, symbols, or prompts. A single run can never satisfy a paper
claim or replication gate.

## Equivalence and safety

- “Same” requires both TOST one-sided tests to reject outside a preregistered equivalence band.
- Provisional prompt-effect equivalence bounds are `[-0.05, +0.05]` in κ; final margins require
  pilot-scale justification before labels are unblinded.
- Zero tolerated fabricated evidence is the release target. The statistical safety endpoint is
  the observed grounding-failure rate with an interval; no experiment may claim a literal
  guarantee that a generative model cannot hallucinate.

## Exclusion and failure rules

- A malformed response is retried once, then scored as hold with `parse_ok=false` and included.
- The final agent-, cell-, and top-level-unit missingness thresholds and partial-unit handling must
  be frozen before confirmation. Treatment-dependent failure is an outcome and is reported by
  technology, ecology, family, and top-level unit.
- Strict-grounding failures remain logged and make the strict run fail verification; they are
  never silently repaired into supported claims.
- Provider failure after the configured retry ceiling aborts the run atomically. Partial runs
  are not analyzed.
- No post-hoc agent, step, symbol, market, participant, or outcome deletion is allowed.

## Freeze gates

1. `flock validate` reports `scaffold_ok=true`, `execution_ready=true` for the exact first-paper
   scope, and no required dataset, model, lineage, analysis, or runner blocker.
2. `flock run configs/experiments/exp-000-smoke.yaml`, `flock verify-run <run>`, and the complete
   tests/linter pass.
3. Pilot power simulations set top-level trajectory/window and H5 market-replica counts, final
   SESOIs/equivalence margins, and the small-sample inference method.
4. The exact models, lineage, family weights, prompts/harnesses, trajectories/windows, dependency
   clusters, data lineage, missingness, outcomes, and multiplicity families listed above are
   exported and reviewed without confirmatory outcomes.
5. The simulator has a complete [ODD report](https://doi.org/10.18564/jasss.4259) and the study has
   a complete [STRESS report](https://doi.org/10.1080/17477778.2018.1442155).
6. The manuscript/release checklist maps every applicable item in the
   [NeurIPS paper checklist](https://neurips.cc/public/guides/PaperChecklist),
   [AEA Data and Code Availability Policy](https://www.aeaweb.org/journals/data/data-code-policy),
   and [ACM artifact criteria](https://www.acm.org/publications/policies/artifact-review-and-badging-current)
   to a verifiable artifact, including a master reproduction path and data-availability statement.
7. Commit the frozen artifacts and record the commit SHA. Only then create the immutable
   [`prereg-v1` git tag and OSF registration](https://osf.io/registries); record both identifiers
   here before the first confirmatory provider call.

Frozen commit SHA: **not available; freeze gates are not met.**

OSF registration DOI/URL: **not available; freeze gates are not met.**

## Amendments log

| Date | Amendment | Rationale |
|---|---|---|
| — | — | — |
