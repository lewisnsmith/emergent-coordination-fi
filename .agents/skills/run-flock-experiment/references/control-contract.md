# experiment control contract

This is the compact operator contract for prompt-driven control. It routes to authoritative
materials and records safety boundaries; it does not redefine a hypothesis, estimand, method, or
release rule.

## authority order

Resolve disagreement in this order and stop when reconciliation would change science:

1. frozen registration and append-only amendments, once they exist;
2. `docs/research/research-scope-outcomes-and-evidence.md` for scope and claim boundaries;
3. `docs/research/experimental-methods-and-statistical-analysis.md` for design and inference;
4. `docs/research/data-provenance-artifacts-and-release.md` for data and release gates;
5. `docs/research/local-first-execution-costs-and-risk-roadmap.md` for sequencing and cost;
6. `docs/research/research-decisions-and-execution-log.md` for dated decisions;
7. `docs/research/preregistration.md` while it remains a draft;
8. checked-in configs, compiled plans, materializations, terminal ledgers, and manifests for what
   the implementation will actually do; and
9. the five living external-evidence audit artifacts for the current literature snapshot.

`CLAUDE.md` governs repository operation. When prose and executable contracts disagree, do not
choose a convenient winner: report the drift and block the affected tier.

## two-axis controller

Every request resolves to one roadmap phase and one authorization tier.

| program phase | normal deliverable | additional gate |
|---|---|---|
| audit external evidence | versioned evidence decision audit | source/version, artifact, license, comparability, and claim-use review |
| benchmark the workstation | fixed workload and hardware manifest | pinned model/runtime, telemetry, thermal and storage limits |
| freeze the scoring key | executable tasks and frozen intermediate values | deterministic oracle, task lineage, rights, and held-out split |
| run local precision and fidelity screen | paired checkpoint/precision results | exact hashes, quantizer/runtime parity, contamination controls |
| run frontier behavioral bridge | sampled, cached frontier comparison | local finalist gate, current capability/pricing, live authorization |
| run mechanistic funnel | frozen-site interventions | behavioral gate, causal controls, activation retention policy |
| run local replay and simulated-market discovery | verified signatures | complete blocks, independent units, held-out and classical controls |
| test transport in real markets | bounded transport assessment | lawful panel, domain-shift plan, no causal exposure claim |
| run prospective paper trading | paper-only ledger | frozen strategy, paper account, side-effect caps, no live money |
| build the release | clean reproducible bundle | preregistration, claims, checksums, independent review, publish approval |

| tier | allowed effect | default disposition |
|---|---|---|
| `plan` | read, research, calculate, and prepare without execution | proceed through read-only gates |
| `mock` | local deterministic rehearsal and verification | highest implemented execution tier |
| `canary` | tiny provider or externally consequential probe | blocked until live controller hardening and scoped approval |
| `pilot` | nuisance/failure estimation without confirmatory inspection | blocked until verified canary and new authorization |
| `confirmatory` | frozen confirmatory collection | blocked until preregistration and all prior gates pass |
| `release` | build offline, then register/publish separately | offline build allowed; every remote write needs approval |

Program phase does not imply tier. For example, the frontier bridge can be planned at `plan`,
materialized with mock mappings at `mock`, or executed only at an authorized live tier.

Roadmap order is not completion state. No durable phase-completion ledger exists yet, so an
unqualified “next phase” remains at `plan` until a target is supplied or terminal gate artifacts
prove the current and completed phases. File existence and narrative status are not sufficient.
The workstation benchmark currently calls for fresh scoring-key tasks before the later scoring-key
freeze phase; resolve whether those are explicitly non-confirmatory calibration tasks before
running it.

## access and approval matrix

| resource or effect | minimum access | approval boundary |
|---|---|---|
| repo inspection, compilation, costing, verification | read-only workspace | none |
| local configs, plans, mock results, analysis | workspace write | normal scoped implementation or experiment request |
| public evidence refresh | public web read | allowed when requested; no contact or remote write |
| datasets and regulatory filings | exact network hosts and terms | approve acquisition scope, rights, volume, and output root |
| provider metadata | exact endpoint plus one injected key | approve live metadata probe; zero generation |
| provider generation | exact endpoint/model plus one injected key | hash-bound stage authorization and hard caps |
| local GPU/model roots | exact local paths and telemetry | approve substantial compute; purchase/rental is separate |
| human-subject work | ethics record, consent flow, restricted storage | explicit approval after applicable review; no autonomous contact |
| real-market transport | lawful data credentials only | never infer exposure or causation from resemblance |
| paper trading | paper-only endpoint and credential | explicit write approval and caps; never accept live-money access |
| OSF, git tag, GitHub, or public release | narrow remote write | separate registration/publish approval after offline verification |

Keep the default workspace-write sandbox and network off. Allowlist only hosts actually required by
the chosen builder or provider. Current builders may require Polymarket, Kalshi, SEC, or resolved
market-data hosts; verify exact endpoints before access rather than granting wildcards.

## authorization packet

The operator may prepare but never self-approve a live record. Bind all of these fields:

- authorization ID, issuer, issue time, expiry, program phase, tier, study ID, and stage ID;
- source SHA and dirty-state disposition;
- study-plan, materialization, dataset, prompt, scoring-key, model, and environment hashes;
- exact provider, endpoint, model revision, deployment class, and supported parameters;
- maximum calls, input/output/reasoning tokens, retries, dollars, compute, storage, and wall time;
- permitted output root and whether acquisition, registration, publication, or paper-order side
  effects are allowed;
- the verified prior-gate ledger and stop conditions; and
- `live_money_trading=false`.

Any mismatch or expiry invalidates the record before a side effect occurs. Confirmatory authority
also requires the frozen commit, `prereg-v1` tag, and OSF registration identifier. A push or public
release is never implied by execution authority.

## current baseline and hard blockers

Re-run the status script before every action. The 2026-08-13 baseline is safe through mock only:

- `flock validate` reports a valid scaffold but `execution_ready=false`; required real datasets,
  H2, H6, H7, H9, and H10 inputs/runners remain blocked.
- the preregistration is draft with no frozen commit, `prereg-v1` tag, or OSF record; H1/H3/H4
  rules remain unfrozen.
- `execute-materialized` rejects non-mock assignments, while direct `flock run` lacks a durable
  stage authorization and its runtime budget is not cumulative across processes/retries.
- the compiled study's canary is within its hard cap, but current high-envelope pilot and
  confirmatory estimates exceed their stage caps.
- the methods require all 80 MPHIQ Hamming-one edges, while the study config supplies one 31-edge
  Gray chain; H1 inference and H4 multiplicity also need reconciliation.
- the compiled study mixes separate H5 outputs into first-paper outputs, and H5 lacks its required
  capital allocation, ODD/STRESS, and verification path.
- provider adapters/manifests/cache do not yet capture enough resolved model, capability,
  finish/safety, SDK/API, endpoint, and request provenance; provider parameters need current
  compatibility checks before any canary.
- pricing is stale beyond the current freshness threshold, the registry lacks complete rights and
  raw-retrieval provenance fields, and iCloud has dataless ignored artifacts that make broad
  environment operations unsafe.
- the evidence audit has no artifact approved for collection reduction. H6 human work, H7 adoption,
  H10 exposure attribution, prospective paper trading, and the complete release exporter retain
  external or implementation gates.
- there is no machine-readable phase-completion ledger, so the controller cannot safely infer the
  next roadmap phase from prose or artifact presence.

These are stop conditions, not a backlog the agent may silently waive.

## safe command routes

Run from the repository root with `UV_NO_EDITABLE=1` and the configured `.venv.nosync` environment.

```bash
.venv.nosync/bin/python .agents/skills/run-flock-experiment/scripts/status.py --repo .
.venv.nosync/bin/flock validate
.venv.nosync/bin/flock doctor
.venv.nosync/bin/flock compile-study configs/studies/paper-core.yaml --output /private/tmp/flock-study-plan.json
.venv.nosync/bin/flock validate-study /private/tmp/flock-study-plan.json
.venv.nosync/bin/flock estimate --plan /private/tmp/flock-study-plan.json --stage canary
```

For an offline rehearsal, materialize with an explicit mock resolution, execute only the resulting
mock bundle, then verify the terminal ledger, assignments, study bundle, and paper rejection gate.
Never use direct frontier configs as a substitute for this route.

## prompt interface

These prompts should be sufficient:

```text
use $run-flock-experiment and show current status
```

```text
plan the local precision screen at mock tier; use read-only research agents and do not execute
```

```text
prepare the frontier bridge canary with a $10 and 50-call ceiling; stop before provider access
```

```text
run the offline rehearsal from materialization <hash>; verify every reused assignment
```

```text
resume ledger <path>; reconcile incomplete attempts before proposing a retry
```

```text
build a release candidate from bundle <path>; reproduce offline but do not publish or push
```

After the live controller is implemented and tested, the explicit form is:

```text
run authorized frontier bridge canary <authorization-id> from materialization <hash>; stop on drift, the first failed gate, or any cap
```

## primary operating references

Use the living evidence audit for claim-level sources. For control decisions, prefer these primary
standards and provider records:

- [OSF registrations](https://help.osf.io/article/330-welcome-to-registrations) for immutable
  registration and transparent updates;
- [NIST experiment design](https://www.itl.nist.gov/div898/handbook/pmd/section3/pmd33.htm) for
  randomization, replication, and blocking;
- [W3C PROV-O](https://www.w3.org/TR/prov-o/) and
  [RO-Crate 1.2](https://www.researchobject.org/ro-crate/specification/1.2/introduction.html) for
  execution and artifact provenance;
- [ODD](https://www.jasss.org/23/2/7.html) and
  [STRESS](https://www.equator-network.org/reporting-guidelines/strengthening-the-reporting-of-empirical-simulation-studies-introducing-the-stress-guidelines/)
  for simulation description and experiment reporting;
- [HHS 45 CFR 46](https://www.hhs.gov/ohrp/regulations-and-policy/regulations/45-cfr-46/) and
  [SPDX license expressions](https://spdx.github.io/spdx-spec/v3.0.1/annexes/spdx-license-expressions/)
  for human-subject and rights gates; and
- current official provider compatibility/schema records for
  [OpenAI](https://platform.openai.com/docs/api-reference/backward-compatibility),
  [Anthropic](https://platform.claude.com/docs/en/about-claude/model-deprecations), and
  [Google](https://ai.google.dev/api/generate-content?hl=en) before any live canary.

## completion and recovery evidence

Each control report records phase/tier, source and artifact hashes, gate evidence, actual/reserved
usage, verification commands, blockers, next safe action, and next approval. Preserve `.incomplete`
artifacts and caches. Reuse only verified manifests; a changed input produces a new plan and ledger.
Build analysis and release candidates offline in new hash-addressed locations, and require clean
reproduction before external publication.
