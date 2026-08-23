# H1 and H3 replay model convergence

## Question

Under matched market information and cohort ecologies, do LLM and classical agents converge
differently, and is convergence stronger within the same model or provider lineage?

## Design

Exp-000 must first separate known-convergent mocks from heterogeneous and random controls. Exp-001
and exp-002 run paired equity and resolution-safe prediction-market replay. Exp-005 balances
same-model, same-provider/different-model, and cross-provider pairs. Exp-009 tests only the locked
H1/H3 effects across held-out harnesses, memory conditions, regimes, and semantic paraphrases.

## Estimands, units, and controls

Primary estimands are paired run-level chance-corrected agreement and balanced model-pair
contrasts. Independent units are non-overlapping windows, contracts, or independently generated
trajectories; response seeds are nested. Classical, heterogeneous, and random cohorts, common
random numbers, hidden outcomes, identical information, and provider-balanced exposure are frozen
controls. Use cluster-aware intervals, preregistered multiplicity control, and locked equivalence
margins for robustness.

## Failure rules and limits

Calibration failure stops provider-backed replay. Resolution leakage, unresolved model identity,
imbalanced pair exposure, or incomplete top-level blocks prevents the affected verdict. Convergence
does not establish correctness, coordination, returns, or behavior outside the sampled panel.
H4-specific robustness belongs to the profile-information branch.

## Execution sequence

1. Resolve data rights and freeze models, provider lineages, prompts, harnesses, and units.
2. Implement and pass exp-000 offline calibration.
3. Preregister contrasts, uncertainty, equivalence, and multiplicity.
4. Gate any acquisition, provider calls, compute, spending, and release rights.
5. Run replay and pair contrasts, then open held-out exp-009 blocks without retuning.
6. Release positive, null, negative, and non-equivalent results under one contract.
