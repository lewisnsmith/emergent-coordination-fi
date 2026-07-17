# 06 — Pre-registration

**Status: DRAFT; not frozen and not eligible to freeze yet.** The synthetic pilot, real input
datasets, independent windows, exact provider releases, and power simulations must pass the gates
below before the first confirmatory frontier-model call. After freeze, changes require a dated
amendment and a new confirmatory split.

## Confirmatory structure

The full catalog contains H1–H12 plus H2b, but they are not one indiscriminate p-value family.

- **Primary family:** H1 equity replay and prediction-market replication.
- **Mechanism/moderator family:** H3, H4, and the locked H12 contrasts selected by the blinded
  pilot. H2 is a separately harmonized external-anchor analysis.
- **Market-consequence family:** H2b and H5, randomized at the whole-market-replica level.
- **Human/forecast family:** H6 and H7 only after human-study approval and verified adoption
  inputs.
- **Transport/causal/data family:** H8–H11 under their separate protocols. Detection under H9
  cannot establish H10 causation.

Holm correction applies within each locked confirmatory family. High-dimensional exploratory
MPHIQ screening uses hierarchical FDR and must be confirmed on untouched blocks.

## Primary H1 outcome

`Δκ = κ(LLM cohort) − κ(baseline cohort)` on the complete `(step, symbol)` action grid. Each
effect is computed within a market-window/seed block. Inference uses paired sign-flip
randomization over independent blocks plus a block-level 95% interval. Agent calls, steps,
agent pairs, paraphrases, and overlapping windows are not independent observations.

H1 succeeds only if all are true:

1. the Holm-adjusted randomization p-value is below 0.05;
2. the 95% interval is entirely above zero;
3. the effect is at least the provisional SESOI `Δκ = 0.10` or is reported as statistically
   detectable but practically small;
4. parse, grounding, leakage, balance, and ledger quality gates pass;
5. the held-out market-type replication has the same sign and no preregistered material
   contradiction.

Portfolio overlap and strategy-fingerprint dispersion are ordered secondary outcomes. Rationale
similarity is exploratory and never mechanistic evidence.

## Locked design parameters

- **Pilot:** 3 seeds, short blocks, fractional prompt-pressure screen, no confirmatory claim.
- **Provisional confirmation:** 10 seeds per cell; increase to at most 20 only from blinded
  simulation-based power analysis. This is a planning value, not a frozen sample size.
- **Cohorts:** real replay configs currently specify 12 frontier LLM, 12 heterogeneous baseline,
  and 12 random-null agents. Any change occurs before freeze and preserves matched capital.
- **Models:** exactly the dated frontier-eligible releases in `configs/models.yaml`: two OpenAI,
  two Anthropic, one Google, and local `gpt-oss-120b`. Reverification is required on execution
  day; model aliases without immutable releases are recorded as a validity limitation.
- **Prompts:** five written semantic paraphrases from `configs/prompts/catalog.yaml`, nested
  within blocks. “Likely prompt” population weights remain disabled until empirical elicitation.
- **Pressure:** 24 cells (`3×2×2×2`), never the stale 16-cell interpretation.
- **MPHIQ:** all 32 `M P H I Q` codes, `1=same`, `0=balanced different`.
- **Datasets/windows:** not yet lockable. Only the synthetic dataset is acquired. The exact real
  windows and content hashes must be inserted in the frozen artifact produced by `flock validate`.

## Equivalence and safety

- “Same” requires both TOST one-sided tests to reject outside a preregistered equivalence band.
- Prompt-pressure “better” requires quality improvement above its SESOI and safety/suitability
  noninferiority.
- Provisional prompt-effect equivalence bounds are `[-0.05, +0.05]` in κ; final margins require
  pilot-scale justification before labels are unblinded.
- Zero tolerated fabricated evidence is the release target. The statistical safety endpoint is
  the observed grounding-failure rate with an interval; no experiment may claim a literal
  guarantee that a generative model cannot hallucinate.

## Exclusion and failure rules

- A malformed response is retried once, then scored as hold with `parse_ok=false` and included.
- If any agent exceeds 20% parse failure, the run fails its quality gate and is excluded exactly
  as preregistered; its existence and diagnostics remain reported.
- Strict-grounding failures remain logged and make the strict run fail verification; they are
  never silently repaired into supported claims.
- Provider failure after the configured retry ceiling aborts the run atomically. Partial runs
  are not analyzed.
- No post-hoc agent, step, symbol, market, participant, or outcome deletion is allowed.

## Freeze gates

1. `flock validate` reports `scaffold_ok=true` and no required dataset/model blocker.
2. `flock run configs/experiments/exp-000-smoke.yaml`, `flock verify-run <run>`, and the complete
   tests/linter pass.
3. Pilot power simulations set independent block counts and final SESOI/noninferiority margins.
4. Dataset/window hashes, immutable model IDs, treatment assignments, outcomes, and multiplicity
   families are exported and reviewed without looking at confirmatory outcomes.
5. Commit the frozen artifacts, record the commit SHA here, and tag `prereg-v1`.

Frozen commit SHA: **not available; freeze gates are not met.**

## Amendments log

| Date | Amendment | Rationale |
|---|---|---|
| — | — | — |
