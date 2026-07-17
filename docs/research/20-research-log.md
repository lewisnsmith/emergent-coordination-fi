# 20 — Research Log

**Status: ACTIVE. Last updated: 2026-07-17.** This file begins as a dated reconstruction from the
repository and the 2026-07-17 hardening review. It must not be represented as a contemporaneous
record of earlier work. Future entries should be written when decisions are made, before outcomes
are known when possible, and should link to immutable evidence.

## Entry format

Each future entry records: date and timezone; question or trigger; evidence inspected; decision;
alternatives rejected; whether outcomes were visible; expected consequence; linked issue, commit,
or artifact; and unresolved questions. Corrections append a new entry rather than silently editing
the original account.

## 2026-07-17 — Preserve the pre-hardening state

- **Trigger:** Begin turning a broad experiment scaffold into an API-key-to-paper workflow without
  erasing prior work.
- **Evidence:** Existing repository, tests, configs, research documents, and working tree.
- **Decision:** Preserve the starting point in checkpoint commit `e23fb37`; continue on
  `feat/paper-ready-experiments`; do not rewrite history to create a cleaner-looking narrative.
- **Outcome visibility:** No confirmatory frontier-model outcomes were available.
- **Open question:** Which historical decisions can be supported by records outside git and should
  be added to this reconstruction by Lewis?

## 2026-07-17 — Pseudoreplication discovered in the paper path

- **Trigger:** Audit whether the existing significance output used the independent unit promised
  by the preregistration draft.
- **Problem:** A single run could export paper-like significance using agents or repeated nested
  observations. Agents, pairs, steps, prompts, retries, and model seeds that share one market path
  do not create independent evidence about the study-level effect.
- **Decision:** Treat an independently generated synthetic trajectory or a nonoverlapping
  historical window/dependence cluster as the highest inferential unit. Make single-run analysis
  diagnostic only; reject duplicated block evidence; require block-level effects for paper claims.
- **Alternatives rejected:** Reporting a larger agent-level `n`; treating response seeds as market
  replications; relabeling overlapping windows as independent; preserving an attractive p-value
  with a disclaimer.
- **Outcome visibility:** This was a design/software audit. No real confirmatory result was used to
  choose the correction.
- **Evidence:** Safeguard commit `049b663`; current independent-unit contract in
  [06 — Preregistration](06-preregistration.md) and [12 — Statistical Analysis Plan](12-statistical-analysis-plan.md).
- **Open question:** The final small-sample estimator, SESOIs, multiplicity family, and top-level
  sample size still require outcome-blind simulation and qualified statistics review.

## 2026-07-17 — Baseline diversity confound discovered

- **Trigger:** Ask whether the original LLM-versus-classical comparison isolated technology.
- **Problem:** Comparing one homogeneous or closely related LLM cohort with a deliberately
  heterogeneous mixture of classical strategies changes both technology and ecology. A difference
  could be caused by supplied family diversity rather than an LLM-specific mechanism.
- **Decision:** Cross technology with ecology. Compare homogeneous LLM and classical cohorts and
  heterogeneous LLM and classical cohorts under matched cohort size, capital, information,
  constraints, activity, and marginal actions. Estimate within-ecology technology contrasts and
  the technology-by-ecology interaction with frozen family weighting and leave-one-family-out
  checks.
- **Alternatives rejected:** Keeping the heterogeneous classical mixture as the only control;
  describing the confound as a limitation without redesigning; selecting classical strategies
  after seeing LLM results.
- **Outcome visibility:** No real confirmatory result was used to choose the redesign.
- **Evidence:** Research-contract commit `8f4c7d8`; design in
  [01 — Research Question](01-research-question.md) and
  [02 — Experimental Design](02-experimental-design.md).
- **Open question:** Exact eligible model and classical families, activity matching tolerances,
  population weights, and a genuinely held-out family remain to be frozen.

## 2026-07-17 — Narrow the paper and novelty claim

- **Trigger:** Prior-art and admissions-oriented reviews found that the broad H1–H12 agenda
  exceeded what one paper could authenticate and that convergence/herding claims already exist in
  related work.
- **Decision:** Center the first paper on H1/H3/H4, with H5 as a separately randomized,
  simulator-bounded extension. Describe the contribution as matched-control decomposition of
  technology and ecology, not first evidence that LLM traders converge. Treat H2 as conditional on
  harmonized lawful data and move H6–H12 to the future program.
- **Alternatives rejected:** Claiming universal provider behavior; calling agreement collusion;
  treating simulator effects as real-market causal effects; maximizing the number of partially
  completed hypotheses.
- **Outcome visibility:** No confirmatory frontier-model outcomes were available.
- **Evidence:** Commit `8f4c7d8`; [07 — Related Work](07-related-work.md).
- **Open question:** The final paper claim must be restated after exact dated endpoints and data
  availability are known, without broadening beyond the sampled domain.

## 2026-07-17 — Implement pre-execution and audit safeguards

- **Trigger:** Determine whether API keys alone could safely produce auditable evidence.
- **Decision:** Add or strengthen strict study compilation, dated pricing, provider attempt
  metadata, atomic resumability, complete dataset-bundle hashes, market/ledger invariants, an
  environment doctor, type checking, and canonical metric tests. Preserve terminal failures and
  mock/real status rather than silently coercing them into usable observations.
- **Evidence:** Commits `9810f53` through `2c858af` on the paper-hardening branch. The commit range
  is implementation evidence, not evidence that live endpoints, datasets, or scientific results
  have passed their gates.
- **Outcome visibility:** Mock fixtures and automated tests were visible; no paid confirmatory
  study result was used.
- **Open questions:** Study-level release bundles, claim-locked paper generation, clean-room
  reproduction, exact live endpoint availability, final licensed datasets, and external reviews
  remain incomplete until separately verified.

## Next entries required

Do not collapse these into one retrospective success narrative. Add separate entries for:

1. canary authorization, exact model resolution, and canary outcome;
2. pilot freeze, blinded nuisance estimates, failure/cost observations, and stop/go decision;
3. any protocol or analysis amendment, including who proposed and approved it;
4. failed, null, contradictory, or surprising pilot findings;
5. preregistration freeze, commit SHA, OSF identifier, and first confirmatory call time;
6. independent reviews and every resulting change or declined suggestion; and
7. clean-room reproduction outcome and final claim/limitation sign-off.

The conceptual consequence of the first two redesigns is documented in
[21 — Mistake Case Study](21-mistake-case-study.md).

