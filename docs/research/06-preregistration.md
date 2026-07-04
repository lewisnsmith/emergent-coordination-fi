# 06 — Pre-registration

**Status: DRAFT — to be frozen before the first real-model sweep (exp-001).**
Until frozen, this document may change freely. After freezing, changes go only in the
Amendments log below, with rationale and date.

## Frozen elements (on freeze)

### Hypotheses
H1–H5 exactly as stated in [01 — Research question](01-research-question.md). Confirmatory
family for Holm–Bonferroni: {H1, H2, H3, H4, H5}. Everything else is exploratory.

### Primary outcome
Δκ = mean pairwise Cohen's κ (LLM cohort) − mean pairwise Cohen's κ (baseline cohort), on
identical information sets, replay topology, aggregated across seeds by run-level mean.
Success criterion for H1: permutation p < 0.05 (Holm-adjusted) and Δκ 95% BCa CI excluding 0.

### Secondary outcomes
Portfolio overlap contrast; fingerprint-dispersion contrast; H2 anchor comparisons (LSV on
13F panel vs LSV on LLM cohort under matched activity filters); H3 within/cross-provider κ
contrast; H4 persona-vs-information dispersion contrast; H5 cascade frequency contrast.

### Design parameters (filled at freeze from pilot)
- Seeds per cell: ___ (from `stats.power_seeds` on exp-000 pilot variance; target power 0.8
  for Δκ = 0.1 at α = 0.05).
- Cohort size per run: ___ (default 8 LLM + 8 baseline + 8 null).
- Datasets/windows: enumerated list with content hashes.
- Model list with exact model IDs and parameters.
- Paraphrase battery: k = 5 task-prompt paraphrases, written before any real-model run.

### Exclusion rules
- Agent-steps with `parse_ok = false` after one retry are scored as `hold` and *included*
  (they are behavior, not noise); runs where any agent exceeds 20% parse failures are excluded
  and the exclusion reported.
- API failures after 3 retries abort the run; partial runs are never analyzed.
- No post-hoc removal of agents, steps, or symbols.

### Analysis plan
Exactly the pipeline in `src/flock/analysis/` at the freeze commit: metric hierarchy of
[03 — Metrics](03-metrics.md), permutation inference with agent-level relabeling, BCa
bootstrap, Holm–Bonferroni over the confirmatory family. Analysis code is frozen by git SHA;
any change after freeze is an amendment.

## Freeze procedure

1. Complete exp-000 pilots; run power analysis; fill the blanks above.
2. Commit with message `preregistration: freeze v1` and tag `prereg-v1`.
3. Record the commit SHA here: `________`.

## Amendments log

| Date | Amendment | Rationale |
|---|---|---|
| — | — | — |
