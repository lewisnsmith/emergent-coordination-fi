# H9 and H11 simulation signatures

## Question

Which observable signatures distinguish simulated AI participation on held-out independent exchange
replicas, and can those simulation-only outputs form a reproducible data product?

## Design

Consume verified exp-011/012 replica outputs without importing unfinished exchange code. Freeze
candidate features and replica-level splits, use nested cross-validation for discovery, reserve an
untouched simulation test set, and evaluate placebo labels and calibration. Hash the final feature
set and model before any external-domain work.

## Estimands, units, and controls

Report held-out replica-level discrimination and calibration with replica bootstrap uncertainty.
The independent unit is a shared-market replica; feature rows and events are nested. Locked test
replicas, placebo labels, leakage scans, calibration curves, and source-artifact hashes are required
controls.

## Failure rules and limits

Replica leakage, dependent splits, failed placebo calibration, unstable feature definitions, or
missing upstream hashes blocks release. A simulation signature does not show AI presence,
coordination, transport, or causation in real data. The released dataset remains explicitly
simulation truth.

## Execution sequence

1. Verify the exchange release and freeze eligible replicas, features, labels, and splits.
2. Implement leakage-safe nested validation and placebo/calibration checks.
3. Freeze the protocol before opening the locked test replicas.
4. Run discovery, lock the signature, and evaluate the untouched simulation test.
5. Build the simulation-only dataset and dataset card with exact lineage.
6. Release positive, null, or failed-discrimination outcomes under the same contract.
