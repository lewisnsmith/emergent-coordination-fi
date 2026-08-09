# Mechanistic Interpretability

H8 asks what supplied information causally changes a model's investment decision and, for local
open-weight models, which internal computations mediate that change. H12 additionally asks why
pressure framing changes quality, safety, risk, abstention, or convergence. H13 asks whether
quantization changes those computations and whether a mechanism motif transfers across precision,
scale, and independently trained model families.

The repository intentionally implements two different evidence lanes:

- API/local black-box input interventions in
  [`interpretability/black_box.py`](../../src/flock/interpretability/black_box.py); and
- internal activation interventions for hookable local checkpoints in
  [`interpretability/local_hooks.py`](../../src/flock/interpretability/local_hooks.py).

Hashed tensor artifacts are written by
[`interpretability/artifacts.py`](../../src/flock/interpretability/artifacts.py). The study
contracts are `exp-016`, `exp-017`, `exp-024`, and `exp-026` in
[`configs/research-program.yaml`](../../configs/research-program.yaml).

## Evidence boundary

| Method | Can support | Cannot support |
|---|---|---|
| Generated rationale | What the model emitted as an explanation | Which facts or activations actually caused the output |
| API black-box intervention | Causal effect of changing a supplied input on this model/API behavior | Claims about hidden weights, layers, features, or thought process |
| Local activation intervention | Causal role of an internal activation in a hookable checkpoint on tested examples | Transfer to a closed API or other checkpoint without replication |
| Same-checkpoint precision contrast | Causal behavioral effect of the frozen quantization procedure on that checkpoint | Effect of model scale, training data, architecture, or a frontier/local difference |
| Correlation/probe/attention map | Predictive association useful for discovery | Mechanism without an intervention |

Rationale is not mechanistic evidence. Chain-of-thought must not be requested or treated as a
faithful internal trace. Store only the concise auditable decision summary required by the response
contract.

## Questions and estimands

| Question | Estimand | Independent unit |
|---|---|---|
| Which supplied facts change trades? | Paired output change under a one-feature mask or replacement | Observation-prompt-model intervention block |
| Which facts receive greatest decision weight? | Standardized, preregistered intervention effect with uncertainty | Independent intervention block, not feature rows |
| Does pressure change evidence use? | Difference-in-differences: feature effect under pressure minus neutral | Market/prompt/model block containing both conditions |
| Which internal sites mediate a change? | Recovery or loss of target behavior under patch/ablation | Observation-checkpoint-intervention-seed block |
| Is output convergence also mechanism convergence? | Cross-agent similarity of confirmed causal feature effects | Held-out block after feature confirmation |
| Where does quantization-induced reasoning divergence begin? | Precision-by-depth change in step-error hazard plus behavioral recovery under BF16↔quantized patches | Held-out financial-template/checkpoint block |

Outputs include action probability or target score, signed/absolute quantity, position-size change,
abstention, normalized regret, constraint compliance, and confidence calibration. A causal input
effect is not automatically beneficial; report quality and safety alongside magnitude.

## Lane A: closed-API black-box attribution

Closed APIs expose prompts and outputs, not valid internal activations. Use paired counterfactual
observations while holding model revision, task/profile text, harness, market outcome, response
contract, and randomization block fixed.

The intervention catalog should include:

- remove or replace news while preserving evidence budget;
- shorten one symbol's history without changing the current price;
- change one client fact such as liquidity, horizon, dependents, or risk capacity;
- perturb signal values within valid synthetic ranges;
- change evidence order or salience without changing content;
- apply sham masks and semantically neutral rewrites; and
- include negative-control fields that should not influence suitability.

Interventions must alter one declared feature family at a time and write a before/after hash audit.
Feature removal must not accidentally disclose the treatment through formatting, token count, or
missing-field wording. Replacement values need support overlap; extrapolative interventions are
reported separately.

The current code is a scaffold, not a complete attribution runner. `intervention_observation()`
currently supports `news` removal and `symbol_history:<symbol>` shortening. `paired_attribution()`
computes a paired mean from equal control/intervention score lists and requires at least two blocks;
the caller must preserve and validate block IDs. Expanding client-fact, order, salience, and value
interventions remains required before `exp-016` is executable.

Primary inference uses block-level paired randomization with Holm correction by frozen feature
family. Discover candidate features on one split; confirm selected features on untouched market
windows and, where possible, unseen model releases. Repeated calls characterize response variance
inside a block and are not independent attribution evidence.

Allowed claim example:

> Removing supplied news changed the tested API model's mean trade score by E on held-out blocks.

Prohibited claim example:

> The API model's hidden news neuron caused the trade.

## Lane B: local open-weight mechanisms

Internal claims require a licensed, locally runnable checkpoint with a frozen weights hash,
tokenizer revision, precision/quantizer metadata, inference stack, and hookable forward pass. H8's
frontier-mechanism claim still requires a frontier-eligible checkpoint; H13 may use smaller
checkpoints, but labels the resulting mechanism by exact family, size, and precision. An
OpenAI-compatible HTTP endpoint is insufficient by itself because it does not expose or patch
activations.

The current `HookableLocalModel` contract requires:

- `capture(prompt, layers)` to return activations by layer; and
- `score_with_patch(prompt, patches, target)` to score a specified target with interventions.

`activation_patch()` captures clean activations, inserts them one layer at a time into the treated
run, and reports clean, treated, patched, and recovered-fraction scores. This proves only that the
patched activation at that site causally changes the chosen target under the adapter and example.

The confirmatory sequence is:

1. Freeze clean/treatment prompt pairs and behavioral targets.
2. Discover candidate sites using causal tracing, probes, sparse features, or gradients on a
   discovery set.
3. Freeze layers/features before confirmatory outcomes are inspected.
4. Patch clean↔treated activations in both directions.
5. Ablate and, where scientifically justified, steer the candidate feature.
6. Run sham patches, random-layer/feature controls, negative-control tokens, norm-matched noise,
   and position controls.
7. Replicate on held-out observations, regimes, profiles, and seeds.
8. Verify that the intervention changes the decision target without broadly corrupting output,
   parsing, or constraint compliance.

A mechanism is “causally supported” only if directional patching and ablation/steering agree on
held-out examples, exceed the frozen SESOI, pass intervention-family correction, survive sham
controls, and reproduce from the saved checkpoint/artifact hashes. Association-only findings are
labeled candidate mechanisms.

## H13 precision mechanisms and transfer

Mechanistic work follows the behavioral screen; it does not begin with an unconstrained dump of
every layer and token. Select both matched-concordant cases and cases whose first error location was
established without using the mechanistic confirmation split. For each same-checkpoint BF16/W8/W4
pair:

1. run gold-prefix scoring to locate the first operation or value whose probability margin changes;
2. measure same-tokenizer logit, residual-stream, MLP-gate, and available SAE-feature drift by
   normalized layer depth and step position;
3. patch BF16 activations into the quantized run and quantized activations into BF16 at the frozen
   sites, targeting the next operation, terminal financial answer, and threshold-crossing trade;
4. ablate or steer the candidate feature/subspace and compare with sham, random-layer,
   position-matched, and norm-matched-noise controls; and
5. confirm on untouched task generators, profiles, regimes, and an independently trained family.

Gemma 2 is a cheap discovery candidate because Gemma Scope supplies pretrained sparse
autoencoders across useful sizes. Those autoencoders must first pass reconstruction and delta-loss
checks on each quantized activation distribution; applying a BF16 SAE to W4 activations is not
automatically valid. If fused quantized serving kernels cannot be hooked, a hookable reference
implementation must demonstrate target-logit and output parity with the deployed runtime before
its activations can explain deployment behavior.

Broader transfer requires three gates: aligned representations, a frozen intervention that moves
the homologous target, and behavioral recovery on held-out examples. Replication in two families
supports a repeated motif in those families; a general claim about open models should preferably
use at least three independently trained families and a family-level synthesis. No local result
directly establishes a mechanism in a closed frontier API.

## H12 pressure mechanisms

Use the 24-cell pressure design to derive clean contrasts such as neutral/routine/hold-allowed
versus fictional-life-or-death/immediate/distressed/must-trade. First establish the behavioral
effect. Then test preregistered mediators:

- action bias and abstention suppression;
- evidence breadth and evidence-feature weight;
- liquidity/risk-constraint attention;
- loss/threat/urgency feature activation;
- confidence and unsupported certainty; and
- action-selection activations after evidence integration.

Causal mediation requires treatment before mediator intervention before output, no post-treatment
selection of examples, and explicit sensitivity to mediator-outcome confounding. A rationale saying
“I traded because it was urgent” is not mediation evidence.

## Practical thresholds and multiple testing

Freeze target-specific SESOIs before confirmation. Recommended defaults are 0.10 standardized
target-score change, 0.05 absolute action/abstention probability, or 0.10 recovered fraction for an
activation patch, with a +0.01 adverse noninferiority margin for fabrication or hard-constraint
failure. Null claims require TOST against a frozen equivalence band; nonsignificance is not evidence
that a feature is unused.

Black-box feature families and local intervention families receive separate Holm corrections in
confirmation. Discovery maps use false-discovery-rate control and may not be relabeled
confirmatory. Layer, token, head, sparse feature, target, direction, and prompt family all count
toward the declared multiplicity family.

## Exact outputs

`exp-016` writes:

- `input_interventions.parquet`: block, feature, control/treatment hashes and scores;
- `causal_input_attributions.parquet`: paired effects, intervals, multiplicity, and margins;
- `input_attribution_verification.json`: one-factor, sham, balance, and held-out checks.

`exp-017` writes:

- `activation_traces_manifest.json`: checkpoint/tokenizer/runtime and trace hashes;
- `intervention_effects.parquet`: site, intervention, target, block effect, and controls;
- `mechanisms.json`: supported/candidate/rejected status with claim boundary;
- `mechanistic_verification.json`: artifact, sham, correction, and replication verdicts; and
- per-artifact `activations.npy` and `manifest.json` files from `write_mechanism_artifact()`.

`exp-024` writes `h12_mediation.parquet` and `h12_mechanisms.json`, linked to the frozen H12
behavioral effect rather than rationale text.

`exp-026` writes:

- `h13_step_transitions.parquet`: gold-prefix/free-run first-error and recovery rows;
- `h13_chain_survival.parquet`: block-level precision×depth effects and intervals;
- `h13_trajectory_divergence.parquet`: shadow/endogenous/reset-horizon propagation;
- `h13_mechanism_transport.json`: candidate/supported/rejected mechanism motifs by family; and
- checkpoint, quantizer, calibration, runtime, prompt, activation, and intervention hashes linked
  to every reported effect.

## How users verify and see results

There is not yet an interpretability CLI or complete `exp-016`/`exp-017`/`exp-026` runner; all
three experiments remain scaffolded. The implemented utility contract is tested with:

```bash
uv run pytest tests/test_interpretability.py
```

Users verify tensor integrity by hashing `activations.npy` and matching `tensor_sha256`, shape,
checkpoint hash, prompt hashes, intervention, and layers in its adjacent `manifest.json`. The final
report should display feature-effect forest plots, evidence-weight shifts, layer×token causal maps,
patch/ablation control distributions, model/profile heterogeneity, and held-out replication. Every
visual point must resolve to `input_interventions.parquet` or `intervention_effects.parquet` and a
specific independent block.
