# 19 — Authorship and Tool Use

**Status: DRAFT for Lewis to verify before any public release. Last updated: 2026-07-17.** This
statement describes the current working process. It is not an authorship certification, and it
must be updated from the final release manifest, research log, git history, and human-review record.

## Responsibility and ownership

Lewis initiated and directs the Flock research project. He is responsible for the research
question ultimately pursued, the scientific claims retained, the decision to run or stop paid
experiments, interpretation of the evidence, and every statement submitted under his name. AI
assistance can propose, critique, implement, and explain work; it cannot accept scholarly
responsibility, provide research consent, serve as an independent reviewer, or be listed as an
author.

The repository is evidence of work performed, not by itself proof of who supplied an idea or
understood a change. Before release, Lewis must verify the following contribution record and add
dated evidence where the present wording is incomplete:

| Area | Lewis's accountable role | AI/tool assistance to disclose | Release evidence |
|---|---|---|---|
| Problem and scope | Chose to study convergence among trading agents and approved the narrowed H1/H3/H4 paper with H5 as a simulator-only extension | Critiqued novelty, causal language, and breadth; proposed narrower formulations | Dated research log and approved preregistration |
| Experimental design | Owns the accepted estimands, controls, independent units, SESOIs, stopping rules, and claim boundary | Stress-tested the original design and proposed the matched `technology × ecology` redesign | Preregistration, design review, and commit history |
| Software | Must be able to explain and verify the code relied on for any claim | Generated and reviewed portions of implementation, tests, documentation, and analysis scaffolding | Git history, test logs, code review notes, and release manifest |
| Data and model calls | Authorizes lawful data use and paid calls; verifies that keys, licenses, model revisions, and invoices reconcile | Automates preflight, acquisition, execution, logging, and provenance checks when explicitly authorized | Dataset manifests, provider manifests, and invoices |
| Statistical analysis | Chooses the frozen analysis after qualified feedback and is responsible for interpretation | Identified pseudoreplication risk; helped implement independent-block inference and metric tests | Statistical verification bundle and external statistics review |
| Writing | Approves every claim, limitation, citation, figure, and conclusion | Drafts, edits, summarizes, formats, and proposes visualizations | Claim registry, manuscript history, and final human sign-off |

“Owns” and “responsible” mean accountable for checking the work, not a claim that Lewis performed
every keystroke unaided. Any row that Lewis cannot explain or substantiate must be revised or
removed before the project is presented as his work.

## Current AI-use disclosure

AI systems have assisted with repository inspection, research-design criticism, prior-art search,
cost estimation, implementation, testing, documentation, and manuscript planning. In particular,
AI-assisted review surfaced two material design problems: agent/call-level pseudoreplication and a
classical-control comparison that confounded technology with the diversity of the supplied
ecology. AI assistance also helped narrow the novelty claim from first evidence of convergence to
a matched-control causal decomposition.

This is a process disclosure, not evidence that the identified problems are fully solved. The
exact providers, model/release identifiers, dates, material prompts or task descriptions, and
accepted code/document changes must be exported from the final release record. If a provider does
not expose an immutable model revision, that limitation must be named rather than replaced with a
more precise-looking alias.

Before submission, replace this paragraph with the venue-appropriate disclosure and an appendix
table containing, at minimum:

| Date range | System and exact version | Purpose | Inputs exposed | Material output used | Human verification |
|---|---|---|---|---|---|
| *To be completed from actual records* | — | — | — | — | — |

Do not publish API keys, credentials, private provider responses, licensed raw data, personal
information, or security-sensitive environment details in order to demonstrate transparency.
Where full prompts or outputs cannot be released, publish hashes, a redacted description, and the
reason for restriction.

## Verification standard

Lewis's final sign-off should attest that he:

- can explain the study design, major implementation choices, statistical estimands, and known
  failure modes without relying on generated prose;
- reproduced the release from the tagged commit or observed an independent clean-room
  reproduction;
- manually checked every substantive claim against `claims.json` and its source artifact;
- checked every citation against the cited source and did not treat an AI summary as a source;
- obtained and answered genuine human review in statistics, market microstructure, and
  reproducibility, using [22 — Independent Review and Response](22-independent-review-response.md);
- preserved unsuccessful, null, and contradictory outcomes under the frozen reporting rules; and
- described the work proportionally: a completed study only after a real verified study exists,
  otherwise a scaffold, pilot, or proposed research program.

## Explicit non-claims at this stage

As of 2026-07-17, this document does **not** claim that a paid study has run, a preregistration has
been frozen, a human expert has reviewed the project, a result has replicated, or a paper has been
accepted. Passing mock tests demonstrates software behavior under synthetic fixtures, not an
empirical finding about frontier models or markets. Current milestones and blockers are recorded
in [20 — Research Log](20-research-log.md) and [23 — Release Checklist and Walkthrough](23-release-checklist-and-walkthrough.md).

