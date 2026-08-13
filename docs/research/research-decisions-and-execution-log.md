# Research decisions and execution log

**Status: ACTIVE. Last updated: 2026-08-12.** This file begins as a dated reconstruction from the
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
  [Preregistration](preregistration.md) and [Statistical Analysis Plan](experimental-methods-and-statistical-analysis.md#statistical-analysis-contract).
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
  [Research Question](research-scope-outcomes-and-evidence.md) and
  [Experimental Design](experimental-methods-and-statistical-analysis.md).
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
- **Evidence:** Commit `8f4c7d8`; [Related Work](research-scope-outcomes-and-evidence.md#prior-work-and-novelty-boundaries).
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

## 2026-07-23 — Reconcile and protect the working branches

- **Trigger:** Integrate the paper-hardening branch without losing the repository-condensation
  work or treating generated mock artifacts as evidence.
- **Evidence:** Dirty-tree inventory, binary patch, branch graph, conflict audit, test suite, and
  tracked paper figures.
- **Decision:** Preserve `docs/condense-repo` as a recovery point; create
  `feat/paper-ready-reconciliation`; commit duplicate removal and document condensation
  incrementally; merge `feat/paper-ready-experiments`; retain feature semantics where the shorter
  text was scientifically outdated.
- **Recovery evidence:** The external worktree patch and a clean-checkout reapplication had the
  same SHA-256, `25cd2aa9f8f426987202a965713a0f82d0d88fa7419161d81a56f7334e812c63`.
  Git history remains the durable recovery path.
- **Generated evidence:** Remove five tracked figures/tables produced from one old mock run. The
  files remain recoverable from commit `beb9263`; paper results remain locked off and single-run
  paper export is tested to fail.
- **Outcome visibility:** Local synthetic mock outputs were visible. No paid or confirmatory
  outcome informed the reconciliation.

## 2026-07-23 — Record the idea genealogy without a priority claim

- **Trigger:** Ask how to describe independently motivated questions when overlapping papers
  already existed.
- **Contemporaneous evidence:** Commit `356963d` recorded the initial repository formulation on
  2026-07-04 at 02:29 PDT; commit `26089c9` added the formal question, design, metrics,
  preregistration draft, and related work four minutes later.
- **Decision:** This establishes that the design existed in the repository by that date. It does
  not prove conception before literature exposure, publication priority, or novelty over prior
  papers. Any statement that the motivating intuition was reached independently must be a truthful
  first-person recollection by Lewis and labeled as such.
- **Positioning:** Make no broad first claim. Present the work as a matched, preregistered
  replication/extension and document subsequent corrections rather than backdating them.
- **Outcome visibility:** No confirmatory outcome was available.

## 2026-07-23 — Refresh prior art and empirical status

- **Trigger:** Verify whether overlapping papers were incorporated and whether any real
  experiments had run.
- **Evidence:** Primary arXiv, ACL, NeurIPS, publisher, NBER, SSRN, and DOI records; local ignored
  result manifests; repository validation; a fresh seed-4242 smoke run.
- **Decision:** Add a reproducible literature search log and complete bibliography entries for
  retained direct precedents, H2 measurement-bias work, monoculture foundations, and H5 market
  comparators. Correct the mistaken interpretation of Klein's DOI as a correction notice.
- **Execution status:** A fresh synthetic mock smoke run produced 720 decisions, 1,274 fills, and
  720 portfolio rows and passed logical verification. Local history also contains mock
  shared-exchange diagnostics. No paid frontier-model canary, pilot, confirmatory run, frozen
  preregistration, or paper-level empirical result exists.
- **Open questions:** H2 harmonization, raw-run aggregation, H5 gates, complete mock
  materialization, licensed real data, exact endpoints, and human review remain open.

## 2026-07-23 — Execute the complete feasible offline matrix

- **Trigger:** Require a terminal rehearsal before any paid canary and prohibit unexecuted or mock
  outputs from appearing as scientific results.
- **Design correction:** Reallocate MPHIQ from two blocks with two nested seeds to four matched
  replay blocks with one nested seed. This preserves 197 planned runs and 232,360 calls while
  raising H4's independent-unit count from two to four.
- **Execution evidence:** Plan hash
  `539ac6c3591f37e4a410d06ed1f98a2575b2d6cc9270f540ffa646602eba26b6`;
  materialization hash
  `1f5bb982db6adef12561b2718c9dfb87bd40c23f23c8b51f96f5f181debbd29d`.
  The ignored ledger records 149 completed and verified mock runs, 48 explicitly blocked H5
  assignments, and zero failed or pending assignments.
- **Reproducibility evidence:** The 144 confirmatory H1/H3/H4 runs aggregated across four
  independent blocks with hash
  `f66cac434c3c881f816a8f0df96f0995d1f4cbf60a14236dc3aa0e94f3d0fb71`.
  A second aggregation was byte-identical; the crossed mock analysis verified and reproduced from
  an empty directory.
- **Evidence boundary:** Generated runs and analytical outputs remain ignored. The release is
  marked `mock`, `paper_requested=false`, `paper_eligible=false`, and
  `mock-rehearsal-only`; no numerical mock outcome is treated as a finding.
- **Open questions:** H2 end-to-end harmonization, H5 simulator gates, three draft statistical
  contract discrepancies, exact live endpoints/data, paid canary authorization, preregistration,
  and independent human review remain open.

## 2026-08-06 — Add local fidelity and quantization propagation as H13

- **Trigger:** Lewis identified the scientific and practical narrative behind using lower-weight
  local models: test whether their convergence and behavior match sampled frontier models, use
  open weights for mechanistic intervention, measure how quantization errors propagate through
  long financial chains, and learn where cheaper models remain sufficiently informative and
  customizable.
- **Evidence inspected:** Primary scaling, quantized-reasoning, long-context, financial-reasoning,
  sparse-autoencoder, and cross-architecture mechanism studies recorded in
  [Related Work](research-scope-outcomes-and-evidence.md#prior-work-and-novelty-boundaries) and [`literature-search-and-screening-log.yaml`](literature-search-and-screening-log.yaml).
  Existing work supports the question but already occupies generic claims that quantization can
  preserve or harm reasoning and that early errors can cascade.
- **Decision:** Add H13 as future work with two linked but nonexchangeable studies. `exp-025`
  compares deliberately sampled local and frontier endpoints descriptively; `exp-026` uses
  same-checkpoint precision pairs to identify quantization effects and test their propagation and
  mechanisms. Keep the first-paper H1/H3/H4 estimand unchanged.
- **Identification rule:** Use an executable financial oracle for correctness, same-checkpoint
  BF16/FP16 for quantization loss, and cached frontier outputs for behavioral similarity. Separate
  model family, parameter scale, weight precision, activation precision, and KV-cache precision.
  Generated structured calculation ledgers are auditable task artifacts, not faithful hidden
  chain-of-thought or mechanistic evidence.
- **Cost decision:** Start with a local precision screen, cap the frontier bridge near 3,802 API
  calls, cap mechanistic discovery at 24 H100-hours, and authorize an approximately 80-hour
  confirmation only after a behavioral gate. These sidecar costs are not silently added to the
  older full-program totals.
- **Alternatives rejected:** Treating the native MXFP4 local endpoint as evidence of a causal
  quantization effect; substituting small models for H1 frontier models without equivalence tests;
  pooling scale and precision into MPHIQ's model bit; starting a broad activation sweep before a
  behavioral effect; or claiming generality from one checkpoint family.
- **Outcome visibility:** No paid, frontier, H13, or mechanistic result was available. The decision
  was made from the stated research goal, current design constraints, and prior work.
- **Open questions:** Exact licensed checkpoint families and sizes, quantizer ladder, held-out
  domains/families, final equivalence margins, local throughput, frontier endpoint pair, and
  whether profile-state customization precedes any LoRA/fine-tuning treatment remain unfrozen.

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
[the dated correction record](#2026-07-17--pseudoreplication-and-ecology-correction-record).

## 2026-07-17 — Pseudoreplication and ecology correction record

**Status: DESIGN CASE STUDY; no empirical effect sizes or p-values are reported here. Last
updated: 2026-07-17.** This case study records a consequential mistake found while hardening Flock
and the associated benchmark redesign. It is not a before/after results comparison, because no
verified paid result is yet available.

### The tempting analysis

Suppose many agents process the same market trajectory. Each agent makes many decisions, each
model may be called with multiple seeds or paraphrases, and pairwise convergence creates still more
rows. It is tempting to compute an agent- or pair-level effect and use the number of agents, pairs,
steps, or calls as the inferential sample size.

That analysis answers a conditional descriptive question—how much the nested observations differ
inside the realized path—but it does not create new independent market histories. Shared prices,
news, opportunity sets, and shocks can make every nested observation move together. More calls on
the same path can make a standard error look arbitrarily precise while adding no independent
evidence about how the effect varies across paths.

Symbolically, let `y[u,t,a]` be an outcome for agent `a` at step `t` in trajectory or window `u`.
The invalid paper path acts as though many `(t,a)` rows are independent. The corrected path first
forms a frozen block effect:

```text
d[u] = aggregate_within_block(treatment outcomes in block u)
     - aggregate_within_block(matched control outcomes in block u)
```

Inference is then based on independent `u` blocks or their declared dependence clusters. Agent,
pair, step, prompt, retry, and response-seed variation remains useful for estimating `d[u]`,
diagnosing mechanisms, and measuring reliability, but it cannot increase confirmatory `n`.

### A second mistake hidden in the baseline

Even correct block-level inference cannot rescue a confounded contrast. The original framing risked
comparing a closely related LLM cohort with a purposefully diverse collection of classical
strategies. In that comparison, “LLM versus classical” also means “homogeneous versus
heterogeneous.” A convergence difference cannot be attributed to technology alone.

The redesign crosses the factors:

| Technology | Homogeneous ecology | Heterogeneous ecology |
|---|---|---|
| LLM | Repeated agents within one exact frozen family, estimated family by family | Frozen balanced mixture across sampled families |
| Classical | One strategy family with parameter/seed variation, estimated family by family | Frozen balanced mixture across classical families |

The paper-level estimands are within-ecology technology contrasts and the
technology-by-ecology interaction. Family balancing prevents a provider with more endpoints from
silently receiving more weight. Matching activity, capital, information, constraints, turnover,
and action marginals reduces alternative explanations but does not establish a universal model
effect.

### What changed in the repository

- Single-run analysis is diagnostic and cannot become paper evidence merely by exporting a
  significance result (`049b663`).
- The research contract defines trajectories/nonoverlapping window clusters as the highest
  independent units and explicitly prohibits nested observations from inflating `n`.
- The compiled study design balances `technology × ecology` cells, family rotations, held-out
  sets, calls, and declared budgets before execution.
- Study-level analysis rejects duplicated block evidence and documents when a sign-flip sensitivity
  relies on symmetry rather than an actual randomized assignment.

These safeguards reduce known failure modes; they do not prove that every dependence structure or
confound has been eliminated. That judgment still needs simulation recovery, a frozen analysis
plan, and independent statistics review.

### The honest before/after artifact to publish later

After a real pilot exists, create a release-derived comparison with no hand-entered numbers:

1. show the invalid agent-level analysis only as a labeled diagnostic demonstration;
2. show the corrected block effects with every independent unit visible;
3. report how point estimates, intervals, and effective `n` change, including null or inconclusive
   outcomes;
4. identify any remaining cluster, overlap, missingness, or activity-balance sensitivity; and
5. link both displays to the same hashed inputs and analysis code.

Do not fill this section with illustrative effect sizes that could be mistaken for observed
results. If the corrected result is weaker, reverses, or becomes inconclusive, that is the central
lesson rather than a presentation problem.

### Why this is evidence of research maturity

The important contribution is not that the first design had no flaws. It is that a consequential
error was made legible, corrected before confirmatory calls, encoded as an automated release gate,
and retained in the public history. The defensible story is therefore one of error detection and
scientific revision, not retrospective perfection. The dated reconstruction is in
[this log](#2026-07-17--pseudoreplication-discovered-in-the-paper-path), and human reviewers should challenge the correction using
[Independent review protocol and responses](independent-review-protocol-and-responses.md).

## 2026-07-23 — Preserve the hardening and polish snapshots

- **Trigger:** Record the implementation and reduction audits before their active documents are
  absorbed into lifecycle manuals.
- **Dated verification:** The hardening snapshot recorded 184 passing tests, Ruff success, Pyright
  success, a 720-decision/1,274-fill/720-portfolio smoke run, 149 completed mock assignments, 48
  explicitly blocked H5 assignments, 144 H1/H3/H4 runs across four blocks, and byte-identical
  crossed aggregation hash
  `f66cac434c3c881f816a8f0df96f0995d1f4cbf60a14236dc3aa0e94f3d0fb71`. These are historical
  counts, not a current verification claim.
- **Dated authorization proposal:** The hardening path proposed a `$50` canary and a cumulative
  paid pilot below `$5,200`. The older cost runbook separately proposed 74,880 first-paper calls
  and much larger full-program ceilings. None is current authorization after the personal-budget
  staging decision.
- **Polish gate:** The 2026-07-23 audit found the mock H1/H3/H4 and H2 software gates substantially
  implemented, H5 still disabled, and manuscript compilation blocked by the environment. It
  deferred broad consolidation at that time. The explicit 2026-08-12 consolidation instruction
  supersedes that process gate without changing any scientific or release gate.
- **Reduction rules retained:** Map every source before deletion, use Git as recovery, search code
  and documentation references separately, edit at most five files per phase, and run tests,
  Ruff, and Pyright. The durable form now lives in `CLAUDE.md`.
- **Presentation boundary:** Git establishes dated repository history, not idea priority,
  authorship, understanding, or scientific novelty. Mock execution may validate software but is
  never paper-eligible empirical evidence.

## 2026-08-10 — Adopt the personal-budget local-first lane

- **Trigger:** Lewis set a personal hardware budget near `$2,000`, a direct software/data/API
  budget near `$200–300`, and identified an existing 64 GB RAM/RTX 2080 Ti workstation. He also
  retained the option to apply for OpenAI and Anthropic research credits.
- **Decision:** Keep every hypothesis, but run evidence audit, workstation benchmarking, financial
  scoring-key construction, local H13 precision/fidelity work, and gated H8 mechanisms before the
  frontier-heavy program. Keep H1/H3/H4 as the configured first paper until machine-readable
  contracts are reconciled.
- **Three outputs:** Preserve public research datasets, owned out-of-sample alpha evaluation, and
  evidence-backed AI-agent trading-risk findings as coequal outputs with separate verdicts.
- **External evidence:** Reuse results only when population, treatment, comparator, estimand,
  outcome, independent unit, provenance, and validation are at least as strong as the registered
  question. Otherwise use the paper for methods, prior art, or a partial bridge.
- **Trading boundary:** Lock simulation signatures before real-market transport, lock trading
  rules before a prospective paper window, report every tried variant and failed signal, and do
  not treat paper performance as live-capital authorization.
- **Unfrozen:** Exact checkpoints, frontier endpoints, GPU purchase, margins, task depths/sample
  caps, market panel, paper-trading venue/duration, and whether H13/H8 becomes a first owned paper.
- **Outcome visibility:** No new model, market, alpha, or mechanistic result informed this staging
  decision.

## 2026-08-12 — Clarify the financial scoring key

- **Trigger:** The phrase “financial oracle” in the 2026-08-06 entry was mistaken for another
  model-comparison stage.
- **Clarification:** Active documentation now says **financial scoring key**: deterministic code
  and frozen intermediate values that score financial correctness. Same-checkpoint BF16/FP16
  comparisons identify quantization effects, while cached frontier outputs measure descriptive
  behavioral similarity. The three references are nonexchangeable.
- **Historical integrity:** The original 2026-08-06 wording remains above as recorded. This later
  entry corrects active terminology rather than rewriting history.

## 2026-08-12 — Consolidate the research record

- **Trigger:** Replace overlapping topic files with lifecycle manuals without losing hypotheses,
  claims, experimental contracts, dated conflicts, or release boundaries.
- **Recovery:** Branch `docs/consolidate-research-record`; recovery baseline commit `697f94a`.
  The baseline preserved the dirty README and untracked local-first plan before consolidation.
- **Preservation audit:** External ledger `/tmp/flock-consolidation-ledger.tsv` maps 397 source
  heading blocks by hash and disposition; it reported zero unmapped source documents before edits.
- **Controlling resolutions:** Active records use financial scoring key; describe H5 as a
  step-synchronous price-time-priority call process with an intra-step limit-order book; use the
  configured `0%, 10%, 25%, 50%, 75%, 100%` H5 grid; treat the eight-level grid as unfrozen; keep
  H1/H3/H4 together, H2 descriptive, and H5 separate; and leave both H1 directional decision
  rules unfrozen.
- **Budget resolution:** The `$2,000` hardware and `$200–300` direct-spend lane controls current
  staging. The 74,880-call, 232,360-call, `$5,200`, and larger scenarios remain dated or
  funding-contingent, never current authorization.
- **Evidence status:** Internal deterministic mock reproduction exists. Independent public
  clean-room reproduction, paid evidence, frozen preregistration, independent review, and
  paper-eligible results do not.

### Source-to-destination consolidation record

| Sources | Canonical destination | Disposition |
|---|---|---|
| Research question, follow-up questions, related work, methodology scope/backlog, and local-first outcome/evidence rules | Research scope, outcomes, and evidence | merged; active conflicts resolved |
| Experimental design, metrics, statistical plan, MPHIQ, profiles, and prompt pressure | Experimental methods and statistical analysis | merged |
| Market dynamics/trust/adoption, mechanistic interpretation, simulation-to-real attribution, simulator ODD/STRESS, H13 methods, and methodology threats/visualizations | Experimental methods and statistical analysis | merged; H5 implementation truth controls |
| Datasets, data products, grounding, and release checklist | Data provenance, artifacts, and release | merged |
| Hardening blockers/safeguards and the methodology data dictionary/result-trust procedure | Data provenance, artifacts, and release | merged; dated counts retained here only |
| Budget-constrained plan, cost runbook, and low-cost engineering/sample-cap material | Local-first execution, costs, and risk roadmap | merged; old budgets historical only |
| Mistake case study, dated hardening evidence, and repository-polish history | Research decisions and execution log | historical only or merged |
| Authorship and tool use | Authorship, AI use, and accountability | renamed and expanded |
| Independent review and response | Independent review protocol and responses | renamed |
| Literature search log | Literature search and screening log | renamed |
| Preregistration | Preregistration | retained and corrected while unfrozen |

- **Outcome visibility:** This was information architecture and conflict reconciliation. No
  scientific outcome, paid call, market result, or trading result was generated or inspected.
