# Post-build repository polish and reduction audit

**Prepared:** 2026-07-23
**Status:** action plan; cleanup is gated on the build criteria below
**Execution model:** lead integrator plus bounded subagent teams

## Purpose

Make the repository concise, professional, reproducible, and admissions-ready without deleting
scientific history, changing estimands, weakening verification, or presenting mock output as
evidence. This audit records recommended actions; it does not certify that the proposed study has
run.

## Cleanup gate

Do not begin broad consolidation or dead-code removal until all applicable items are true:

1. H1/H3/H4 assignments can be resolved and executed with mock substitutes.
2. H2 quarter-to-quarter holdings changes, canonical period-specific LSV, Sias components,
   activity matching, and provenance contracts are implemented and tested.
3. `flock aggregate-study` deterministically converts verified raw runs into crossed aggregates
   and rejects missing, duplicate, incomplete, mixed mock/real, or lineage-invalid inputs.
4. H5 either passes its persistent-book, liquidity, capital, shorting, conservation,
   reconstruction, calibration, ODD, and STRESS gates or remains disabled and simulator-only.
5. The complete proposed-study mock matrix reaches one terminal state per assignment and
   reproduces byte-identically from an empty output directory.
6. Tests, Ruff, and Pyright pass. Manuscript compilation must also pass once a LaTeX engine is
   available.

If a gate remains open, cleanup is limited to accurate status text, generated-artifact hygiene,
confirmed duplicate files, and recovery-safe changes.

### Gate snapshot — 2026-07-23

- Gates 1 and 3 pass for the offline H1/H3/H4 path.
- Gate 5 passes for the current 197-assignment materialization: 149 assignments completed and
  verified, 48 H5 assignments terminated as explicitly blocked, and the 144-run crossed analysis
  reproduced byte-identically. All generated artifacts remain ignored and non-paper-eligible.
- Gate 2 remains open because H2 is tested at the library level but lacks acquired 13F data and a
  complete harmonized artifact/CLI path.
- Gate 4 remains open because H5 is disabled pending calibrated background agents, agent-facing
  cancellation, six-cell capital-share execution, restart/hash stress, benchmark calibration, and
  ODD/STRESS release gates.
- Gate 6 passes for 182 tests, Ruff, and Pyright; manuscript compilation still awaits a
  LaTeX-capable environment.

Therefore broad file consolidation, speculative script deletion, and future-work archiving remain
deferred. Only evidence-safe cleanup already proven by tests may proceed.

## Subagent team structure

Each team works on an isolated branch or worktree, owns at most five files per phase, and returns a
structured report before the lead integrates anything.

| Team | Scope | Required report |
|---|---|---|
| Repository curator | Duplicate, obsolete, generated, dead, or superseded files; imports, CLI, CI, tests, and links | `keep`, `merge`, `archive`, or `delete` disposition with replacement, recovery point, and verification |
| Literature/provenance | Search log, BibTeX, errata/corrections, claim map, idea genealogy | Exact source, query, date, inclusion decision, citation key, and last verification |
| H2/statistics | Holdings-change harmonization, LSV/Sias, activity matching, clustering, sensitivity | Implemented contract, remaining data gates, tests, and forbidden interpretations |
| H5/markets | Exchange mechanics, calibration, invariants, ODD/STRESS | Pass/fail gate per mechanism and whether H5 must remain disabled |
| Execution/reproducibility | Assignment resolution, mock matrix, aggregation, release reproduction | Terminal-state matrix, hashes, failures, byte-identity result, and external-action blockers |

Agents may inspect, test, and propose changes. They may not push, spend money, register a study,
broaden a claim, delete ignored runs, or count themselves as independent human reviewers.

## Authoritative information architecture

Keep these as sources of truth:

- `README.md`: concise purpose, evidence status, quickstart, and principal gates.
- `configs/research-program.yaml`: hypothesis and experiment scope.
- `configs/studies/paper-core.yaml`: exact proposed-study design.
- `docs/research/01`–`07`: question, design, metrics, datasets, roadmap, preregistration, literature.
- `docs/research/18`: dated cost/execution view; budget YAML remains controlling.
- `docs/research/19` and `20`: signed authorship/tool disclosure and append-only research history.
- `docs/research/22`–`24`: real review responses, release checklist, and H5 ODD/STRESS gate.
- `docs/research/25`: authoritative implementation status until replaced by generated status.
- `paper/main.tex` and `paper/references.bib`: working manuscript and sole bibliography.

After the cleanup gate passes:

- Merge `09` and `10` into `02`; merge `12` into `03`.
- Merge first-study material from `13` and `17` into `04`.
- Merge the neutral, dated substance of `21` into the append-only research log.
- Move `11`, `14`–`16`, `26`, and future-product material from `17` into a clearly nonauthoritative
  future-work archive.
- Extract any unique data dictionary from `08`, then delete `08`, which is explicitly
  noncanonical and overlaps the corrected design.
- Absorb `25` into `23` only after an automatically generated status artifact replaces it.

## Repository reduction procedure

For every candidate file, script, dependency, export, alias, schema, fixture, or compatibility
path:

1. Search direct calls, type references, string literals, dynamic imports, re-exports, CLI
   registration, configs, tests, CI, and documentation separately.
2. Record a disposition: `keep`, `merge`, `archive`, or `delete`.
3. Name the canonical replacement and the Git recovery commit.
4. Change no more than five files in a phase.
5. Run focused tests, then the full suite, Ruff, and Pyright.
6. Report file, line, word, and dependency reductions without treating size as research quality.

Generated outputs stay out of source control during development. Git tracks code, schemas,
configuration, the input registry, preregistration, provenance, hashes, and reproduction
instructions. Raw/intermediate runs, caches, provider responses, reports, figures, tables, macros,
PDFs, and licensed payloads remain ignored. Verified public releases should store raw evidence in
a versioned research archive and commit only its URI, hashes, manifest, and reproduction contract.

## Evidence ladder

Every status claim uses one of these labels:

1. **Planned** — documented but not implemented.
2. **Implemented** — code path exists.
3. **Tested** — automated verification passes.
4. **Executed** — a named assignment produced terminal artifacts.
5. **Independently verified** — a real reviewer or separate clean-room rerun checked it.
6. **Paper-eligible** — frozen preregistration and release gates permit the artifact to support a
   manuscript claim.

Mock runs may reach **executed** for software validation but never **paper-eligible** evidence
about frontier LLM behavior.

## Professional and admissions presentation

Use the documented correction as the narrative:

> Broad prototype → adversarial audit → pseudoreplication and ecology-control confound identified
> → matched design narrowed → mock system verified → preregistered real pilot.

Git establishes that the initial design was committed on July 4, 2026; it does not establish
priority over earlier publications or prove pre-literature independent conception. If true, the
author may describe the motivating intuition as independently recalled, while explicitly making
no broad novelty claim. Pivots are presented as dated methodological corrections, not concealed.

Admissions-facing deliverables should be a concise README status panel, a three-to-five-minute
walkthrough, one architecture/experiment diagram, the before/after design correction, and—only
after execution—a one-page pilot brief and reproducible release link. Avoid “first,”
“unprecedented,” “completed research,” “collusion,” mock-as-empirical language, and line/test-count
signaling.

## Completion report

Before any push, the lead presents:

- ordered local commits and their purpose;
- changed/deleted files, canonical replacements, and recovery points;
- before/after file, line, word, and dependency counts;
- full test, Ruff, Pyright, link, citation, BibTeX, manuscript, schema, replay, exchange, H2,
  aggregation, H5, mock-matrix, reproduction, secret, and tracked-artifact results;
- exact mock, paid, preregistration, review, and paper-eligibility status;
- unresolved blockers and every action still requiring explicit approval.
