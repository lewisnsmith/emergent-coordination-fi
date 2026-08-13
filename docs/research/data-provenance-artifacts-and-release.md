# Data provenance, artifacts, and release

**Status: ACTIVE release manual; empirical release remains blocked. Last consolidated:
2026-08-12.** The repository has an internal deterministic mock reproduction from an empty
directory. It does not yet have an independent public clean-room reproduction. No paid
frontier-model study, frozen preregistration, completed independent review, or paper-eligible
empirical release exists.

## Evidence and release boundary

The public dataset, owned-alpha evaluation, and AI-agent trading-risk findings keep separate
schemas, claims, and release gates. Simulation truth, transported signatures, AI-like real
events, verified exposure, and causally attributed effects remain distinct. No tier or output
borrows evidentiary status from another.

## Input datasets and acquisition status

The project uses **inputs** (market data and reference panels) to produce **outputs** (the
candidate agent-decision research artifacts). Input payloads are local and gitignored;
`datasets/manifests.json` versions each dataset and hashes its complete file bundle. Builders live in
`src/flock/data/builders/` and run through `flock data build <builder>`.

### Acquisition status (2026-07-23)

Only the seeded `synthetic-equities-v1` dataset is acquired; its latest registry entry is bundle-
hashed version 2. Equity, prediction-market, 13F, participant trust/delegation,
AI-exposure/adoption, and causal-event datasets are not acquired. `flock validate` reports required
missing inputs as execution blockers; documentation or a builder does not count as acquired data.

### Input datasets

| Source/builder | Contents | Purpose |
|---|---|---|
| `synthetic` | Seeded Markov transitions among trending, mean-reverting, and crisis regimes; common and per-symbol idiosyncratic factors; known-sentiment templated news at regime shifts. Schema: `bars` (`ts`, `symbol`, OHLCV) + `events` (`ts`, `symbol`, `headline`, `sentiment`). | Free, offline pipeline validation, known-convergence metric calibration, and contamination-free robustness. |
| `equities` | yfinance daily OHLCV for configurable symbols across multiple windows, including the 2020 crash, 2021 melt-up, 2022 drawdown, and post-cutoff periods. | Historical equity replay and contamination robustness. |
| `polymarket`, `kalshi` | Historical resolved binary contracts: metadata, price history, and outcome, rendered at prices in `(0,1)`. | Prediction-market replay. |
| `refs13f` | SEC EDGAR quarterly holdings for institutional-manager panels (with a descriptive User-Agent). | H2 external anchors for portfolio overlap and LSV herding. These feed analysis directly, not replay. |
| Planned trader panels | Prediction-market positioning where lawfully obtainable and reproducibly sampled. | Optional descriptive H2 context; no builder or acquired dataset exists yet. |

#### Human trust/delegation panel — H6

- Requires ethics/IRB review as applicable, consent, deidentification, recruitment, randomized
  disclosure/oversight/performance treatments, and incentive-compatible delegation outcomes.
- Synthetic personas or model answers cannot substitute for human trust data.

#### AI exposure and adoption registry — H7/H10

- Time-stamped, source-verifiable records of AI advice/autonomy, assets or order flow exposed,
  deployment date, model/vendor, oversight, and confidence in attribution.
- H10 additionally needs assignment timing or a credible natural-experiment counterfactual.
  Market-pattern resemblance is never stored as verified exposure.

### Output datasets (deliverables)

| Artifact | Unit and contents |
|---|---|
| `results/<run-id>/decisions.jsonl` | One record per agent-step: agent metadata, observation digest, requested and clipped orders, rationale, parse status, usage, and latency. |
| `results/<run-id>/fills.parquet` | Executed fills with prices and fees. |
| `results/<run-id>/portfolio.parquet` | Per-step, per-agent cash, equity, and JSON-encoded portfolio weights. |
| `results/<run-id>/manifest.json` | Inline config and hash, code git SHA, dataset name/version/hash, agent model parameters and seeds, run seed, timing, and cost. |

Representative LLM decision record:

```json
{
  "run_id": "...", "step": 42, "ts": "2024-03-01",
  "agent_id": "llm-claude-x-neutral-0", "cohort": "llm",
  "kind": "llm", "model": "claude-x", "model_id": "...", "persona": "neutral",
  "temperature": 0.7, "seed": 7,
  "observation_digest": "sha256:...",
  "action": "buy",
  "prompt_hash": "sha256:...",
  "raw_response_hash": "sha256:...",
  "evidence_refs": ["price:AAPL"],
  "grounding_ok": true,
  "orders": [{"symbol": "AAPL", "side": "buy", "quantity": 10, "limit_price": null}],
  "orders_clipped": [{"symbol": "AAPL", "side": "buy", "quantity": 10, "limit_price": null}],
  "rationale": "...", "parse_ok": true,
  "usage": {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0},
  "latency_s": 0.0
}
```

After licensing and release verification, the artifacts can provide `(observation, agent
parameterization, decision, rationale, outcome)` tuples for research beyond the proposed study.

Study outputs add `assignments.parquet`, `contrasts.parquet`, `verification.json`,
`safety_failures.parquet`, and `claims.json`. Real-market data products keep four labels
separate: simulation truth, AI-like signature, verified AI exposure, and causally verified AI
event. See [Causal-tier release schemas](#causal-tier-release-schemas).

### Provenance & licensing notes

- Published artifacts contain derived decision logs, not redistributed raw yfinance/vendor data.
- SEC EDGAR and public Polymarket/Kalshi APIs supply reference inputs. Verify source-specific
  licensing and redistribution terms before publishing raw payloads.

## Artifact data dictionary

#### `bars.parquet`

One row per timestamp-symbol market bar.

Expected columns:

- `ts`: timestamp or date.
- `symbol`: asset or contract identifier.
- `open`: opening price.
- `high`: high price.
- `low`: low price.
- `close`: closing/reference price.
- `volume`: traded volume or synthetic volume.

Questions to ask:

- What symbols are included?
- What date range is covered?
- Are timestamps aligned across symbols?
- Are there missing bars?
- Are prices adjusted?
- Is volume real or synthetic?
- Which price is used in observations?
- Which price is used for fills?
- Does the trailing observation window accidentally include future data?

---

#### `events.parquet`

One row per event/news item.

Expected columns:

- `ts`: timestamp.
- `symbol`: related symbol, or empty/market-wide.
- `headline`: text shown or summarized to the agent.
- `sentiment`: numeric score, usually between -1 and 1.

Questions to ask:

- Are events synthetic or real?
- Are events visible to agents?
- Is sentiment visible to agents, or used only in analysis?
- Are events aligned with regime shifts?
- Could sentiment leak the correct future direction too directly?
- Are prediction-market outcomes hidden until after resolution?

---

#### `meta.json`

Dataset metadata.

May include:

- builder name.
- parameters.
- seed.
- provenance.
- symbol list.
- date range.
- instrument type.

Questions to ask:

- Can this dataset be rebuilt exactly?
- Are all relevant parameters recorded?
- Does the dataset hash depend on all important inputs?

---

#### `decisions.jsonl`

One row per agent-step decision.

Expected meaning:

- What did this agent decide at this time?
- What orders did it intend to place after parsing and clipping?
- What rationale did it provide?
- Was the response parsed successfully?
- How much did the call cost?

Important fields:

- `run_id`
- `step`
- `ts`
- `agent_id`
- `cohort`
- `kind`
- `model`
- `persona`
- `temperature`
- `seed`
- `observation_digest`
- `prompt_hash`
- `orders`
- `rationale`
- `parse_ok`
- `usage`
- `latency_s`

Questions to ask:

- Does `orders=[]` mean hold?
- Was this an actual hold or a parse-failure hold?
- Did the agent hallucinate unavailable information?
- Did the rationale match the order?
- Did multiple agents see byte-identical market information?
- Were orders clipped before logging?
- Is the action label too simple for multi-symbol decisions?

---

#### `fills.parquet`

Executed trades.

Questions to ask:

- Did every submitted order fill?
- At what price?
- With what fee/slippage?
- Was the fill delayed to the next bar?
- Does replay mode fill differently from shared exchange mode?
- Do fills reconcile with portfolio changes?

---

#### `portfolio.parquet`

Per-step per-agent portfolio state.

Typical contents:

- step.
- timestamp.
- agent_id.
- cohort.
- cash.
- equity.
- weights / positions.

Questions to ask:

- Are positions marked to current prices?
- Are long and short positions represented correctly?
- Is cash included in equity?
- Are position limits binding?
- Do portfolio weights explain the overlap metrics?

---

#### `manifest.json`

Run provenance.

Should include:

- run ID.
- config.
- config hash.
- git SHA.
- dataset name/version/hash.
- model parameters.
- seed.
- number of agents.
- number of steps.
- total cost.

Questions to ask:

- Can this run be reproduced?
- Was the exact model ID recorded?
- Was the exact dataset hash recorded?
- Was the exact code version recorded?
- Are seeds and configs sufficient to reproduce non-LLM behavior?

---

## Causal-tier release schemas

H11 asks whether verified simulation, detection, exposure, and causal-attribution results can become
reproducible datasets without overstating what each row proves. The governing study is `exp-022` in
[`configs/research-program.yaml`](../../configs/research-program.yaml).

### Product boundary

For the public H11 product, “actionable” means suitable for reproducible research, model
evaluation, surveillance triage, or human review with explicit uncertainty. It does not make the
public release a profitable trading signal, personalized investment advice, automatic enforcement
evidence, or proof that a person or institution used AI. This boundary does not prohibit the
separately labeled owned-alpha track, which has its own locked out-of-sample gates.

The release must preserve four causal tiers:

| Tier | File | Meaning | Forbidden reinterpretation |
|---|---|---|---|
| Simulation truth | `simulation_truth.parquet` | Known randomized treatment and outcomes inside a specified simulator | Verified real-market effect |
| Signature events | `signature_events.parquet` | Locked signature scores in simulation or real data | AI caused the event |
| Verified exposure | `ai_exposure.parquet` | Documented AI deployment/advice scope and provenance | Exposure caused a market outcome |
| Causally verified events | `verified_events.parquet` | Effect estimate under a named exposure/counterfactual design | Universal AI effect outside that design |

Rows may move to a higher tier only through a new versioned build with the required evidence. A
score in `signature_events.parquet` can never be copied into `verified_events.parquet` merely because
it is large.

### Source artifacts already produced

The current experiment runner writes `results/<run-id>/decisions.jsonl`, `fills.parquet`,
`portfolio.parquet`, and `manifest.json` through
[`logging_/decisions.py`](../../src/flock/logging_/decisions.py). `decisions.jsonl` records intended
and clipped orders, prompt/response hashes, evidence references, grounding verdicts, usage, cost,
and latency. The report generator in
[`analysis/report.py`](../../src/flock/analysis/report.py) writes `report.md` and:

- `report/convergence_by_cohort.png`;
- `report/kappa_heatmap.png`; and
- `report/equity_curves.png`.

These are run artifacts, not automatically a validated cross-study release. `exp-022` remains
scaffolded because a dataset exporter and full release-verification runner do not yet exist.

### Release layout

Each immutable release should use:

```text
results/releases/<release-id>/
  simulation_truth.parquet
  signature_events.parquet
  ai_exposure.parquet
  verified_events.parquet
  dataset_card.md
  schemas.json
  lineage.json
  splits.json
  claims.json
  license.json
  checksums.sha256
  release_verification.json
  figures/
```

`release-id` includes semantic version, build date, and source commit. A published release is never
overwritten. Corrections create a new version and a machine-readable changelog/deprecation link.
Raw vendor data, activation tensors, personal identifiers, provider secrets, and restricted
exposure records remain outside the public bundle.

### Required schemas

#### `simulation_truth.parquet`

One row per independent simulation outcome unit or event. Required fields:

- `release_id`, `simulation_id`, `independent_block_id`, `market_replica_id`;
- market, regime, window, seed, instrument/venue scope, and timestamp bounds;
- treatment assignment, AI-capital share, agent ecology, model/profile/prompt/harness hashes;
- randomized ground-truth label and assignment probability;
- outcome/feature IDs and values with units;
- config, dataset, code, and upstream verification hashes; and
- `causal_status: randomized_simulation_only`.

#### `signature_events.parquet`

One row per locked signature/window result. Required fields:

- `event_id`, `domain`, market/venue/instrument scope, start/end time;
- `signature_id`, version, feature-set hash, training-release hash;
- score, threshold, decision, compatible interval, calibration domain, expected false-positive rate;
- domain-shift and data-quality status;
- linked simulation/transport artifacts; and
- `causal_status`, restricted to `simulation_signature` or `ai_like_not_attributed`.

#### `ai_exposure.parquet`

One row per verified exposure interval. Required fields:

- `exposure_id`, authorized entity/product/desk scope, market/assets, start/end time;
- advice-only, human-reviewed, or autonomous status;
- documented capital/exposure definition and uncertainty;
- model/provider family and revision when legitimately available;
- evidence source type, source hash, verification method/date, and permission class;
- overlap/interference fields and linked identification design; and
- `causal_status: exposure_verified_outcome_not_attributed`.

Public releases should aggregate or pseudonymize entity scope to the approved level. A private
exposure registry needs access controls, audit logs, retention limits, and a legal/ethics basis.

#### `verified_events.parquet`

One row per frozen causal estimand, not per raw trade. Required fields:

- `verified_event_id`, linked `exposure_id`, event/window, treatment and counterfactual definitions;
- identification-design ID, assignment/exposure unit, cluster, estimator version;
- effect, unit, interval, SESOI, equivalence/noninferiority bound, raw/adjusted p-values;
- pretrend, placebo, spillover, and sensitivity verdicts;
- assumptions, transport domain, population scope, and limitations; and
- `causal_status: attributed_under_named_design`.

The row is excluded from this tier if exposure provenance or the counterfactual verification fails.
It remains available in the lower appropriate tier with the failure reason.

### Dataset card and claim registry

`dataset_card.md` must state:

- purpose, intended users, prohibited uses, and financial-advice disclaimer;
- causal-tier definitions and row counts by tier/status;
- source coverage, retrieval dates, licenses, permissions, and missing populations;
- construction, randomization/identification, estimands, and independent units;
- model/checkpoint and prompt/profile scope;
- quality, calibration, uncertainty, failure, and subgroup results;
- privacy, human-subject, and deidentification procedures;
- known domain shifts, bias, limitations, and update/deprecation policy; and
- exact reproduction and verification commands.

`claims.json` maps every report statement to hypothesis, estimand, causal tier, data rows, code/data
hashes, effect/interval, adjusted inference, figure/table, limitations, and verification status. A
claim with no complete mapping is omitted from the public report.

### Splits, leakage, and held-out utility

`splits.json` assigns entire market trajectory lineages, participant clusters, institutions, and
time blocks to discovery, validation, or locked test. No shared seed, derived trajectory, prompt
cache, participant, exposure unit, or forward-looking normalization may cross a prohibited split.

The independent evaluation unit is the versioned release tested on a separately hashed held-out
set. Required release estimands are:

- reproduction rate from frozen inputs;
- schema/provenance/lineage completeness;
- leakage and duplicate rate;
- grounding and logical-failure rate;
- signature calibration, false-positive rate, and domain-shift coverage;
- causal-label precision under hand/audit review;
- held-out utility for the stated benchmark; and
- privacy/deidentification failure rate.

Utility must be evaluated against a locked baseline and uncertainty interval. A dataset is not
released because its training performance is high.

### Release gates

Publication requires all of the following:

1. Every upstream run has `verify-run` success or a visible failed-run status.
2. All source artifacts, configs, datasets, code, assignments, and transformations are hashed.
3. Schemas, units, uniqueness, nullability, ranges, timestamps, and foreign keys pass.
4. Splits pass trajectory-, participant-, exposure-, and time-leakage scans.
5. Every signature row carries calibration/domain-shift and noncausal labeling.
6. Every exposure row carries provenance, permission, verification, and uncertainty.
7. Every causal row carries a counterfactual, falsification suite, and passed identification audit.
8. Human data have ethics/IRB or equivalent approval, consent, deidentification, and allowed-use
   documentation; participant-level free text and direct identifiers are absent.
9. Vendor/research licenses permit the released transformations.
10. `checksums.sha256`, `lineage.json`, `claims.json`, and `release_verification.json` reconcile.

Any hard failure sets `release_status: blocked`. The bundle may be retained privately for debugging
but cannot be described as validated or published. Warnings remain visible in the dataset card.

### Exact verification outputs

`release_verification.json` must contain:

- release ID/version/commit and verification timestamp;
- pass/fail for schema, hashes, lineage, leakage, grounding, statistics, privacy, license, causal
  labels, and held-out benchmark;
- expected/realized row counts and independent-unit counts;
- every warning, exclusion, failed upstream artifact, and unresolved blocker;
- checker versions and reproduction commands; and
- one final `release_status` of `pass`, `blocked`, or `deprecated`.

`lineage.json` forms a directed acyclic graph from release rows to source run, dataset, prompt,
profile, model, transformation, and analysis hashes. `checksums.sha256` covers every public payload.
`schemas.json` includes field descriptions, types, units, allowed values, and causal-status enums.

### How users verify and see the data

Current run-level workflow:

```bash
uv run flock data list
uv run flock validate --output readiness.json
uv run flock verify-run results/<run-id> > results/<run-id>/run-verification.json
uv run flock analyze <run-id>
```

Users inspect `results/<run-id>/report.md` and its PNG figures, then trace tables to the native run
artifacts and `manifest.json`. Study-level H1 users can run:

```bash
uv run flock analyze-study results/study-source.json --output results/study-h1.json
```

For a future release, users should first read `dataset_card.md`, verify
`release_verification.json` says `pass`, recompute `checksums.sha256`, inspect `lineage.json` and
`splits.json`, and confirm that their intended use is allowed. Human-readable release figures must
show tier/status labels directly, with separate panels for simulation truth, AI-like events,
verified exposure, and causal effects.

There is currently no `flock export-release` command. Until the exporter and release verifier are
implemented and `exp-022` dependencies pass, the exact tier files above are a binding scaffold, not
an acquired or validated dataset release.

## Grounding and logical verification

This protocol defines what `flock` can verify about model outputs and what it cannot guarantee. The
machine-readable policy is
[`configs/safeguards/grounding.yaml`](../../configs/safeguards/grounding.yaml). The current runtime
uses [`agents/grounding.py`](../../src/flock/agents/grounding.py),
[`agents/llm_agent.py`](../../src/flock/agents/llm_agent.py), and
[`experiments/verify.py`](../../src/flock/experiments/verify.py).

### Assurance boundary

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

### Questions and safeguards

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

### Current implemented controls

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

### Required input provenance

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

### Logical verification layers

#### Response invariants

Each agent-step must have exactly one terminal record. Orders use only listed symbols, finite
positive quantities, valid sides, and feasible cash/inventory/position limits. Abstention and
orders cannot both be true. Voluntary hold, parse-failure hold, grounding rejection, and constraint-
forced hold remain different labels.

#### Market and ledger invariants

Every fill refers to a known agent/order, uses the configured fee rule, and reconciles cash and
positions. Portfolio snapshots equal opening state plus all fills and fees. Shared-exchange book
events reconstruct in price-time order. Missing or duplicate agent-step and portfolio rows are hard
failures.

#### Metamorphic and negative-control tests

Run seeded tests where expected logical behavior is known:

- permuting anonymous symbol labels must permute, not otherwise change, outputs;
- scaling all prices and quantities consistently must preserve portfolio weights;
- reordering semantically irrelevant evidence must not create a directional signal;
- removing news must not introduce a new cited news fact;
- flipping a known synthetic signal should flip the reference action when constraints permit;
- future or resolution fields must be rejected;
- unsupported authorities, anchors, and instruction-like news must not override the mandate; and
- sham input/activation interventions should produce null-calibrated effects.

Synthetic reference-action cases establish whether the system detects correct, incorrect, and abstention
behavior. They do not establish real-world profitability.

### Repository and run verification

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
uv run flock analyze-study results/study-source.json --output results/study-h1.json
```

### Outputs and how to inspect them

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

### Release gates

A confirmatory release fails closed if provenance is incomplete, future leakage is detected,
strict-mode grounding fails, assignments do not match hashes, ledger/cost totals do not reconcile,
planned observations are missing, pair/call pseudoreplication is present, or multiplicity and
equivalence rules differ from the frozen plan. A failed run may be published as a labeled failure
artifact, never silently repaired or certified.

## Implemented safeguards

#### Research contract and study compilation

- The first-paper boundary is H1/H3/H4; H5 is a separate simulator-bounded extension.
- The compiled contract crosses LLM/classical technology with homogeneous/heterogeneous ecology,
  rotates homogeneous families, balances heterogeneous allocations, and holds out a model family.
- Unknown fields, placeholder identifiers, mutable aliases, overlapping independent windows,
  missing prices, unbalanced cells, count disagreements, and authorization overruns fail closed.
- The current deterministic plan resolves to 197 runs, 397,528 agent-steps, and 232,360 calls with
  plan hash `539ac6c3591f37e4a410d06ed1f98a2575b2d6cc9270f540ffa646602eba26b6`.
  This is the configured full-program plan, not current execution or spending authorization.
- `flock materialize-study` deterministically expands those totals into 197 lineage-preserving run
  assignments. It emits runner configs only when dataset, model, persona, prompt, runtime-budget,
  and treatment semantics resolve explicitly. `--allow-unresolved` exports auditable blockers
  without making an assignment executable.

#### Provider execution and cost control

- `flock doctor [--live]`, `compile-study`, `validate-study`, and plan-based `estimate` exist.
- Provider attempts retain request/retry/reasoning/cache-token metadata; only classified transient
  failures retry and `Retry-After` is honored.
- Cache writes and run outputs are atomic. Attempts are isolated, checkpointed, and never truncate
  a completed run. Local cache hits are not counted as new billed requests.
- Every frontier experiment requires explicit request, input-token, output-token, and dollar caps.
  The call boundary reserves a conservative worst-case envelope before a provider request.
- The dated YAML catalog is the only price source. Every paid stage requires a fresh estimate and explicit authorization.

#### Provenance, market mechanics, and inference

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
- Nested simulation power includes blocks, agents, steps, provider heterogeneity, and missing
  blocks. Its H1 sign-flip calculation is sensitivity analysis under symmetry, not design-based
  primary inference. The old normal approximation is diagnostic-only.

#### Paper and reproducibility artifacts

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

A safeguard marked implemented is software evidence only. It is not evidence that a paid
study, scientific claim, public release, or independent reproduction passed.

## Data-quality questions

#### General data quality

- Are timestamps consistent?
- Are time zones handled?
- Are there duplicate rows?
- Are there missing bars?
- Are all symbols present at every step?
- Are prices positive?
- Are returns plausible?
- Is volume plausible?
- Are splits/dividends adjusted in equities?
- Are prediction-market prices bounded between 0 and 1?
- Are resolved outcomes hidden before resolution?
- Are event timestamps realistic?
- Are synthetic data regimes balanced?

---

#### Leakage questions

- Does any observation include future prices?
- Does an event mention something that would only be known later?
- Does sentiment reveal the future direction too directly?
- Does the agent know the final outcome of a prediction market?
- Are regime labels hidden from agents?
- Are fills based on future information only after the decision is made?
- Does the prompt include summary statistics computed using future data?

---

#### Reproducibility questions

- Is every random draw seeded?
- Is the dataset hash recorded?
- Is the config hash recorded?
- Is the git SHA recorded?
- Is the model ID recorded?
- Are provider parameters recorded?
- Are prompts hashed?
- Are LLM responses cached?
- Can the same analysis be rerun offline?

---

## Agent-output audit questions

#### Behavioral questions

- How often does each agent trade?
- Which symbols does each agent prefer?
- Does each agent follow momentum?
- Does each agent follow reversal?
- Does each agent respond to volatility?
- Does each agent respond to news sentiment?
- Does each agent diversify?
- Does each agent overtrade?
- Does each agent become more conservative after losses?
- Does each agent double down after losses?
- Does each agent obey risk constraints?
- Does each agent hallucinate information?
- Does each agent cite unavailable data?

---

#### LLM-specific questions

- Does temperature change trades or only language?
- Does persona change trades or only language?
- Does reasoning effort increase or decrease convergence?
- Do stronger models converge more?
- Do weaker models follow prompt defaults more?
- Does memory increase convergence over time?
- Does memory create path dependence and divergence?
- Are rationales faithful to actions?
- Are rationales more diverse than decisions?
- Can provider/model be predicted from trades alone?
- Can provider/model be predicted from rationales alone?

---

#### Error and failure questions

- How often does JSON parsing fail?
- Are parse failures concentrated in a model/provider?
- Are parse failures counted as holds?
- Do parse failures bias convergence metrics?
- Are invalid symbols produced?
- Are invalid quantities produced?
- Are orders clipped by cash or position limits?
- Are constraints causing artificial convergence?

---

## Result-trust procedure

Before believing any result, check:

- [ ] Dataset is understood.
- [ ] Dataset hash is recorded.
- [ ] Config hash is recorded.
- [ ] Git SHA is recorded.
- [ ] Seeds are recorded.
- [ ] Agent list is known.
- [ ] Cohort sizes are equal or justified.
- [ ] Action distributions are reported.
- [ ] Parse failures are reported.
- [ ] Constraint clipping is reported.
- [ ] Null cohort is included.
- [ ] Baselines are strong enough.
- [ ] Cohen's kappa is reported, not just raw agreement.
- [ ] Portfolio metrics are reported.
- [ ] Strategy fingerprint metrics are reported.
- [ ] Confidence intervals are reported.
- [ ] The frozen primary test is reported, with permutation or sign-flip output labeled as a
  sensitivity analysis wherever assignment does not justify randomization inference.
- [ ] Multiple comparisons are handled for confirmatory claims.
- [ ] Prompt-template sensitivity is checked.
- [ ] Regime sensitivity is checked.
- [ ] Contamination concerns are addressed.
- [ ] Claims are labeled confirmatory or exploratory.

---

## Release gates and handoff

**Status: BLOCKED; this is a release plan, not evidence of a completed study. Snapshot date:
2026-07-17.** Checkboxes remain unchecked until their named artifacts exist and pass verification.
Do not infer completion from implemented scaffolding or passing mock tests.

### Scientific release gate

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

### Software and artifact gate

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

### Paper and accountability gate

- [ ] The manuscript contains methods, results, robustness, conclusion, limitations,
  ethics/broader impacts, reproducibility, data/code availability, funding/conflicts, bibliography,
  and an accurate LLM-use disclosure.
- [ ] Figure titles, captions, and legends distinguish mock, pilot, confirmatory, exploratory, and
  simulator-only evidence and show independent units where relevant.
- [ ] Lewis has verified and signed
  [Authorship, AI use, and accountability](authorship-ai-use-and-accountability.md), can explain the design and code
  relied on for claims, and has not presented generated prose as understanding.
- [ ] The dated [Research decisions and execution log](research-decisions-and-execution-log.md) includes failures, amendments, null or
  contradictory outcomes, and stop/go decisions without rewriting earlier entries.
- [ ] A release-derived correction comparison uses real hashed pilot artifacts and clearly labels
  the invalid agent-level analysis as diagnostic; its historical rationale remains in the
  [dated correction record](research-decisions-and-execution-log.md#2026-07-17--pseudoreplication-and-ecology-correction-record).
- [ ] Genuine independent statistics, market-microstructure, and reproducibility reviews are
  recorded in [Independent review protocol and responses](independent-review-protocol-and-responses.md); no unresolved release-blocking or high-priority finding remains.
- [ ] README and portfolio descriptions say exactly what was executed and reproduced, not what the
  broader H1–H13 agenda proposes.
- [ ] The release is immutable, checksummed, versioned, licensed, archived, and linked to the exact
  source commit without rewriting prior history.

### Required release manifest fields

The final manifest records the release ID/date, source and preregistration commits, OSF identifier,
code/environment lock hashes, data-bundle hashes and permissions, exact model/provider revisions,
SDK/API versions, pricing snapshot, prompts/profiles, assignment and dependence maps, random seeds,
independent-unit counts, expected/realized calls and costs, failures/exclusions, verification
results, paper artifact hashes, disclosure/review status, and the clean-room reproduction record.

Any missing required field is either a release blocker or an explicit `not applicable` with a
machine-checkable reason. Blank, inferred, and `unknown` values cannot silently pass.

### Three-to-five-minute walkthrough plan

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

### Independent handoff test

Give an uninvolved reader only the public release location and ask them to:

1. identify the strongest supported claim and three forbidden interpretations;
2. report the top-level independent `n` and explain why agent/call counts differ;
3. reproduce the mock paper and verify the real paid-run manifest without author intervention;
4. trace one paper sentence backward to raw/allowed input provenance; and
5. explain Lewis's contribution, AI assistance, the major corrected mistakes, and unresolved risks.

Record their screen capture or terminal log, environment, elapsed time, questions, and every
discrepancy. Failure of any task blocks the “independently reproducible” claim until corrected and
retested.

## Current blocker register

The current blockers are:

- exact immutable frontier endpoints and lawful historical inputs are unresolved;
- the H2 harmonization input panel has not passed its gate;
- the scoring key and H13 benchmark contracts are not frozen;
- the three first-paper statistical discrepancies must be reconciled in the preregistration;
- H5 lacks persistent orders, background liquidity, reconstructable book exports, calibrated
  targets, and complete ODD/STRESS validation;
- no paid pilot or confirmatory run has executed;
- no immutable preregistration or OSF record exists;
- no genuine independent statistics, market-microstructure, or reproducibility review exists;
- no independent public clean-room reproduction exists; and
- a LaTeX toolchain must be available in release CI before manuscript eligibility.

The current personal-budget lane can proceed locally through evidence audit, workstation
benchmarking, scoring-key construction, local precision tests, and bounded mechanistic
discovery. Those steps do not clear the configured first-paper or H5 release blockers.

## Current verification commands

```bash
UV_NO_EDITABLE=1 uv run flock validate --output readiness.json
UV_NO_EDITABLE=1 uv run flock doctor
UV_NO_EDITABLE=1 uv run flock verify-run results/<run-id> > results/<run-id>/run-verification.json
UV_NO_EDITABLE=1 uv run flock analyze <run-id>
UV_NO_EDITABLE=1 uv run flock analyze-study results/study-source.json --output results/study-h1.json
```

`scaffold_ok=true` is not `execution_ready=true`. A run-level `ok=true` covers only the
implemented checks. Paper, causal, public-data, and independent-reproduction gates remain
separate.
