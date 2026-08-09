# Low-Cost Local-Model Fidelity and Trading Simulation

## Idea

Build a cheap, runnable fidelity ladder that tests when smaller open-weight and quantized models
reproduce the financial reasoning, trading behavior, and cohort convergence observed in sampled
frontier models. The same local checkpoints then support activation capture and causal
interventions that closed APIs cannot.

The purpose is scientific as well as practical: learn which behavioral findings survive scale and
precision changes, locate where quantization errors enter long financial calculations, and test
whether those errors wash out or alter later trades and portfolios. A future population simulator
may use the cheapest configuration that passes these gates, but local execution is not itself
evidence of fidelity to a frontier model, person, investor, or market.

## Core question

Under what model-scale, family, precision, reasoning-depth, and feedback conditions do local
models remain behaviorally equivalent to sampled frontier endpoints, and how does error propagate
when they do not?

The useful target is a measured fidelity surface rather than one leaderboard score:

- executable financial-program and terminal-answer accuracy by dependency depth;
- item-level agreement, error-type agreement, calibration, abstention, and constraint failures;
- action, quantity, portfolio, strategy, and within-cohort convergence equivalence;
- first-error position, chain survival, recovery, and downstream numerical or threshold drift;
- shadow-state versus endogenous-state trajectory divergence; and
- latency, energy or GPU time, memory, and dollar cost per verified valid decision.

## Why quantization might work

The decision policy may not need a frontier call at every tick. Many simulated actions have a
small action space, structured state, and limited context. Quantized local models may therefore be
adequate for routine policy proposals, while cached frontier calls are reserved for a held-out
bridge, ambiguous cases, and periodic audits. H13 tests this possibility; it does not assume it.

Quantization is only one source of error.  A 4-bit model may be sufficiently faithful for simple,
well-constrained action selection yet fail on long memory, numerical reasoning, rare events, or
subtle social inference.  A larger unquantized model with a poor persona, state representation,
or feedback model can still produce a worse simulator.

## Error propagation

Let a full-precision checkpoint produce action distribution \(p(a_t \mid s_t)\) and its quantized
version produce \(q(a_t \mid s_t)\). A local divergence \(\epsilon_t = D(p, q)\) matters because the
action changes the next state:

\[
s_{t+1} = F(s_t, a_t, \eta_t).
\]

If the transition is stable/mixing, local policy errors can wash out and long-run distributional
error remains bounded.  If it has feedback, thresholds, contagion, leverage, or a shared order
book, a small early difference can alter later observations for many agents.  In that setting
error is compounded through both time and interaction topology; matching one-step action accuracy
does not guarantee matching trajectories, tails, or causal response.

Measure the propagation directly instead of inferring it from model bits:

| Layer | Check | Failure signal |
|---|---|---|
| Reasoning step | gold-prefix next-step error, first-error hazard, chain survival | a small local probability change flips an operation or value and contaminates later steps |
| Policy | held-out action log likelihood, calibration, constraint violations | wrong or overconfident local choices |
| Individual trajectory | action persistence, switching, memory decay, regret/utility proxies | a plausible first step drifts unrealistically |
| Population | distributional distance, clustering, cross-agent correlations | population collapses into one voice or becomes arbitrary noise |
| System | stylized facts, shock impulse responses, tail/cascade rates | feedback amplifies small policy errors into unrealistic dynamics |
| Counterfactual | ranking and sign stability across interventions | attractive baseline fit that fails under changed conditions |

Use three references that answer different questions. An executable calculator or program defines
financial correctness. A same-checkpoint BF16/FP16 run identifies quantization loss. Cached
frontier outputs define a descriptive behavioral bridge. Agreement with a frontier output is not
correctness, and a local-frontier difference cannot be attributed to quantization.

The primary precision dose response should use one quantizer across BF16/FP16, W8A16, W4A16, and
W3A16 stress conditions for each frozen checkpoint. Weight-plus-activation and KV-cache
quantization are separate later experiments. Record weights and tokenizer revisions, quantizer,
group size, calibration corpus, clipping, kernels, prompts, decoding, seeds, and hardware.

## Reducing accumulated error

1. **Give agents a compact causal state, not a giant transcript.** Maintain typed memory for
   holdings/resources, beliefs, objectives, commitments, recent observations, and social links.
   Retrieve only decision-relevant history.  This improves both quality and inference speed.
2. **Constrain the action interface.** Require structured actions, valid quantities, budgets,
   latency, and hard risk/role rules.  Use deterministic accounting and a market/social transition
   engine outside the model.
3. **Train/calibrate for behavior, not prose.** Fine-tune or distill on decision traces and
   conditional action distributions; calibrate sampling and persona weights to held-out moments.
   Do not optimize only for plausible rationales.
4. **Preserve diversity deliberately.** Use a mixture of model families, quantization levels,
   personas, information sets, memory horizons, and latent policy seeds.  Track collapse and
   pairwise correlation; temperature alone is not meaningful heterogeneity.
5. **Use hierarchical fidelity.** Run inexpensive 4–8 bit models for routine steps; escalate an
   uncertain, high-impact, out-of-distribution, or disagreement case to a stronger model; cache
   the answer and optionally distill it back into a local policy.
6. **Control feedback.** Introduce short receding horizons, conservative position/impact limits,
   periodic re-anchoring to observed distributions, and ensemble rollouts.  These do not make the
   system "true," but make divergence measurable and contained.
7. **Validate tails separately.** Rare panics, runs, coordinated exits, and manipulation are the
   cases where compounding error matters most.  Overweight them in evaluation but never invent a
   calibration claim from synthetic examples alone.

## Minimal architecture

```text
scenario + observed/calibrated data
              |
      population builder (roles, goals, priors, network)
              |
  per agent: typed state -> quantized policy -> structured stochastic action
              |                                  |
              +---- deterministic market/social transition engine ----+
                                     |
                         logs, metrics, replay, calibration
                                     |
                 optional high-fidelity adjudicator / API escalation
```

The language model supplies a policy proposal, not the simulator's truth layer.  State updates,
matching, accounting, constraints, and random draws live in ordinary code.  All random draws must
be seedable for exact replay, even when the simulated action policy is intentionally stochastic.

## Cheap deployment shape

**Local-first runner.** Put llama.cpp/vLLM-compatible checkpoints behind the same frozen policy
interface. Batch independent chains, batch gold-prefix scoring, cache rendered prompts, and start
pipeline discovery on 2B–9B models. Promote a 27B–32B checkpoint only after the precision screen
shows that the larger cell can resolve an uncertainty that the small cells cannot.

**Paid API/MCP option.** Expose the same interface through an MCP server with tools such as
`create_population`, `run_rollouts`, `inspect_trace`, `compare_quantization`, and
`calibrate_to_targets`.  The server accepts a provider key supplied by the user, enforces a run
budget before calls, uses a local cache, and escalates only selected decisions to a paid model.
It should return provenance and cost fields with every result, never silently make open-ended API
calls, and keep a fully offline mock/local mode for reproducibility.

**Cost levers.** The biggest savings are usually fewer model calls (event-driven decisions,
batched agents, cached repeated states, and longer deterministic intervals), shorter typed
contexts, local quantization, and selective escalation—not merely pushing bit width lower.

## Customization output

Local checkpoints make targeted customization possible, but the base study should first measure
whether quantization itself attenuates sensitivity to client facts. Apply paired interventions to
risk capacity, horizon, liquidity, dependents, tax constraints, mandate limits, and information
access, then compare each model's profile-response vector, suitability, constraint compliance, and
convergence. This yields a reusable map of which local configurations retain meaningful
personalization rather than merely matching average frontier behavior.

Prompt/state customization is the first extension because it leaves weights fixed. LoRA,
fine-tuning, distillation, or selective mixed precision comes later as a separately labeled
treatment after the base precision effect is frozen; otherwise adaptation and quantization are
confounded. Candidate mitigations should be trained only on discovery blocks and evaluated on
untouched domains, profiles, and model families.

## Staged experiment sequence

| Stage | Minimal work | Stop/go gate |
|---|---|---|
| Offline scoring calibration | Fresh executable finance chains at depths 2, 4, 8, and 16; deterministic oracle; duplicate reference loads | Oracle execution and trace alignment pass before any model comparison |
| Local precision screen | Two independent open families, two useful size tiers, BF16/W8/W4 plus W3 stress; 25–50 paired items per depth cell | Expand only around informative precision cliffs and unresolved intervals |
| Frontier bridge | Two frontier families and two local finalists on about 384 held-out chains plus a short replay; cache every response | Continue only if equivalence or a material difference can be resolved within the frozen margins |
| Confirmation | 24–32 independent template, company/document, or market clusters, with a blinded cap near 48 if power simulation requires it | Frozen superiority, equivalence, noninferiority, and multiplicity rules pass |
| Mechanistic funnel | Coarse activation scan on matched concordant and first-divergence cases, then freeze a few layers/features for two-direction patching | Activation work proceeds only after a behavioral precision effect or a strong equivalence question exists |

For each financial chain, run three paired modes: gold-prefix scoring to isolate the conditional
next-step error; free-running execution to measure cascading and recovery; and single-error
injection at early, middle, and late positions to estimate amplification. In trading replay,
compare a common shadow portfolio with endogenous portfolios and reset horizons of 1, 5, 20, and
all steps. The difference estimates state-mediated amplification inside replay.

A useful first API bridge is roughly 384 chains × 2 frontier endpoints, two extra repeats on 10%
of items, and 12 short replay blocks × 30 steps × 4 agents × 2 endpoints: about 3,800 API
calls. That is about 97% below the existing 112,800-decision full-program API pilot assumption.
Run the broad precision ladder locally, generate each frontier reference once, and expand only
after an interval-width gate. Begin mechanistic discovery with a 24 H100-hour cap and authorize an
approximately 80-hour confirmation cap only after the behavioral gate passes.

## Success criterion

The project succeeds if it maps where a low-cost configuration is equivalent, noninferior, or
materially different on frozen financial, behavioral, convergence, safety, and trajectory margins;
replicates the result on held-out domains or model families; and reports the cost per verified
chain and decision. Nonsignificance is not equivalence. Convincing prose, final-answer accuracy
alone, or one open checkpoint cannot establish fidelity or a general mechanism.

## Open decisions

- Which two open families have licensed immutable checkpoints at two useful sizes and a genuine
  BF16/W8/W4 ladder, rather than only a native low-precision release?
- Which H13 confirmation domains should be held out entirely: financial topic, template generator,
  company/document, model family, or all four in separate transport tests?
- What final equivalence margins are scientifically meaningful for program accuracy, κ, regret,
  hard constraints, and profile-response vectors?
- Should the first customization extension test profile facts and information access, or defer all
  fine-tuning/LoRA work so model adaptation cannot confound the base precision result?
