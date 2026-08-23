# H8 exp-017 mechanistic convergence

## Question

In one frozen open-weight model, does a causal residual-stream intervention change decision
convergence across equivalent prompts, and does that change alter displacement in a paired
synthetic exchange?

## Design

Pin `Qwen/Qwen3-4B-Instruct-2507` at revision
`cdbee75f17c01a7cc42f958dc650907174af0554`. Use FP16, batch size one, direct hooks, eight discovery
trajectories, 24 untouched confirmation trajectories, 12 states per trajectory, and five frozen
prompt renderings. Score `BUY`, `SELL`, and `HOLD` deterministically and require clean/counterfactual
token alignment.

Scan the final-position residual stream at layers 4, 8, 12, 16, 20, 24, 28, and 32. Freeze one site
by discovery action-margin recovery. Confirmation includes forward and reverse patching,
discovery-mean ablation, sham patching, seeded random-layer control, and norm-matched noise.

## Estimands and controls

The primary endpoint is active-minus-sham change in mean pairwise Cohen's kappa, reduced to one
effect per confirmation trajectory. Use 10,000 seeded block-bootstrap resamples. Feed active and
sham orders into identical one-step books; absolute end-of-step displacement in basis points is the
synthetic downstream endpoint.

## Failure rules

Stop below 11 GB available GPU memory. More than 10% incomplete confirmation blocks prevents a
verdict. Mechanism support requires held-out patching and ablation agreement, recovered fraction
above 0.10, controls below the frozen margin, and output-integrity checks. Null and negative results
use the same release contract.

## Limits and publication boundary

This protocol narrows and supersedes the broader exp-017 design at `4016845`. It excludes feature
dictionaries, steering, formal mediation, provider APIs, and real-market claims. Rationales,
attention maps, and probes are not mechanism evidence. Alpha evaluation is a separate study.

## Execution sequence

1. Implement and verify the complete CPU fake-model study.
2. Freeze and hash this protocol before confirmation inspection.
3. Gate checkpoint acquisition, discovery compute, registration, and confirmation compute.
4. Run confirmation and the paired exchange diagnostic without retuning.
5. Rebuild core artifacts twice, verify byte identity, and inspect the rendered report.
