# 25 — API-Key-to-Paper Hardening: Implementation Status

**Audit date:** 2026-07-17  
**Implementation branch:** `feat/paper-ready-experiments`  
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
| End-to-end repository audit | Provider retries, cache billing, data hashes, ledger reservations, self-trades, replay gaps, resume behavior, and strict schemas had failure modes | Atomic attempts/cache, classified retry contract, complete bundle hashes, conservation checks, strict configs, terminal manifests | Materialize and execute the complete compiled matrix; finish prediction-market and H5 mechanics |
| Admissions/authenticity | The repository looked like an ambitious lab agenda rather than completed owned research | Authorship statement, dated research log, public mistake case study, review-response template, and walkthrough/release checklist | Execute one narrow corrected study and obtain three real independent reviews |

## Implemented and verified

### Research contract and study compilation

- The first-paper boundary is H1/H3/H4; H5 is a separate simulator-bounded extension.
- The compiled contract crosses LLM/classical technology with homogeneous/heterogeneous ecology,
  rotates homogeneous families, balances heterogeneous allocations, and holds out a model family.
- Unknown fields, placeholder identifiers, mutable aliases, overlapping independent windows,
  missing prices, unbalanced cells, count disagreements, and authorization overruns fail closed.
- The current deterministic plan resolves to 197 runs, 397,528 agent-steps, and 232,360 calls with
  plan hash `8df6027377f3a1226f62db70acfcc3c2d8824a43960ed6b9ff9e12b2b4e9f015`.

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
- Nested simulation power includes blocks, agents, steps, provider heterogeneity, missing blocks,
  and the exact/Monte-Carlo sign-flip boundary. The old normal approximation is diagnostic-only.

### Paper and reproducibility artifacts

- A verified bundle writes independent units, block effects, effects, multiplicity,
  statistical verification, claims, and two claim-linked core figures.
- Paper mode rejects incomplete, unverified, single-run, mock, or preregistration-missing evidence.
- `flock reproduce` regenerates into an empty directory and requires byte-identical core hashes.
- The manuscript contains methods, robustness, limitations, ethics, reproducibility/data
  availability, funding/conflict language, author responsibility, LLM-use disclosure, and a real
  bibliography. Its result switch remains locked.
- The authenticity package records ownership, AI assistance, design mistakes, unresolved
  weaknesses, independent-review slots, and the 3–5 minute walkthrough path.

## Current verification evidence

- `pytest`: **142 passed**.
- Ruff: **all checks passed**.
- Pyright: **0 errors, 0 warnings**.
- Clean offline smoke run: **720 decisions, 1,236 fills, 720 portfolio rows; verification passed**.
- Repository validation: `scaffold_ok=true`, `execution_ready=false`, no scaffold errors.
- No LaTeX engine is installed in the current environment, so manuscript compilation was not run.

## Open release blockers

### P0 — must clear before any paid call

1. Hydrate or relocate the iCloud `dataless` result artifact detected by `flock doctor`; never
   delete it as an automated workaround.
2. Install provider SDK extras, add keys through the environment, and run bounded metadata-only
   live probes for every exact endpoint. Do not substitute a mutable alias.
3. Acquire and hash the exact equity windows; acquire a legally usable prediction panel only if
   H2/H1 prediction-market harmonization remains in scope.
4. Materialize compiled study cells into resolved experiment configs. The compiler currently
   proves design/count/budget consistency, but it is not yet a complete matrix runner.
5. Finish the family-weighted crossed H1 estimator and H3/H4 paired estimators. The verified bundle
   currently exercises the conservative H1 block path, not the complete final multiplicity family.
6. Run the full internally feasible compiled matrix with mocks and prove every planned cell reaches
   one terminal state before enabling provider calls.

### P1 — must clear before confirmatory or H5 release

1. Freeze the simulation-derived independent-unit counts, SESOIs, equivalence/noninferiority
   margins, missingness rules, multiplicity family, and blinded variance re-estimation rule.
2. Freeze the commit and rendered inputs, register immutably on OSF, and record the URI/SHA/tag
   before confirmatory calls.
3. Add missingness/failure, equivalence/noninferiority, sensitivity/specification-curve, and power
   artifacts to the release bundle; add action raster, provider heatmap, and robustness figures.
4. Implement timestamp-aligned prediction-contract metadata, expiry, settlement, YES/NO semantics,
   and asynchronous listing policies before interpreting prediction replay.
5. Keep H5 disabled until persistent orders, cancel/expiry events, seeded fundamental/noise/
   liquidity demand, reconstructable book exports, calibration targets, and all ODD/STRESS checks
   pass. The current exchange is a step-synchronous intra-step book, not a validated continuous
   double auction.
6. Install a LaTeX toolchain and make manuscript compilation part of clean-room CI.
7. Obtain statistics, market-microstructure, and reproducibility reviews; populate the response
   table with real dated reviewer evidence.

## Authorized execution sequence

```bash
uv run flock validate
uv run flock doctor
uv run flock compile-study configs/studies/paper-core.yaml \
  --output results/paper-core/plan.json
uv run flock validate-study results/paper-core/plan.json
uv run flock estimate --plan results/paper-core/plan.json --stage canary
uv run flock doctor --live
```

Stop if any command fails. After the P0 materializer/mock-matrix work is complete, authorize only
the `$50` canary. Re-estimate before the pilot and keep cumulative paid pilot authorization below
`$5,200`. Confirmatory calls remain unauthorized until all pilot, power, preregistration, data,
failure, drift, throughput, and cost gates pass.

## Defensible current conclusion

The repository now prevents several ways of manufacturing a paper result from invalid evidence and
can reproducibly exercise the offline path. It is not yet a key-only confirmatory runner. The next
scientifically meaningful milestone is a complete compiled mock matrix followed by a bounded paid
canary—not a broad H1–H12 execution or a manuscript claim.
