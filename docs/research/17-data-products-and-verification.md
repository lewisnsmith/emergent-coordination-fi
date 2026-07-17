# 17 — Data Products and Verification

H11 asks whether verified simulation, detection, exposure, and causal-attribution results can become
reproducible datasets without overstating what each row proves. The governing study is `exp-022` in
[`configs/research-program.yaml`](../../configs/research-program.yaml).

## Product boundary

“Actionable” means suitable for reproducible research, model evaluation, surveillance triage, or
human review with explicit uncertainty. It does not mean a profitable trading signal, personalized
investment advice, automatic enforcement evidence, or proof that a person or institution used AI.

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

## Source artifacts already produced

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

## Release layout

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

## Required schemas

### `simulation_truth.parquet`

One row per independent simulation outcome unit or event. Required fields:

- `release_id`, `simulation_id`, `independent_block_id`, `market_replica_id`;
- market, regime, window, seed, instrument/venue scope, and timestamp bounds;
- treatment assignment, AI-capital share, agent ecology, model/profile/prompt/harness hashes;
- randomized ground-truth label and assignment probability;
- outcome/feature IDs and values with units;
- config, dataset, code, and upstream verification hashes; and
- `causal_status: randomized_simulation_only`.

### `signature_events.parquet`

One row per locked signature/window result. Required fields:

- `event_id`, `domain`, market/venue/instrument scope, start/end time;
- `signature_id`, version, feature-set hash, training-release hash;
- score, threshold, decision, compatible interval, calibration domain, expected false-positive rate;
- domain-shift and data-quality status;
- linked simulation/transport artifacts; and
- `causal_status`, restricted to `simulation_signature` or `ai_like_not_attributed`.

### `ai_exposure.parquet`

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

### `verified_events.parquet`

One row per frozen causal estimand, not per raw trade. Required fields:

- `verified_event_id`, linked `exposure_id`, event/window, treatment and counterfactual definitions;
- identification-design ID, assignment/exposure unit, cluster, estimator version;
- effect, unit, interval, SESOI, equivalence/noninferiority bound, raw/adjusted p-values;
- pretrend, placebo, spillover, and sensitivity verdicts;
- assumptions, transport domain, population scope, and limitations; and
- `causal_status: attributed_under_named_design`.

The row is excluded from this tier if exposure provenance or the counterfactual verification fails.
It remains available in the lower appropriate tier with the failure reason.

## Dataset card and claim registry

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

## Splits, leakage, and held-out utility

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

## Release gates

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

## Exact verification outputs

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

## How users verify and see the data

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
uv run flock analyze-study results/<block-1> results/<block-2> --output results/study-h1.json
```

For a future release, users should first read `dataset_card.md`, verify
`release_verification.json` says `pass`, recompute `checksums.sha256`, inspect `lineage.json` and
`splits.json`, and confirm that their intended use is allowed. Human-readable release figures must
show tier/status labels directly, with separate panels for simulation truth, AI-like events,
verified exposure, and causal effects.

There is currently no `flock export-release` command. Until the exporter and release verifier are
implemented and `exp-022` dependencies pass, the exact tier files above are a binding scaffold, not
an acquired or validated dataset release.
