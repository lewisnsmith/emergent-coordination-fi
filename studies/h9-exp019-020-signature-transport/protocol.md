# H9 signature transport and detection

## Question

Do locked simulation signatures transport to unseen regimes and real-market windows, and where do
calibrated AI-like patterns appear without causal interpretation?

## Design

Exp-019 applies the immutable exp-018 signature to held-out simulation regimes and non-overlapping
real-market windows. Exp-020 may begin only if the frozen transport gate passes; it emits calibrated
AI-like pattern scores using the same feature set. Negative-control periods, calibration windows,
domain-shift flags, and false-positive audits remain fixed.

## Estimands, units, and controls

Estimate out-of-domain discrimination and calibration change, then the prevalence of calibrated
AI-like patterns. The independent unit is a non-overlapping held-out market window; feature rows
and events are nested. Use window-cluster intervals, temporal separation, locked features,
negative-control periods, and domain-shift sensitivity.

## Failure rules and limits

Failed transport stops exp-020. Feature drift, temporal leakage, unresolved rights, severe
unmodeled domain shift, or failed calibration blocks detection release. Pattern resemblance does
not establish AI presence, exposure, coordination, or causation; exp-020 does not answer H10.

## Execution sequence

1. Verify the immutable signature release and freeze eligible domains and windows.
2. Resolve market-data lineage, transformations, lawful use, and release rights.
3. Freeze transport, domain-shift, calibration, and false-positive rules.
4. Run exp-019 and evaluate its gate without changing the signature.
5. Run exp-020 only after the gate passes, preserving all domain warnings.
6. Release transport failure or noncausal detection results under the same contract.
