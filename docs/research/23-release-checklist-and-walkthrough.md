# 23 — Release Checklist and Walkthrough

**Status: BLOCKED; this is a release plan, not evidence of a completed study. Snapshot date:
2026-07-17.** Checkboxes remain unchecked until their named artifacts exist and pass verification.
Do not infer completion from implemented scaffolding or passing mock tests.

## Scientific release gate

- [ ] The first-paper claim, population boundary, hypotheses, estimands, independent units, SESOIs,
  equivalence/noninferiority margins, missingness policy, multiplicity family, and stopping rules
  are frozen before confirmatory calls.
- [ ] Exact dated model releases and lineage are resolved; no mutable alias or preview endpoint is
  silently treated as an immutable checkpoint.
- [ ] Every required dataset has a lawful license/use record, immutable raw or restricted snapshot,
  complete bundle hash, transformation lineage, timezone/corporate-action handling, and leakage
  report.
- [ ] Outcome-blind nested power simulations justify the independent trajectory/window and H5
  market-replica counts under provider heterogeneity, missingness, dependence, and multiplicity.
- [ ] ODD/STRESS documentation and market validation support the limited simulator language.
- [ ] The preregistration is immutable and records the OSF identifier, frozen commit SHA, and
  `prereg-v1` tag created before the first confirmatory call.
- [ ] Canary and pilot stop/go decisions, paid usage, failure rates, drift, throughput, blinded
  nuisance estimates, and costs are preserved—including unfavorable outcomes.
- [ ] Confirmatory bundles contain complete blocks only, pass grounding/provenance/statistical
  verification, and cannot inflate `n` with nested or duplicate observations.
- [ ] Conclusions use only `practically supported`, `statistically detectable but small`,
  `equivalent/noninferior`, or `inconclusive`, as warranted by frozen rules.

## Software and artifact gate

- [ ] `pytest`, Ruff, and the configured Python type-checker pass from a clean environment at the
  tagged commit; versions and complete logs are in the release manifest.
- [ ] Every internally feasible core protocol completes under mocks, and mock status is visible in
  every derived artifact.
- [ ] Interruption/resume, atomic cache, spend cap, stale price, provider retry, conservation,
  leakage, duplicate-path, incomplete-block, and negative paper-gate tests pass.
- [ ] One master command regenerates every paper number, macro, table, figure, and claim record from
  hashed inputs without network access except where explicitly documented.
- [ ] `claims.json` links every substantive sentence to an estimand, effect, interval, adjusted
  inference, source rows, figure/table, limitation, and verification status.
- [ ] A clean-room reproducer obtains the tagged code, follows only public instructions, verifies
  checksums, rebuilds the eligible mock study and paper, and records discrepancies.
- [ ] Restricted data/model dependencies are labeled; the public artifact does not imply that an
  unavailable input is reproducible merely because its hash is known.
- [ ] API keys, credentials, personal information, licensed raw data, and private provider content
  are absent from the public bundle and git history.

## Paper and accountability gate

- [ ] The manuscript contains methods, results, robustness, conclusion, limitations,
  ethics/broader impacts, reproducibility, data/code availability, funding/conflicts, bibliography,
  and an accurate LLM-use disclosure.
- [ ] Figure titles, captions, and legends distinguish mock, pilot, confirmatory, exploratory, and
  simulator-only evidence and show independent units where relevant.
- [ ] Lewis has verified and signed
  [19 — Authorship and Tool Use](19-authorship-and-tool-use.md), can explain the design and code
  relied on for claims, and has not presented generated prose as understanding.
- [ ] The dated [20 — Research Log](20-research-log.md) includes failures, amendments, null or
  contradictory outcomes, and stop/go decisions without rewriting earlier entries.
- [ ] The final [21 — Mistake Case Study](21-mistake-case-study.md) is generated from real hashed
  pilot artifacts and clearly labels the invalid agent-level analysis as diagnostic.
- [ ] Genuine independent statistics, market-microstructure, and reproducibility reviews are
  recorded in [22 — Independent Review and Response](22-independent-review-response.md); no
  unresolved P0/P1 finding remains.
- [ ] README and portfolio descriptions say exactly what was executed and reproduced, not what the
  broader H1–H12 agenda proposes.
- [ ] The release is immutable, checksummed, versioned, licensed, archived, and linked to the exact
  source commit without rewriting prior history.

## Required release manifest fields

The final manifest records the release ID/date, source and preregistration commits, OSF identifier,
code/environment lock hashes, data-bundle hashes and permissions, exact model/provider revisions,
SDK/API versions, pricing snapshot, prompts/profiles, assignment and dependence maps, random seeds,
independent-unit counts, expected/realized calls and costs, failures/exclusions, verification
results, paper artifact hashes, disclosure/review status, and the clean-room reproduction record.

Any missing required field is either a release blocker or an explicit `not applicable` with a
machine-checkable reason. Blank, inferred, and `unknown` values cannot silently pass.

## Three-to-five-minute walkthrough plan

The walkthrough is recorded only after a real verified bundle exists. It uses one preregistered
unit selected by a frozen, non-outcome-based rule—not the most dramatic example—and keeps a visible
`pilot`, `confirmatory`, `mock`, or `simulator-only` label throughout.

| Time | Screen | Required explanation and trace |
|---|---|---|
| 0:00–0:30 | Claim card and topology | State the narrow question, four `technology × ecology` cells, highest independent unit, sampled-domain boundary, and non-claims |
| 0:30–1:05 | One observation | Show timestamped market inputs, news/evidence IDs, portfolio/constraints, data-bundle hash, and why no future information is visible |
| 1:05–1:45 | Prompt to decision | Show rendered prompt/model revision and hashes, structured response, intended orders, parse/grounding states, token/cost record, and any retry without exposing secrets |
| 1:45–2:20 | Decision to fill | Show clipping versus voluntary hold, reservation, order-book/tape event, fill or no-fill, fee, cash/inventory conservation, and simulator-only boundary where applicable |
| 2:20–3:05 | Fill to block effect | Aggregate the nested steps/agents into the frozen unit effect; show why repeated calls do not increase `n` and display all independent blocks |
| 3:05–3:45 | Effect to claim | Trace effect, interval, SESOI, multiplicity, sensitivity, and limitation through `claims.json` to the exact figure and sentence |
| 3:45–4:30 | Reproduction and mistakes | Run or show the master reproduction command, verification result and hashes; summarize the pseudoreplication/baseline-confound correction and unresolved weaknesses |

The narration should be understandable without source-code fluency. A viewer must be able to pause
on every screen and identify the relevant release path or manifest key. Do not use an animation,
edited console output, or a rehearsed example to hide failures or manual steps.

## Independent handoff test

Give an uninvolved reader only the public release location and ask them to:

1. identify the strongest supported claim and three forbidden interpretations;
2. report the top-level independent `n` and explain why agent/call counts differ;
3. reproduce the mock paper and verify the real paid-run manifest without author intervention;
4. trace one paper sentence backward to raw/allowed input provenance; and
5. explain Lewis's contribution, AI assistance, the major corrected mistakes, and unresolved risks.

Record their screen capture or terminal log, environment, elapsed time, questions, and every
discrepancy. Failure of any task blocks the “independently reproducible” claim until corrected and
retested.

## Current blocker summary

At this snapshot, there is no frozen preregistration, verified paid study, completed external
review, clean-room reproduction, or release-derived mistake comparison. Exact live endpoint and
dataset readiness must also pass their gates. Consequently, this package may support planning and
show methodological revision, but it cannot yet support a paper-results or completed-research
claim.
