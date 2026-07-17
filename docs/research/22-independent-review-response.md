# 22 — Independent Review and Response

**Status: EMPTY REVIEW TEMPLATE; no independent review has yet been recorded here. Last updated:
2026-07-17.** A completed table requires actual reviewer feedback. AI review, repository tests, and
Lewis's own inspection do not count as independent human review.

## Reviewer independence and consent

Recruit at least one qualified reader for each of three lenses: statistics, market microstructure,
and reproducibility. A reviewer may cover more than one lens only if their relevant qualifications
are stated. Before publishing a name, affiliation, quotation, or full review, obtain the reviewer's
permission. An anonymous review may state qualifications at a non-identifying level.

Record conflicts, prior involvement, compensation, access to outcomes, and whether the reviewer
inspected code/data or only the manuscript. A reviewer who designed or implemented the relevant
component can provide useful feedback but is not independent for that component.

| Review ID | Lens | Reviewer/anonymous qualification | Independence and conflicts | Materials/version | Outcomes blinded? | Date received | Permission to publish |
|---|---|---|---|---|---|---|---|
| *No reviews received* | — | — | — | — | — | — | — |

## Common review packet

Give every reviewer a versioned packet containing the paper claim and non-claims, preregistration
status, study plan, independent-unit diagram, data/model provenance, analysis code, verification
status, known failures, and reproduction instructions. Record the exact commit and release ID.
Never send only successful figures. Provide null, failed, excluded, and contradictory artifacts
under the frozen missingness policy.

Ask all reviewers:

1. What is the strongest claim the evidence supports, and which current sentence exceeds it?
2. What dependence, confound, leakage, selection, or implementation failure could still generate
   the result?
3. Which assumption is least defensible, and what falsification or sensitivity would change your
   view?
4. Is any reported uncertainty, sample size, causal label, or visual encoding misleading?
5. Could an uninvolved researcher reproduce the claim from the release packet alone?
6. What must be fixed before public release, and what can remain a clearly disclosed limitation?

## Lens-specific prompts

### Statistics

- Does the top-level unit and dependence-cluster map match the data-generating process?
- Do family weighting, paired construction, missingness, dyadic aggregation, and multiplicity
  reproduce the frozen estimand?
- Are the inference method, SESOI, equivalence/noninferiority margins, power simulation, and
  attainable p-values justified at the available number of independent units?
- Can any agent, pair, call, step, paraphrase, retry, seed, duplicate path, or overlapping window
  still increase confirmatory `n`?

### Market microstructure

- Do cash, inventory, reservations, fees, order priority, partial fills, self-trade prevention, and
  order lifetimes conserve and behave as documented?
- Are background liquidity, arrival rules, endowments, tick size, order types, and no-trade states
  sufficiently realistic for the limited H5 claim?
- Do spread, depth, volume, volatility, tails, fill rate, and impact diagnostics support the use of
  the chosen simulator language?
- Is every causal conclusion explicitly bounded to the validated simulator?

### Reproducibility

- Does a clean environment reproduce all eligible mock artifacts from the tagged commit and hashed
  inputs using one documented entry point?
- Are model revisions, SDK/API versions, prompts, datasets, pricing, environment, randomization,
  raw-response hashes, failures, and transformations traceable?
- Do restricted inputs have lawful access instructions and immutable private snapshots without
  being falsely represented as public?
- Can a failed verification, stale price, mutable alias, dataless input, or incomplete block reach
  the paper?

## Findings and response matrix

Use one row per atomic finding. Preserve the original wording or attach its immutable hash. Severity
is the reviewer's assessment; disposition is Lewis's decision. Declining a suggestion requires a
technical rationale and, where appropriate, a narrower claim.

| Finding ID | Review ID | Severity | Verbatim finding or attachment | Response | Change/evidence | Disposition | Residual limitation | Reviewer recheck |
|---|---|---|---|---|---|---|---|---|
| *No findings recorded* | — | — | — | — | — | — | — | — |

Allowed dispositions are `accepted`, `accepted with modification`, `declined with rationale`, and
`release-blocking`. Do not delete resolved findings. If a release-blocking finding is unresolved,
the final release status remains blocked.

## Completion record

This section remains blank until real reviews exist:

- Statistics review completed: **no**
- Market-microstructure review completed: **no**
- Reproducibility review completed: **no**
- All P0/P1 findings resolved and rechecked: **no**
- Review packet commit/release ID: **not available**
- Public response-table hash: **not available**

The release owner verifies these facts in
[23 — Release Checklist and Walkthrough](23-release-checklist-and-walkthrough.md).
