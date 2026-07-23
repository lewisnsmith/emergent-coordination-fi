# 25 — API-Key-to-Paper Hardening: Implementation Status

**Audit date:** 2026-07-23
**Implementation branch:** `feat/paper-ready-reconciliation`
**Scientific status:** scaffold verified; confirmatory execution blocked

This document consolidates the five requested review lenses, the implemented corrections, and the
remaining execution queue. A checked software item means the code path and automated tests exist;
it does not mean a paid study, empirical result, independent review, or paper release exists.

## Review synthesis

| Review lens | Finding | Implemented response | Remaining gate |
|---|---|---|---|
| Paper stress test | Agent/call-level inference was pseudoreplication; design and claims exceeded the independent evidence | Block-level inference, duplicate trajectory/dependence rejection, nested power, mock/paper separation, claim lock | Freeze the exact top-level model and margins after pilot nuisance estimates |
| Prior-art overlap | Broad LLM convergence, reduced dispersion, herding, common errors, and simulated instability are occupied | Title and contribution narrowed to matched technology-by-ecology controls and component decomposition; real bibliography added | Refresh the evidence map at preregistration and submission |
| Cost/authenticity | Existing totals mixed formulas and agent counts; full H1–H12 scope was not priced | Deterministic call matrix, dated catalog, canary/pilot authorization, high retry envelope, runtime dollar/token/request guard | Reprice exact live endpoints immediately before each authorized stage |
| End-to-end repository audit | Provider retries, cache billing, data hashes, ledger reservations, self-trades, replay gaps, resume behavior, and strict schemas had failure modes | Atomic attempts/cache, classified retry contract, complete bundle hashes, conservation checks, strict configs, terminal manifests, deterministic assignment materialization, and asynchronous binary-contract replay | Resolve and execute the complete compiled matrix; finish H5 mechanics |
| Admissions/authenticity | The repository looked like an ambitious lab agenda rather than completed owned research | Authorship statement, dated research log, public mistake case study, review-response template, and walkthrough/release checklist | Execute one narrow corrected study and obtain three real independent reviews |

## Implemented and verified

### Research contract and study compilation

- The first-paper boundary is H1/H3/H4; H5 is a separate simulator-bounded extension.
- The compiled contract crosses LLM/classical technology with homogeneous/heterogeneous ecology,
  rotates homogeneous families, balances heterogeneous allocations, and holds out a model family.
- Unknown fields, placeholder identifiers, mutable aliases, overlapping independent windows,
  missing prices, unbalanced cells, count disagreements, and authorization overruns fail closed.
- The current deterministic plan resolves to 197 runs, 397,528 agent-steps, and 232,360 calls with
  plan hash `539ac6c3591f37e4a410d06ed1f98a2575b2d6cc9270f540ffa646602eba26b6`.
- `flock materialize-study` deterministically expands those totals into 197 lineage-preserving run
  assignments. It emits runner configs only when dataset, model, persona, prompt, runtime-budget,
  and treatment semantics resolve explicitly. `--allow-unresolved` exports auditable blockers
  without making an assignment executable.

### Provider execution and cost control

- `flock doctor [--live]`, `compile-study`, `validate-study`, and plan-based `estimate` exist.
- Provider attempts retain request/retry/reasoning/cache-token metadata; only classified transient
  failures retry and `Retry-After` is honored.
- Cache writes and run outputs are atomic. Attempts are isolated, checkpointed, and never truncate
  a completed run. Local cache hits are not counted as new billed requests.
- Every frontier experiment requires explicit request, input-token, output-token, and dollar caps.
  The call boundary reserves a conservative worst-case envelope before a provider request.
- The dated YAML catalog is the only price source. Canary audit: 40 calls, about `$1.43` expected,
  `$23.44` high envelope, below the `$50` cap. These are estimates, not authorization to run.

### Provenance, market mechanics, and inference

- Dataset identity covers the complete bundle rather than one parquet file; changing any tracked
  input invalidates dependent verification.
- Replay rejects duplicate symbol/timestamps and uses only timestamps common across symbols.
- Market and ledger tests cover self-trades, counterparty-linked tape, reservations, partial fills,
  fees, cash, inventory, and position limits.
- Canonical LSV uses the contemporaneous expected-buy fraction. Sias is decomposed into following
  own versus other-agent demand and algebraically reconciled.
- Study inference rejects response seeds or relabeled duplicate paths as independent evidence.
  Sign flips are described as symmetry-based except where assignment truly supports randomization.
- The first-paper estimator family-balances all four `technology × ecology` cells, reports both
  within-ecology technology contrasts and their interaction, estimates provider-stratified H3 and
  Hamming-one H4 effects, and applies one frozen Holm correction across H1/H3/H4.
- MPHIQ materialization now expands each cohort into explicit one-agent treatments, validates all
  five factor levels and assignment digests, rejects balance/confounding drift, and propagates the
  treatment into each decision manifest.
- Binary prediction replay uses the union of asynchronous contract timestamps, exposes only active
  contracts with sufficient own history, hides terminal outcome bars, rejects inactive orders,
  prevents truncated-run settlement leakage, and settles internal YES holdings at 0/1.
- Nested simulation power includes blocks, agents, steps, provider heterogeneity, missing blocks,
  and the exact/Monte-Carlo sign-flip boundary. The old normal approximation is diagnostic-only.

### Paper and reproducibility artifacts

- A verified bundle writes independent units, block effects, effects, multiplicity, missingness and
  failures, sensitivities, estimand registry, equivalence/noninferiority results, statistical
  verification, claims, and two claim-linked core figures.
- Paper mode consumes the complete crossed H1/H3/H4 family, requires every aggregate row to cite
  verified treatment runs with matching lineage, hashes every contributing run, and proves that
  nested treatment runs cannot increase independent `n`.
- Paper mode rejects incomplete, unverified, single-run, mock, or preregistration-missing evidence.
- Mock rehearsal uses the same crossed analysis and verification path but requires an explicit
  rehearsal contract and forces `paper_requested=false`, `paper_eligible=false`, mock-only claims,
  and disabled paper-claim flags.
- `flock reproduce` regenerates into an empty directory and requires byte-identical core hashes.
- The manuscript contains methods, robustness, limitations, ethics, reproducibility/data
  availability, funding/conflict language, author responsibility, LLM-use disclosure, and a real
  bibliography. Its result switch remains locked.
- The authenticity package records ownership, AI assistance, design mistakes, unresolved
  weaknesses, independent-review slots, and the 3–5 minute walkthrough path.

## Current verification evidence (2026-07-23)

- Full-suite `pytest`: **182 passed**.
- Ruff: **all checks passed**.
- Pyright: **0 errors, 0 warnings**.
- Fresh offline smoke run: **720 decisions, 1,274 fills, 720 portfolio rows; verification passed**.
- Complete ignored mock matrix: **149 completed and verified, 48 explicitly blocked H5, 0 failed,
  0 pending**; materialization hash
  `1f5bb982db6adef12561b2718c9dfb87bd40c23f23c8b51f96f5f181debbd29d`.
- Raw aggregation: **144 verified confirmatory runs across 4 independent blocks**; two clean
  aggregations were byte-identical with hash
  `f66cac434c3c881f816a8f0df96f0995d1f4cbf60a14236dc3aa0e94f3d0fb71`.
- Crossed mock analysis and clean reproduction both verify with 12 estimands and remain explicitly
  non-paper-eligible. Numerical mock outcomes are ignored and are not reported as findings.
- No paid frontier-model pilot, confirmatory run, or paper-level empirical result exists.
- Repository validation: `scaffold_ok=true`, `execution_ready=false`, no scaffold errors.
- Study materialization: **197 planned mock assignments, 149 executable, 48 H5-blocked**.
- No LaTeX engine is installed in the current environment, so manuscript compilation was not run.

## Open release blockers

### P0 — must clear before any paid call

1. Hydrate or relocate the iCloud `dataless` result artifact detected by `flock doctor`; never
   delete it as an automated workaround.
2. Install the provider/data extras, add keys through the environment, and run bounded
   metadata-only live probes for every exact endpoint. Do not substitute a mutable alias.
3. Acquire and hash the exact equity windows; acquire a legally usable prediction panel only if
   H2/H1 prediction-market harmonization remains in scope.
4. Resolve the live materialized assignments against immutable provider revisions and licensed
   datasets. Offline mock mappings are complete; H5 capital weighting and calibrated background
   demand remain intentionally disabled.
5. Finish H2 end to end: acquire lawful 13F inputs, emit harmonized quarterly activity artifacts,
   build comparable simulated holdings changes, and enforce the activity-match gate.
6. Reconcile the three draft statistical-contract discrepancies before freeze: primary
   small-sample inference versus sign-flip sensitivity, the exact H1 contrasts, and unified Holm
   versus H4 hierarchical FDR.

### P1 — must clear before confirmatory or H5 release

1. Freeze the simulation-derived independent-unit counts, SESOIs, equivalence/noninferiority
   margins, missingness rules, multiplicity family, and blinded variance re-estimation rule.
2. Freeze the commit and rendered inputs, register immutably on OSF, and record the URI/SHA/tag
   before confirmatory calls.
3. Add power artifacts plus the action raster, provider heatmap, and full specification-curve
   figures. Missingness/failure, equivalence/noninferiority, sensitivity, and the complete crossed
   multiplicity family are now wired into paper verification.
4. Rebuild any external prediction dataset under the strict timestamp/rules/terminal-payout
   schema before use. Replay now handles asynchronous listings and YES settlement; direct NO-share
   trading remains unsupported and must not be implied.
5. Keep H5 disabled until persistent orders, cancel/expiry events, seeded fundamental/noise/
   liquidity demand, reconstructable book exports, calibration targets, and all ODD/STRESS checks
   pass. The current exchange is a step-synchronous intra-step book, not a validated continuous
   double auction.
6. Install a LaTeX toolchain and make manuscript compilation part of clean-room CI.
7. Obtain statistics, market-microstructure, and reproducibility reviews; populate the response
   table with real dated reviewer evidence.

## Proposed gated execution sequence

```bash
uv run flock validate
uv run flock doctor
uv run flock compile-study configs/studies/paper-core.yaml \
  --output results/paper-core/plan.json
uv run flock validate-study results/paper-core/plan.json
uv run flock materialize-study results/paper-core/plan.json \
  --output results/paper-core/assignments.json --allow-unresolved
uv run flock estimate --plan results/paper-core/plan.json --stage canary
uv run flock doctor --live
```

Stop if any command fails. `doctor --live`, provider calls, and registration require explicit
authorization. After the P0 materializer/mock-matrix work is complete, the first paid request may
be only the separately approved `$50` canary. Re-estimate before the pilot and keep cumulative paid
pilot authorization below `$5,200`. Confirmatory calls remain unauthorized until all pilot, power,
preregistration, data, failure, drift, throughput, and cost gates pass.

## Defensible current conclusion

The repository now prevents several ways of manufacturing a paper result from invalid evidence and
reproducibly exercises the complete feasible offline path. It is not yet a key-only confirmatory
runner. The next scientifically meaningful milestone is to finish H2 and the remaining H5 and
statistical-contract gates, then request separate authorization for a bounded paid canary—not a
broad H1–H12 execution or a manuscript claim.
