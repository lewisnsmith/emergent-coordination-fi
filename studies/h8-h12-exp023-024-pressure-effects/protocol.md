# H8 and H12 pressure effects

## Question

How do fictional stakes, urgency, emotion, and forced action change decision quality and safety,
and which measured evidence-use, risk, confidence, or abstention pathways reproduce in held-out
frames?

## Design

Exp-023 crosses stakes, urgency, emotion, and forced action in the frozen 3 by 2 by 2 by 2 design
with invariant evidence and output schemas. Exp-024 opens secondary frames, prompts, and models only
after exp-023 and the exp-016 attribution release are locked. Corrective prompts, semantic controls,
negative-control frames, and invariant fictional safety language are required.

## Estimands, units, and controls

Estimate factorial main and interaction effects on quality, suitability, safety, risk, abstention,
and convergence, then held-out frame and prespecified pathway effects. Independent units are
non-overlapping windows or trajectories within randomized model-treatment blocks and held-out
window-model-prompt-family blocks. Freeze TOST equivalence, safety noninferiority, Holm correction,
and nested response handling.

## Failure rules and limits

Missing cells, evidence drift, provider drift, invalid assignment hashes, or failed safety controls
blocks a verdict. Nonsignificance is not equivalence. Frames do not imply that models experience
emotion or stakes. Measured pathways are not formal mediation or activation-level mechanisms.

## Execution sequence

1. Verify exp-016 and freeze metrics, treatments, invariance checks, units, and inference.
2. Implement and verify the 24-cell assignment and provider-control pipeline.
3. Gate calls, spending, protocol execution, and release rights.
4. Run and lock exp-023 before opening any exp-024 held-out material.
5. Run exp-024 without retuning and report pressure, safety, and pathway claims separately.
6. Release positive, equivalent, unsafe, null, and failed-held-out outcomes identically.
