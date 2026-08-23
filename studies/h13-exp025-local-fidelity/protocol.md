# H13 local behavioral fidelity

## Question

Which lower-weight local models preserve sampled frontier behavior on frozen financial reasoning,
trading actions, quantities, and within-cohort convergence?

## Design

Pair executable financial-chain tasks and held-out replay windows across immutable local checkpoint
families and scales, plus frontier endpoints only if separately authorized. Deterministic scoring
keys measure verified answers, error types, actions, quantities, convergence, and cost per valid
decision. Equivalence is evaluated only after a frozen task-capability gate passes.

## Estimands, units, and controls

Estimate capability-conditioned equivalence and deviation by checkpoint family and scale. The
independent unit is a held-out task family or non-overlapping replay window paired across model
conditions. Controls include executable scoring keys, frozen prompts and harnesses, matched
information, paired seeds, local checkpoint hashes, and explicit equivalence margins.

## Failure rules and limits

Scoring failures, checkpoint drift, pairing gaps, capability-gate failure, or unresolved output
rights prevents the affected comparison. Frontier resemblance is not correctness. Results do not
identify quantization loss and do not generalize beyond sampled tasks, families, and endpoints.

## Execution sequence

1. Build tasks and freeze executable scoring keys before evaluating models.
2. Resolve checkpoint, replay-data, and optional frontier-output rights and costs.
3. Freeze model identities, prompts, harnesses, seeds, splits, and equivalence margins.
4. Gate acquisition, optional calls, GPU compute, spending, and release rights.
5. Apply the capability gate, then run paired held-out equivalence evaluation.
6. Release supported, rejected, inconclusive, and capability-gate failures identically.
