# H2b delegation transmission

## Question

Does shared AI delegation widen correlated behavior across investors and capital when execution is
partial, delayed, or noisy?

## Design

Exp-004 sweeps delegation share while holding pairwise convergence at the verified investor anchor
and total capital fixed. Exp-014 passes frozen AI recommendations through prespecified compliance,
latency, and sizing-noise models. Direct AI execution, no AI advice, and zero-delegation conditions
remain distinct controls. Exp-014 does not consume exp-013 participant results.

## Estimands, units, and controls

Estimate capital-weighted convergence breadth and recommendation-to-execution transmission curves.
Independent units are separately initialized simulation replicas spanning their share or compliance
conditions; seeds are nested unless they generate the replica. Reconcile recommendations, orders,
capital, pairwise convergence, and cohort breadth in every block.

## Failure rules and limits

Failure to hold pairwise convergence or total capital fixed, incomplete share blocks, or failed
recommendation-to-execution reconciliation prevents a verdict. Simulated execution noise does not
measure human trust, current delegation, actual exposed capital, or real-market effects.

## Execution sequence

1. Verify the matched-investor anchor and freeze the delegation and compliance grids.
2. Freeze executor noise, recommendation inputs, independent units, and inference.
3. Gate any model-output generation, compute, spending, and release rights.
4. Run exp-004 before exp-014 and preserve all failed transmissions.
5. Release null and adverse curves under the same simulation-only contract.
