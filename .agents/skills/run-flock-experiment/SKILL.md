---
name: run-flock-experiment
description: Control, resume, inspect, rehearse, verify, analyze, and prepare releases for the flock research program through phase and authorization gates. Use when a user asks for experiment status or readiness, the next safe phase, study planning or materialization, mock execution, canary/pilot/confirmatory preparation or execution, recovery, evidence refresh, preregistration, analysis, or release. Do not use for an isolated code explanation or ordinary bug fix.
---

# run flock experiment

Operate the experiment from short prompts without replacing frozen scientific contracts with agent
judgment. Resolve every request on two axes: one program phase and one authorization tier.

## enforce the current ceiling

Treat `mock` as the highest implemented execution tier. Planning, public research, local
preparation, mock execution, verification, and offline release checks can proceed through their
normal gates. Mark provider-backed `canary`, `pilot`, and `confirmatory` execution
`blocked_implementation` until all of these exist and pass tests:

- a real materialized executor that requires a hash-bound authorization record;
- a persistent cumulative spend ledger that reconciles incomplete and retried attempts;
- provider capability and parameter checks plus response-resolved provenance; and
- cache isolation by execution fingerprint and provider revision.

Never route around this ceiling with `flock run`. A broad instruction such as “run the experiment”
does not authorize provider calls, spending, purchases, participant contact, paper orders,
registration, publication, pushing, or any other remote write.

## start every control turn

1. Read the repository `CLAUDE.md` and
   [control contract](references/control-contract.md). Read only the canonical manuals relevant to
   the requested phase.
2. From the repository root, run:

   ```bash
   .venv.nosync/bin/python .agents/skills/run-flock-experiment/scripts/status.py --repo .
   ```

3. Inspect the current branch, source SHA, and dirty paths. Preserve unrelated work. Never read an
   `.env` file or print credential values.
4. Name the requested program phase and authorization tier. If either is ambiguous, choose the
   lowest consequential interpretation and state it.
5. Create an ephemeral task plan with: inputs and hashes, gates, approval boundary, action,
   verification, recovery, and stop condition. Do not create another durable roadmap.

The roadmap order is not a completion ledger. If `phase_state.current_phase` is `null` and the user
asks for “next,” do not guess from file existence or narrative status. Remain at `plan`, report that
the phase is unrecorded, and request or prepare the evidence needed to select a target. Never start
an execution tier from an inferred phase.

## evaluate gates before acting

Fail closed at the first missing gate. A manual, external, or human-only check is blocked until its
evidence is supplied; never infer it from prose or chat memory.

- **scope:** hypothesis, claim boundary, output track, estimand, and independent unit are named.
- **repository:** source SHA and dirty-state disposition are recorded.
- **inputs:** paths, content hashes, lineage, rights, splits, and privacy constraints are present.
- **design:** the current study compiles; plan and materialization hashes match the request.
- **implementation:** the exact runner, verifier, and recovery path exist for the tier.
- **budget:** pricing is current and calls, tokens, retries, compute, storage, and high-cost envelope
  fit a scoped cap.
- **authorization:** consequential action matches a valid record or receives specific user approval.
- **verification:** terminal ledgers and complete blocks reconcile; exclusions are not silently
  introduced.
- **release:** preregistration, claims, reproduction, provenance, review, and disclosure gates pass.

`scaffold_ok=true` never means `execution_ready=true`. A failed gate stops the phase; it never
silently shrinks the design, changes an estimand, or deletes a hypothesis.

## act through existing deterministic commands

Prefer the existing `flock` CLI and checked-in contracts over bespoke shell logic. Safe operations
include `validate`, non-live `doctor`, `compile-study`, `validate-study`, `materialize-study`, cost
estimation, mock `execute-materialized`, run/study verification, aggregation, harmonization,
analysis, and reproduction. Use a hash-addressed output in `results/` for experiment artifacts and
`/private/tmp` for disposable preflight artifacts.

For mock execution, require an explicitly resolved mock materialization, execute that bundle, and
verify every completed or reused assignment. A mock or smoke artifact can validate plumbing only;
never use it as paper evidence.

The `--live` doctor flag performs metadata probes, so it still needs explicit network approval and
the exact provider credential injected into only that process. It does not authorize generation.

## obtain narrow approvals

Prepare an authorization packet from the contract before requesting any consequential action. Ask
separately for provider generation/spend, data acquisition under terms, paid compute or hardware,
OSF registration or tags, human-subject activity, paper-account writes, and publication or push.
Authorization expires when a bound hash, endpoint, model revision, cap, or prerequisite changes.

Never store keys in prompts, skill files, config, manifests, logs, or git. Report credential
presence only. Paper credentials must never be accepted for live-money endpoints; live-money
trading is outside this skill.

## delegate bounded audits

Use up to three read-only research agents when parallel work materially helps:

- methods and statistical validity;
- evidence, provenance, rights, and contamination; and
- reproducibility, provider drift, security, and cost.

Give each agent a bounded question and require file/line or primary-source evidence, severity, and
blockers. Keep one main operator as the sole writer and adjudicator during execution. Refresh the
living evidence census with `refresh-external-evidence` when the phase reaches a mandatory refresh
point.

## recover without erasing evidence

- **offline/mock:** resume the same hashed materialization and reuse only artifacts that verify.
- **paid/live:** do not blind-retry. Preserve incomplete artifacts, reconcile provider usage and
  conservative reservations, then require a new remaining-envelope authorization.
- **drift:** compile a new plan or materialization; never mutate an old ledger to appear current.
- **corruption:** preserve and quarantine the artifact before replacement.
- **analysis/release:** reproduce into a new hash-addressed location from a clean environment.

## verify and report

After implementation changes, run the project tests, linter, type checker, and the phase-specific
mock/reproduction path. Before a paper check, confirm that mock evidence is rejected.

Return one compact control report containing:

- phase, tier, and resulting status;
- source, control-file, plan, materialization, and evidence snapshot identifiers;
- gates passed and blockers with evidence paths;
- actions taken, verification results, and actual or reserved usage/cost; and
- the next safe action plus the next approval boundary.

Do not claim completion merely because a command ran. Stop at the first unresolved gate and say
exactly what evidence or implementation is missing.
