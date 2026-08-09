# Grounding and Logical Verification

This protocol defines what `flock` can verify about model outputs and what it cannot guarantee. The
machine-readable policy is
[`configs/safeguards/grounding.yaml`](../../configs/safeguards/grounding.yaml). The current runtime
uses [`agents/grounding.py`](../../src/flock/agents/grounding.py),
[`agents/llm_agent.py`](../../src/flock/agents/llm_agent.py), and
[`experiments/verify.py`](../../src/flock/experiments/verify.py).

## Assurance boundary

No model, prompt, evaluator, or test suite can guarantee that an LLM will never hallucinate. The
defensible claim is narrower:

> Supplied evidence is machine-addressable; selected claims and constraints are checked
> deterministically; invalid strict-mode proposals fail closed to no order; all known failures are
> retained and reported.

Passing grounding means passing the implemented checks for a particular request and validator
version. It does not prove that every qualitative sentence is true, that the investment is good,
that every prompt injection was detected, or that an output's explanation reveals its mechanism.
An LLM judge may assist triage but may never be the sole verifier or override a deterministic
failure.

## Questions and safeguards

| Question | Evidence required | Allowed conclusion |
|---|---|---|
| Did the model cite supplied information? | Every evidence reference resolves to that observation | References are syntactically grounded |
| Did it fabricate a number? | Numeric statement matches a supplied value or preregistered derivation | No unsupported number was detected by this validator |
| Did it obey hard trading constraints? | Deterministic schema, symbol, quantity, cash, inventory, and limit checks | Proposed/executed order passed enumerated constraints |
| Did untrusted news attempt prompt injection? | Delimited evidence plus detector and adversarial cases | Known injection pattern was detected or resisted |
| Is the rationale truthful? | Controlled causal interventions, not prose alone | Rationale may be audited but is not mechanistic evidence |
| Is the run reproducible? | Config, dataset, model, prompt/response, code, and artifact hashes | The recorded run can be reconstructed to the stated boundary |
| Is a market claim statistically valid? | Independent-block analysis and frozen estimand | The claim passed the named statistical contract |

H12 pressure text never relaxes evidence or hard constraints. “Must trade,” urgency, distress, and
fictional life-or-death wording are experimental treatments, not authorization to invent support.
The invariant safety header and 24 cells are defined in
[`configs/prompts/pressure-treatments.yaml`](../../configs/prompts/pressure-treatments.yaml).

## Current implemented controls

The current agent prompt requests structured orders, evidence references, confidence, and stated
uncertainties. It tells the model to treat news as untrusted and hold when evidence is insufficient.
Parsing rejects unknown symbols, invalid sides, and nonpositive quantities. One malformed response
is retried; a second failure becomes a distinct `parse_ok=false` hold.

`evidence_catalog()` currently addresses cash, equity, prices, bar closes/volumes, positions, and
news headlines. `validate_grounding()` currently checks:

- unknown evidence references;
- missing references in strict mode;
- confidence outside `[0, 1]`;
- numeric rationale tokens not found among observed numeric values; and
- several explicit prompt-injection-like headline patterns.

In `grounding_mode: strict`, a failed verdict produces no executable order while preserving the
proposal's audit fields. In `grounding_mode: audit`, the order may execute and the failure remains
logged. Confirmatory safety and market-impact runs should use strict mode unless an alternative raw-
behavior mode and its paired strict control were frozen in advance.

The current checker is deliberately incomplete relative to the full policy. It does not yet parse
every factual clause, validate arbitrary derived formulas, enforce the entire response contract in
the policy YAML, or detect every semantic injection. Reports must state the exact validator version
and residual failure risk rather than describing the system as hallucination-proof.

## Required input provenance

Before a confirmatory call, preserve and hash:

- expanded experiment config and independent-block assignment;
- dataset manifest, payload files, timestamp cutoffs, source, retrieval time, and license;
- exact provider model ID/API revision or local checkpoint hash;
- system, task, profile, pressure, information, and response-contract components separately;
- rendered observation and evidence catalog;
- provider parameters, request ID when available, retry count, token use, and cache status; and
- raw and normalized responses.

An evidence item must include a stable ID, value, unit, availability time, and source artifact hash.
Outcome/resolution data and future-derived statistics are prohibited before their public timestamp.
Untrusted content must remain visibly delimited below the instruction hierarchy.

## Logical verification layers

### Response invariants

Each agent-step must have exactly one terminal record. Orders use only listed symbols, finite
positive quantities, valid sides, and feasible cash/inventory/position limits. Abstention and
orders cannot both be true. Voluntary hold, parse-failure hold, grounding rejection, and constraint-
forced hold remain different labels.

### Market and ledger invariants

Every fill refers to a known agent/order, uses the configured fee rule, and reconciles cash and
positions. Portfolio snapshots equal opening state plus all fills and fees. Shared-exchange book
events reconstruct in price-time order. Missing or duplicate agent-step and portfolio rows are hard
failures.

### Metamorphic and negative-control tests

Run seeded tests where expected logical behavior is known:

- permuting anonymous symbol labels must permute, not otherwise change, outputs;
- scaling all prices and quantities consistently must preserve portfolio weights;
- reordering semantically irrelevant evidence must not create a directional signal;
- removing news must not introduce a new cited news fact;
- flipping a known synthetic signal should flip the oracle response when constraints permit;
- future or resolution fields must be rejected;
- unsupported authorities, anchors, and instruction-like news must not override the mandate; and
- sham input/activation interventions should produce null-calibrated effects.

Synthetic oracle cases establish whether the system detects correct, incorrect, and abstention
behavior. They do not establish real-world profitability.

## Repository and run verification

The repository preflight checks research-program references, frontier eligibility metadata,
profile membership, experiment configs, acquired datasets, the 32 MPHIQ schemes, and the 24 pressure
cells. It deliberately distinguishes `scaffold_ok` from `execution_ready`: missing external data,
ethics approval, exposure data, or runners remain visible blockers.

Run verification currently checks decision/portfolio completeness, duplicate rows, known agents,
clipped-order validity, prompt/response hashes for LLMs, strict grounding verdicts, usage-cost
reconciliation, fill fees, cash ledger reconciliation, and the 20% parse-failure warning.

Use:

```bash
uv run flock validate --output readiness.json
uv run flock design --output resolved-design.json
uv run flock run configs/experiments/exp-000-smoke.yaml
uv run flock verify-run results/<run-id> > results/<run-id>/run-verification.json
uv run flock analyze <run-id>
```

`validate` returning `scaffold_ok=true` does not mean `execution_ready=true`. `verify-run` returning
`ok=true` certifies only its implemented checks. Statistical study verification is separate; H1
block aggregation is currently available through:

```bash
uv run flock analyze-study results/<block-1> results/<block-2> --output results/study-h1.json
```

## Outputs and how to inspect them

Current runs write `decisions.jsonl`, `fills.parquet`, `portfolio.parquet`, and `manifest.json`.
The decision log includes intended and clipped orders, rationale, parse status, evidence references,
confidence, uncertainties, grounding verdict/failures, prompt/response hashes, usage, and latency.

The full release contract additionally requires:

- `evidence_catalog.parquet`;
- `request_provenance.jsonl`;
- `raw_response_audit.jsonl`;
- `grounding_verdicts.parquet`;
- `injection_events.parquet`;
- `logical_gate_failures.parquet`;
- `run_verification.json`; and
- `release_verification.json`.

Users see the human-readable result in `results/<run-id>/report.md` and the generated PNG figures in
`results/<run-id>/report/`. They verify individual failures by filtering `decisions.jsonl` on
`parse_ok`, `grounding_ok`, and `grounding_failures`, then reconcile the CLI JSON verdict with
`manifest.json`. A publication should link every displayed claim to its block-level effect record,
config/data hashes, and verification status.

## Release gates

A confirmatory release fails closed if provenance is incomplete, future leakage is detected,
strict-mode grounding fails, assignments do not match hashes, ledger/cost totals do not reconcile,
planned observations are missing, pair/call pseudoreplication is present, or multiplicity and
equivalence rules differ from the frozen plan. A failed run may be published as a labeled failure
artifact, never silently repaired or certified.
