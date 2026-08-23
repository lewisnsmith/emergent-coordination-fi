# H8 and H13 quantization mechanisms

## Question

Where do errors first appear across same-lineage precision conditions, and when do they compound
into different financial decisions, activations, and closed-loop trajectories?

## Design

After exp-025 passes its capability and scoring gates, compare the same checkpoint lineage at
BF16/FP16, GPTQ W8A16, W4A16, and a prespecified W3A16 stress condition. Cross reasoning depth with
gold-prefix and free-running chains, then shadow-state and endogenous-state replay. Activation
patching begins only after behavioral divergence and alignment establish an interpretable target.

## Estimands, units, and controls

Estimate precision-by-depth changes in conditional step-error hazard, chain survival, activation
drift, decision divergence, and trajectory divergence. Independent units are held-out task families
or market blocks by checkpoint; tokens, steps, and rollouts are nested. Controls include identical
weight lineage, tokenizer, prompt, seed, executable prefixes, sham quantization, random-layer
patches, negative-control tasks, TOST/noninferiority, and hierarchical intervals.

## Failure rules and limits

Lineage or quantizer mismatch, failed step reconciliation, invalid gold prefixes, alignment
failure, or missing held-out replication blocks the mechanism claim. Activation drift alone is not
causal evidence. Full precision identifies quantization loss only within one checkpoint lineage.

## Execution sequence

1. Verify exp-025 and freeze paired checkpoint, quantizer, task, scorer, prompt, and split metadata.
2. Benchmark and gate acquisition, GPU compute, storage, spending, and release rights.
3. Run paired precision/depth conditions with gold-prefix and free-run separation.
4. Run shadow-state and endogenous-state replay and reconcile first errors.
5. Gate and run held-out activation interventions only after divergence and alignment pass.
6. Release null, equivalent, divergent, and failed-mechanism results under one contract.
