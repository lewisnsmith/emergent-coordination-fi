# H4 profile and information differentiation

## Question

Does genuine information differentiation reduce decision convergence more than financially relevant
profiles or identity-only wording?

## Design

Exp-006 compares neutral, reciprocal financially relevant, and identity-only matched profiles while
measuring both convergence and suitability. Exp-007 crosses profile sameness with deterministic,
equal-token-budget information partitions. H4-specific held-out profile, information, regime, and
semantic checks live here rather than in exp-009.

## Estimands, units, and controls

Estimate the profile effect and the profile-by-information difference-in-differences. Independent
units are non-overlapping windows or independently generated trajectories within balanced profile
and information blocks; response seeds are nested. Freeze neutral and reciprocal profiles,
identity-only controls, same-profile/same-information cells, equal information budgets, assignment
hashes, factor balance, hierarchical intervals, and multiplicity rules.

## Failure rules and limits

Unbalanced assignments, unequal evidence budgets, failed cutoff hashes, or conflation of identity
wording with financial constraints prevents the affected claim. Profile differences do not imply
population stereotypes, and reduced convergence does not imply better decisions. Results remain
bounded to the reviewed profiles and information partitions.

## Execution sequence

1. Review and freeze the profile registry, suitability rules, and identity-only counterfactuals.
2. Build and verify equal-budget information partitions and balanced assignments.
3. Preregister independent units, interactions, multiplicity, and H4 robustness margins.
4. Gate data, provider execution, spending, compute, and derived-release rights.
5. Run exp-006 and exp-007, then open held-out H4 blocks without retuning.
6. Release every verdict with assignment, balance, suitability, and evidence-hash audits.
