# Local-first execution, costs, and risk roadmap

**Status: ACTIVE personal-budget staging plan. Last consolidated: 2026-08-12.** The default
personal envelope is about `$2,000` for hardware and `$200–300` total direct spend across
software, data, and API use. No paid provider call, hardware purchase, credit purchase, or
research execution is authorized merely because it appears here.

The configured publication program remains H1/H3/H4 first, H2 descriptive, H5 separate, and
H2b/H6–H13 future. The affordable execution lane begins with H13/H8 and can apply for OpenAI
and Anthropic research credits. Credits expand replication or the frontier bridge; they do not
change evidence standards, justify private-profit framing in an application, or remove direct
spend caps without a new decision.

## Controlling rules

- Cost may stage, defer, cap, fund, or substitute qualified external evidence. It may never
  delete a hypothesis.
- The public-dataset, owned-alpha, and validated-risk outputs are coequal and keep separate
  estimands, verdicts, and evidence.
- A paper substitutes for owned collection only under the
  [evidence-substitution contract](research-scope-outcomes-and-evidence.md#evidence-substitution).
- Local-to-frontier similarity, same-checkpoint quantization loss, and financial correctness
  answer different questions and are never pooled.
- The financial scoring key is deterministic executable code and frozen intermediate values,
  not another model or a trading signal.
- Historical cost scenarios below are planning records, never current authorization.

## Decision and scope

Use a local-first execution order that fits a personal hardware ceiling of about $2,000 and a
software, data, and direct API ceiling of about $300. Research credits are optional upside and are
not required for the local program to start.

This plan changes staging, not the hypothesis registry. H1–H13 and H2b remain recorded. The first
owned empirical emphasis becomes H13 and the open-model portion of H8: local-to-frontier behavioral
fidelity, same-checkpoint quantization effects, error propagation, and targeted mechanistic
interventions. H1/H3/H4 frontier factorials, H5 shared-market work, and H9–H11 real-market products
remain connected follow-on lanes. Human-subject and real-market causal-attribution work remains
deferred until its external requirements exist.

The canonical repository still identifies H1/H3/H4 as the proposed first paper. This document is
the budget-constrained execution plan requested before those study and budget configurations are
reconciled. Do not call H13 the canonical first paper until that reconciliation is reviewed and
recorded.

Do not treat this plan as authorization to buy hardware, call a provider, trade real money, or
claim a completed study. Each paid or externally consequential stage keeps its own stop/go gate.
## Budget boundary

| Resource | Working ceiling | Planned use |
|---|---:|---|
| Existing workstation | already owned | 64 GB system RAM, RTX 2080 Ti, offline calibration, small-model and quantized screens |
| Hardware acquisition | about $2,000 | Prefer one tested 24 GB CUDA GPU after the existing-rig benchmark; reserve room for storage, power, and cooling |
| Software, data, and direct API spend | $200–300 | A bounded provider canary, temporary market-data access only if needed, and backup/storage support |
| OpenAI research credits | not assumed | A held-out OpenAI frontier bridge if awarded |
| Anthropic research credits | not assumed | A held-out Anthropic frontier bridge if awarded for an eligible safety/alignment scope |

The current purchase candidate is a used RTX 3090 24 GB if it passes a stress test and the system
passes a PSU, connector, slot, case, and thermal audit. Do not buy it before measuring the current
rig. Do not spend the hardware ceiling merely because it exists. A 24 GB GPU is useful because it
can support same-checkpoint BF16-versus-quantized comparisons on useful small-model tiers; raw
inference speed is secondary to that identification gain.

Use open-source software wherever possible. The core stack should not require paid desktop AI
subscriptions. Large full-precision checkpoints and broad activation sweeps remain cloud- or
credit-contingent.
## Measurement contract

Three references answer different questions. None replaces the others.

| Reference | What it is | Question it answers | What it cannot establish |
|---|---|---|---|
| Financial scoring key | Executable program and frozen intermediate values for a financial task | Is a generated step or final answer financially correct? | Whether a local model behaves like a frontier model |
| Same local checkpoint at BF16 or FP16 | The higher-precision version of the exact checkpoint used in the precision ladder | Did quantization change this checkpoint's behavior or internal state? | Whether either precision matches a frontier model or market |
| Cached frontier outputs | Frozen responses from sampled OpenAI and Anthropic endpoints on the same held-out inputs | Does a local configuration preserve sampled frontier behavior, decisions, and convergence? | Ground-truth correctness or a causal quantization effect |

The financial scoring key is not a competing model and does not need to cover every trading
decision. It is the answer key for tasks with verifiable calculations. Without it, two models can
agree and both be wrong, or disagree without revealing which result is correct.

The local precision experiment includes both comparisons:

- Compare W8, W4, and W3 with the same local checkpoint at BF16 or FP16 to identify quantization
  effects.
- Compare the selected local configurations with cached frontier outputs to measure behavioral
  fidelity.

For example, an executable task may establish that a covenant ratio is `2.4`. If local BF16
produces `2.4` and local W4 produces `2.1`, the paired checkpoint comparison identifies a
quantization-associated error. If a frontier endpoint and the local model both produce `2.4` but
choose different trades, the scoring key says both calculations are correct while the frontier
bridge records a behavioral difference. These are separate findings.
## Execution stages

### Audit external evidence

Compare every candidate external result with the measurement contract and assign its permitted
use. Reuse robust public tasks, executable programs, pretrained interpretability tools, and
established statistics where their artifacts pass review.

**Materials:** Literature search log, papers, supplements, code, datasets, model cards, licenses,
and the registered claim boundaries.

**Output:** A versioned evidence matrix with the permitted use, mismatch reasons, artifact hashes,
and the experiment cells that still require owned evidence.

**Gate:** Do not reduce collection until a named artifact passes provenance and comparability
review.

### Benchmark the existing workstation

Run a small, fixed workload on the RTX 2080 Ti before buying hardware. Include a full-precision
small checkpoint, a 7B–9B quantized checkpoint where feasible, activation capture at selected
layers, and a short local-agent replay.

**Materials:** Existing workstation, pinned drivers and libraries, two candidate open families,
fresh scoring-key tasks, and a power/temperature monitor.

**Output:** Throughput, latency, peak VRAM, system-RAM offload, power, temperature, failure, and
cost-per-valid-chain tables plus a hardware purchase decision.

**Gate:** Buy a GPU only if the measured bottleneck prevents a preregistered comparison that the
upgrade can resolve.

### Freeze the financial scoring key

Build or reuse fresh executable financial tasks at dependency depths near 2, 4, 8, and 16. Freeze
the operation sequence, intermediate values, final answer, tolerances, task-family identifier, and
generator seed. Use public real-document tasks as a held-out ecological bridge, not as the sole
identification set.

**Materials:** FinChain-style parameterized templates, an ordinary deterministic calculator,
held-out FinQA or DocFinQA-style documents where licensing permits, and duplicate/contamination
checks.

**Output:** Hashed task records containing executable programs, step-aligned correct values,
tolerances, provenance, and discovery/validation/test assignments.

**Gate:** Every program executes deterministically, trace alignment passes, and no template or
document lineage crosses a prohibited split.

### Run the local precision and fidelity screen

Quantized local policies might be adequate for routine proposals because many simulated actions
have a small action space, typed state, and limited context. That is a hypothesis, not an
assumption. A 4-bit model may work on constrained action selection yet fail on long memory,
numerical reasoning, rare events, or subtle social inference; a larger unquantized model can still
fail because its persona, state representation, or feedback model is poor. Quantization is only
one error source, and H13 must measure the boundary directly.

Run two open families at two feasible size tiers across BF16 or FP16, W8, W4, and W3 stress where
the hardware permits. Use the same tokenizer, prompt, decoding, quantizer family, calibration
corpus, seed, runtime, and hardware within each causal precision contrast.

For each financial chain, run gold-prefix scoring, free-running execution, and a controlled
single-error injection. For each trading replay, compare a common shadow portfolio with an
endogenous portfolio so the analysis can separate one-step disagreement from state-mediated
propagation.

**Materials:** Frozen scoring key, immutable full-precision checkpoints, reproducibly generated
quantized variants, local runner, replay windows, and a completed hardware benchmark.

**Output:** Program and final-answer accuracy, first-error hazard, chain survival, recovery,
calibration, constraint failures, action/quantity disagreement, portfolio divergence,
within-cohort convergence, latency, memory, energy, and cost tables.

**Gate:** Expand only near informative precision cliffs, unresolved equivalence margins, or
material trajectory divergences. Do not spend compute filling cells that cannot change the
conclusion.

### Run the frontier behavioral bridge

Apply the same held-out scoring-key tasks and short replay blocks to one OpenAI and one Anthropic
endpoint, subject to credits or a separately authorized spend cap. Cache each response and record
the exact resolved endpoint, request, tokens, retries, latency, and cost.

Compare the frontier responses with the local finalists on correctness-conditioned agreement,
error type, calibration, actions, quantities, strategy fingerprints, profile response, and
within-cohort convergence. Do not treat frontier agreement as correctness.

**Materials:** Local finalist artifacts, frozen held-out inputs, exact public frontier endpoints,
provider keys, credits or direct authorization, and a small canary.

**Output:** Local-to-frontier equivalence and difference estimates, endpoint-specific failure and
cost records, cached reference outputs, and the cheapest configuration that passes each frozen
margin if one exists.

**Gate:** Stop the bridge at its call and dollar caps. Continue only when independent held-out
clusters can resolve a frozen equivalence or material-difference question.

### Run the mechanistic funnel

Select matched local cases where precision variants agree, first diverge, recover, or produce
different trades. Run a coarse activation scan, freeze a small set of layers or features, and test
two-direction activation patching, ablation, sham interventions, and random-layer controls.

Use pretrained sparse autoencoders or transcoders when their checkpoint and layer match. Treat
their features as discovery candidates until causal interventions pass.

**Materials:** Hookable open checkpoints, matched behavioral cases, activation tools, pretrained
interpretability artifacts where available, storage limits, and frozen intervention sites.

**Output:** Activation-summary manifests, intervention effects, behavioral recovery or disruption,
negative-control results, and a bounded mechanism claim for the sampled checkpoint and precision.

**Gate:** Do not begin a broad activation sweep before a behavioral effect or strong equivalence
question exists. Retain raw tensors only for shortlisted sites and required verification.

### Run local-agent replay and simulated-market discovery

Run the affordable local configurations across model family, precision, profile, information,
prompt, harness, and market regime. Use classical and random cohorts as controls. Escalate only
frozen ambiguous or high-impact cases to cached frontier references.

Discover candidate public signatures from simulated AI/no-AI or local/frontier contrasts, such as
convergence breadth, flow persistence, timing, size discretization, liquidity withdrawal, impact,
volatility, and cascade structure. Split complete trajectory lineages before feature selection.

**Materials:** Verified local configurations, historical and synthetic replay data, classical
baselines, validated simulator components, market replicas, and frozen feature candidates.

**Output:** Decision, fill, portfolio, convergence, strategy, cost, and simulation-signature
artifacts with placebo-label and crowded-classical controls.

**Gate:** A signature must discriminate held-out simulation replicas, remain calibrated, and avoid
mistaking ordinary classical crowding for AI before real-market use.

### Test transport in real markets

Lock the signature library before applying it to unseen market periods. Build the same public
features from a lawful real-market panel, measure domain shift, and estimate calibration only where
labels support it. Preserve the label `ai_like_not_attributed` unless verified exposure and a
credible counterfactual exist.

**Materials:** Locked simulation signature library, real trade/quote or daily feature panel,
corporate-action and timezone handling, negative-control periods, and data licenses.

**Output:** Transport predictions, domain-shift diagnostics, false-positive results, and a versioned
`signature_events.parquet` for observational AI-like patterns.

**Gate:** Failed transport ends real-market use of the signature. Resemblance never becomes AI
exposure or causation.

### Run prospective paper trading

Convert only transport-approved signatures into a small set of frozen trading rules. Specify the
signal transformation, universe, execution time, rebalance cadence, position and turnover limits,
benchmark, fees, slippage, and stopping rules before the prospective window begins.

Run a walk-forward historical evaluation followed by paper trading. Do not tune the rule on the
paper-trading window. Count every tried signal and parameterization in the multiple-testing and
backtest-overfitting record.

**Materials:** Frozen signal rules, held-out historical periods, transaction-cost and slippage
models, benchmark portfolios, a paper-trading API, and an immutable prospective start time.

**Output:** Backtest and prospective order/fill ledgers, gross and net return, turnover, drawdown,
factor exposure, benchmark-relative performance, failed signals, and an explicit verdict of
supported, inconclusive, or rejected.

**Gate:** Paper performance does not authorize live trading. Any later real-money experiment needs
a separate risk, legal, operational, and capital authorization outside this research plan.

### Build the release

Reproduce every eligible artifact from hashes in a clean environment. Separate simulation truth,
AI-like signatures, verified exposure, and causally attributed events. Link each public claim to
its exact estimand, rows, code and data hashes, uncertainty, limitations, and verification status.

**Materials:** Verified upstream artifacts, frozen analysis, source and preregistration commits,
licenses, checksums, schemas, environment lock, and independent review.

**Output:** A manuscript, the H13/H8 fidelity and mechanism datasets, simulation and observational
signature artifacts, the prospective paper-trading ledger, figures, `claims.json`, lineage,
checksums, a dataset card, release verification, and a separate evidence-backed AI-agent trading
risk assessment. Organize the release so the public-dataset, owned-alpha, and validated-risk
verdicts can be read and audited independently.

**Gate:** Missing provenance, leakage, incomplete blocks, failed reproduction, causal-label
inflation, or an unresolved high-priority review finding blocks publication.
## Expected research products

The affordable core can produce:

- A finance-specific same-checkpoint quantization and error-propagation dataset.
- A local-to-frontier behavioral equivalence map conditioned on correctness and task difficulty.
- Targeted causal activation-intervention results on small open checkpoints.
- A reusable library of local-agent decisions, portfolios, convergence, and strategy fingerprints.
- A locked simulation-signature library and, if transport passes, observational real-market
  signature events.
- A prospective paper-trading record that includes failed signals and all tested variants.
- A reproducible paper and artifact release even if the main equivalence, mechanism, transport, or
  alpha result is null.

The personal budget cannot by itself produce a comprehensive multi-provider frontier factorial,
an approved human-subject study, licensed institution-level AI exposure, or a credible causal
attribution of real-market outcomes to AI. Keep those hypotheses visible and blocked or deferred
until the required evidence and authorization exist.
## Immediate next actions

- Reconcile the older first-paper call matrix with this local-first authorization order.
- Label every proposed experiment and artifact with the public-dataset, owned-alpha, and
  validated-risk tracks it serves.
- Build the external-evidence matrix before removing any collection cell.
- Select two open checkpoint families with immutable BF16 weights and reproducible W8/W4 variants.
- Create a fixed existing-rig benchmark before purchasing a GPU.
- Freeze the smallest executable scoring-key dataset needed for that benchmark.
- Draft research-credit applications around truthful economic-impact, generalization, robustness,
  and systemic-safety questions; do not make private trading profit the funded research purpose.

## Local engineering and sample-cap details

### Reducing accumulated error

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
### Minimal architecture

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
### Cheap deployment shape

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

### Provisional H13 caps and paired modes

| Stage | Minimal work | Stop/go gate |
|---|---|---|
| Offline scoring calibration | Fresh executable finance chains at depths 2, 4, 8, and 16; deterministic financial scoring key; duplicate reference loads | Scoring-key execution and trace alignment pass before any model comparison |
| Local precision screen | Two independent open families, two useful size tiers, BF16/W8/W4 plus W3 stress; 25–50 paired items per depth cell | Expand only around informative precision cliffs and unresolved intervals |
| Frontier bridge | Two frontier families and two local finalists on about 384 held-out chains plus a short replay; cache every response | Continue only if equivalence or a material difference can be resolved within the frozen margins |
| Confirmation | 24–32 independent template, company/document, or market clusters, with a blinded cap near 48 if power simulation requires it | Frozen superiority, equivalence, noninferiority, and multiplicity rules pass |
| Mechanistic funnel | Coarse activation scan on matched concordant and first-divergence cases, then freeze a few layers/features for two-direction patching | Activation work proceeds only after a behavioral precision effect or a strong equivalence question exists |

For each financial chain, run three paired modes: gold-prefix scoring to isolate the conditional
next-step error; free-running execution to measure cascading and recovery; and single-error
injection at early, middle, and late positions to estimate amplification. In trading replay,
compare a common shadow portfolio with endogenous portfolios and reset horizons of 1, 5, 20, and
all steps. The difference estimates state-mediated amplification inside replay.

A provisional maximum API bridge is roughly 384 chains × 2 frontier endpoints, two extra repeats
on 10% of items, and 12 short replay blocks × 30 steps × 4 agents × 2 endpoints: about 3,800
API calls. That is about 97% below the existing 112,800-decision full-program API pilot
assumption.

Run the broad precision ladder locally, generate each frontier reference once, and expand only
after an interval-width gate. Begin mechanistic discovery only under its separate 24 H100-hour
authorization; passing the behavioral gate makes an approximately 80-hour confirmation eligible
for separate authorization and never authorizes compute by itself.

## High-cost and externally blocked registry

The conversation did not declare the following questions unimportant:

- A broad multi-provider frontier H1/H3/H4 factorial remains credit- or funding-contingent.
- H5 shared-market thresholds require additional simulator validation and independent replicas.
- H6 human trust and delegation requires ethics review, recruitment, consent, and compensation.
- H7 adoption forecasting requires a verified adoption series and an H5 threshold distribution.
- H9/H10 real-market transport and detection require an acquired market feature panel.
- H10 causal attribution requires verified AI exposure and a credible counterfactual.
- H11 public data products require the release exporter, licenses, and verification gates.
- Broad mechanistic claims beyond sampled open checkpoints require more compute and independent
  family replication.

Keep each item recorded as high cost, blocked, conditional, or deferred. Do not delete it.

Every listed item remains part of the research program. A high-cost, blocked, conditional, or
deferred label records execution status; it never means the hypothesis was cut.

## Working decisions

The conversation established these working decisions:

- Preserve every hypothesis regardless of cost.
- Use a local-first execution order within the stated personal budget.
- Treat research credits as optional and keep direct spend bounded.
- Prefer an evidence matrix over informal decisions about which papers are "good enough."
- Keep financial correctness, quantization causality, and frontier similarity distinct.
- Preserve the public-dataset, owned-alpha, and validated-risk tracks as coequal project outputs.
- Require held-out transport before converting a simulated signature into a trading rule.
- Require prospective paper trading before considering any separate live-capital decision.
- Publish negative and inconclusive results when the design and execution pass verification.

## Unfrozen decisions

The following items remain proposals rather than canonical study decisions:

- Making H13/H8 the first owned empirical paper instead of the configured H1/H3/H4 paper.
- Buying a used RTX 3090 24 GB rather than another GPU or no GPU.
- Selecting the exact two open checkpoint families and two size tiers.
- Selecting the exact OpenAI and Anthropic frontier endpoints.
- Using the provisional 2, 4, 8, and 16 dependency-depth ladder and the current sample allocation.
  The 3,802-call bridge is a provisional maximum planning stop cap unless an outcome-blind,
  separately approved amendment lowers or replaces it before any paid request.
- Selecting equivalence, noninferiority, safety, and material-difference margins.
- Selecting the real-market feature panel, universe, frequency, and paper-trading venue.
- Selecting the prospective paper-trading duration and any later criteria for a separate
  real-money proposal.

Resolve these items through benchmark evidence, power calculations, licensing review, and a frozen
preregistration rather than conversational preference.

## Historical full-program cost scenarios

**Dated basis: 2026-07-13. Funding-contingent and not authorized.** This section preserves the
74,880-call first-paper pilot, 135,360-decision broader pilot, 232,360-call configured study,
$5,200 hardening-era path, and larger full-program estimates as planning history. The current
personal-budget staging above controls. Prices were not refreshed during consolidation.
Legacy seed counts below are workload multipliers, not independent evidence; scientific power
uses trajectories, nonoverlapping windows, or whole-market replicas.

**Pricing verified:** 2026-07-13. All amounts are USD before tax.

This runbook converts the staged research design into API calls, token costs,
GPU hours, storage, and CPU analysis time. It is a planning estimate, not a
vendor quote. Re-run the pilot calibration before authorizing either the base
or high program.

Machine-readable inputs are in:

- `configs/budgets/pricing.yaml` — verified standard-execution prices.
- `configs/budgets/run-matrix.yaml` — low/pilot, base, and high workloads.

### Scope boundary

The run matrix budgets the broader research program, not just the first paper. Every component is
therefore assigned to one of three authorization scopes:

- `first_paper` — H1/H3/H4 MPHIQ and semantic-equivalence work.
- `separate_h5` — the simulator-only AI-capital-share experiment, which is not part of the first
  paper's confirmatory family.
- `future_program` — H6 trust/delegation, H12 prompt pressure, and H13 local-model fidelity work.
  H8/H13 mechanistic GPU work is budgeted separately rather than treated as ordinary decision
  calls.

**Retention rule:** authorization scope and cost never remove a hypothesis from the canonical
program. High-cost work may be staged, deferred, supported through credits, or partly satisfied by
qualified external evidence, but the underlying hypothesis and claim boundary remain recorded.
Removal or substantive merger requires a scientific rationale unrelated to cost and a visible
preregistration amendment. The machine-readable rule and high-cost registry live in
`configs/research-program.yaml`.

| Scenario | First paper | Separate H5 | Future program | Full-program total |
|---|---:|---:|---:|---:|
| Pilot | 74,880 | 11,520 | 48,960 | 135,360 |
| Base cumulative | 4,068,480 | 126,720 | 1,978,560 | 6,173,760 |
| High cumulative | 11,134,080 | 241,920 | 3,908,160 | 15,284,160 |

Authorizing only the first-paper pilot defers 60,480 decisions, or 44.7% of the full pilot.
At the base ceiling it defers 2,105,280 cumulative decisions, or 34.1%. These are call-count
reductions, not final dollar estimates: endpoint mix, retries, fixed compute overhead, and the
deferral of H8 mechanistic GPU work must be recalculated before purchasing credits or compute.

The full-program totals below remain useful as ceilings, but they are not one indivisible study.
External datasets or prior experiments may later reduce bridge or exploratory work; no such saving
is counted here until the artifacts pass provenance and comparability review and the analysis plan
records how they will be used.

#### H13 local-first sidecar

H13 was added after the existing full-program call ceilings were calculated, so its sidecar below
is **not included** in the scenario totals above or in the historical dollar estimates below. Keep
it separate until exact checkpoints, hardware throughput, frontier endpoints, context lengths, and
output caps are benchmarked.

| H13 pilot component | Formula | Workload/cap |
|---|---|---:|
| Local free-running precision screen | 2 families × 2 sizes × 4 precisions × 4 depths × 50 items | 3,200 local chains |
| Local gold-prefix scoring | 2 families × 2 sizes × 4 precisions × 50 items × (2+4+8+16 steps) | 24,000 scored prefixes |
| Frontier financial-chain bridge | 384 held-out chains × 2 endpoints | 768 API calls |
| Frontier repeat sample | about 10% of chains × 2 extra repeats × 2 endpoints | 154 API calls |
| Frontier short replay | 12 blocks × 30 steps × 4 agents × 2 endpoints | 2,880 API calls |
| **Frontier bridge cap** |  | **3,802 API calls** |
| Mechanistic discovery | coarse-to-fine layers/sites after behavioral gate | 24 H100-hours |
| Mechanistic confirmation | frozen sites on held-out blocks/family | 80 H100-hours, separately authorized |

The 3,802-call bridge is about 96.6% below the existing 112,800-API-decision full-program pilot
assumption. It is not powered merely because it has thousands of calls: its evidence comes from
held-out template/document/market clusters. Use 25–50 items per depth cell for local screening,
8–12 discovery clusters for nuisance estimates, and power roughly 24–32 paired confirmatory
clusters with a preregistered blinded cap near 48.

Do not assign a dollar figure yet. First benchmark local token throughput and measure actual
frontier input, visible output, reasoning tokens, retries, and latency on a small authorized canary.
Then multiply the fixed call cap by the selected endpoints' measured usage and add the same spend
abort and contingency rules used elsewhere in this runbook.

### Historical recommendation

Do not buy the whole confirmatory budget up front.

1. The dated scenario proposed authorizing the 74,880-call first-paper pilot first and then
   recalculating its dollar envelope from the selected endpoints. It staged H5, H6, H8, H12, and
   H13 separately without removing their hypotheses.
2. Keep **$2,300** as the ceiling only for the full-program pilot: $1,100 API, $1,000 GPU/VM,
   and $200 CPU/storage.
3. Measure actual provider-specific tokens, parse retries, throughput, and
   exclusion rates. Recalculate every later stage from those observations.
4. If the pre-registered stop/go gates pass, treat **$121,000** as the full-program base
   ceiling: $100,000 API, $20,000 GPU/VM, and $1,000 auxiliary.
5. Treat **$580,000** as a full-program sensitivity ceiling, not as the default plan. It is
   needed only if pilot power analysis requires twenty seeds and the expanded
   robustness battery.

At the 2026-07-13 snapshot, the scoped first-paper pilot was the recommendation. It is not current
authorization. The $2,300 pilot and the base and high figures are historical full-program ceilings:
do not prebuy those credits before scope, pilot power, usage, failure-rate, and throughput
measurements are complete.

The full-program base API split for work performed on or after 2026-09-01 is:

| Provider | Credits/budget |
|---|---:|
| OpenAI | $39,000 |
| Anthropic | $50,000 |
| Google | $11,000 |
| **Total** | **$100,000** |

These rounded amounts include approximately 15% API contingency.

### Cost equations

One LLM decision is normally one model request. A malformed response triggers
one format-repair request, so calls and billable requests are not identical.

```text
decisions = sum(cells * environments * seeds * steps * LLM_agents)

API_decisions   = decisions * 5/6
local_decisions = decisions * 1/6

billable_API_requests = API_decisions * (1 + retry_rate)

API_cost(model) = requests(model)
                * (input_tokens * input_price
                   + output_tokens * output_price)
                / 1,000,000
```

The six endpoints are two OpenAI models, two Anthropic models, one Google
model, and one local open-weight model. They are balanced inside experimental
cells. The six endpoints, 24 personas, and five semantic prompt variants are
not blindly crossed with all 32 MPHIQ schemes.

For Anthropic, the calculation multiplies estimated token counts by 1.30.
Anthropic states that Claude Opus 4.7+ and Claude Sonnet 5 use a tokenizer that
produces approximately 30% more tokens for the same text. This adjustment is
conservative and must be replaced with measured usage after the pilot.

Local serving cost is benchmark-driven:

```text
GPU_hours = generated_tokens / effective_generated_tokens_per_second / 3,600
          + prefill + model_load + idle + orchestration overhead

VM_cost = instance_hours * hourly_instance_price
```

For an eight-GPU instance, `GPU_hours = instance_hours * 8`.

### Official price basis

The executable catalog uses standard synchronous inference and therefore sets
`batch_discount: 0.0`. OpenAI, Anthropic, and Google advertise roughly 50%
Batch/Flex reductions for the listed models, but the current experiment is
sequential: the decision at step `t+1` depends on the portfolio created at
step `t`. A discount must not be budgeted until a wavefront/batch runner is
implemented and verified.

| Endpoint | Input / MTok | Output / MTok | Notes |
|---|---:|---:|---|
| GPT-5.6 Sol | $5.00 | $30.00 | Standard processing |
| GPT-5.6 Terra | $2.50 | $15.00 | Standard processing |
| Claude Opus 4.8 | $5.00 | $25.00 | Plus the tokenizer-count adjustment |
| Claude Sonnet 5 | $2.00 | $10.00 | Introductory rate through 2026-08-31 |
| Claude Sonnet 5 | $3.00 | $15.00 | Announced rate from 2026-09-01 |
| Gemini 3.1 Pro Preview | $2.00 | $12.00 | Output includes thinking tokens |

Official sources:

- [OpenAI API pricing](https://openai.com/api/pricing/),
  [GPT-5.6 Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol), and
  [GPT-5.6 Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra).
- [Anthropic Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing).
- [Google Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing).

The local endpoint assumption is `gpt-oss-120b`. OpenAI describes it as a
117B-parameter, 5.1B-active-parameter MXFP4 model that fits on one 80 GB H100.
See [Introducing gpt-oss](https://openai.com/index/introducing-gpt-oss/) and the
[gpt-oss-120b model page](https://developers.openai.com/api/docs/models/gpt-oss-120b).

| VM shape | Instance price/hour | GPUs | Effective H100 price |
|---|---:|---:|---:|
| Runpod H100 PCIe | $2.89 | 1 | $2.89/GPU-hour |
| CoreWeave HGX H100 | $49.24 | 8 | $6.155/GPU-hour |
| GCP `a3-highgpu-8g` | $88.490000119 | 8 | $11.061/GPU-hour |
| GCP `e2-standard-4` | $0.13402284 | 0 | CPU analysis only |

Sources: [Runpod pricing](https://www.runpod.io/pricing),
[CoreWeave pricing](https://coreweave.com/pricing),
[GCP accelerator VM pricing](https://cloud.google.com/products/compute/pricing/accelerator-optimized),
and [GCP general-purpose VM pricing](https://cloud.google.com/products/compute/pricing/general-purpose).

Runpod is the quoted option that supports a true single-H100 pilot. The quoted
CoreWeave and GCP on-demand shapes contain eight H100s.

### Token and retry envelopes

The current prompt contains a persona/mandate, a 20-bar observation window,
five symbols, duplicated human- and machine-readable market summaries, the
portfolio, events, and structured-output instructions. Reasoning/thinking
tokens can materially exceed the short visible JSON response.

| Case | Input/request | Output/request | Retry rate used |
|---|---:|---:|---:|
| Pilot/low | 1,200 | 150 | 1% |
| Base/expected | 2,200 | 350 | 3% |
| High | 4,000 | 800 | 10% |

The existing model configuration caps completion output at 1,024 tokens. The
high case remains below that cap but allows substantial hidden reasoning. Any
increase in the cap requires a fresh cost estimate.

### Pilot call count

| Component | Calculation | Decisions |
|---|---|---:|
| MPHIQ screen | 32 × 1 environment × 3 seeds × 60 steps × 8 agents | 46,080 |
| Semantic equivalence | 4 schemes × 5 variants × 1 × 3 × 60 × 8 | 28,800 |
| Prompt-pressure fractional screen | 16 cells × 1 × 3 × 60 × 8 | 23,040 |
| Exchange/AI share | 6 shares × 1 regime × 3 × 80 × 8 | 11,520 |
| Trust/delegation | 6 endpoints × 24 personas × 5 variants × 12 vignettes × 3 | 25,920 |
| **Total** |  | **135,360** |

Split: 112,800 API decisions and 22,560 local decisions. At a 1% repair rate,
the budget covers 113,928 API requests.

Estimated standard API cost is **$858.90** through 2026-08-31 or **$916.66**
after the announced Claude Sonnet 5 price change. With contingency, buy about
$1,100 of API capacity.

### Base call count

| Component | Calculation | Decisions |
|---|---|---:|
| MPHIQ confirmation | 32 × 8 environments × 10 seeds × 120 steps × 8 agents | 2,457,600 |
| Semantic equivalence | 4 schemes × 5 variants × 8 × 10 × 120 × 8 | 1,536,000 |
| Full prompt pressure | 24 cells (`3×2×2×2`) × 8 × 10 × 120 × 8 | 1,843,200 |
| Exchange/AI share | 6 shares × 3 regimes × 10 × 80 × 8 | 115,200 |
| Trust/delegation | 6 endpoints × 24 personas × 5 variants × 12 vignettes × 10 | 86,400 |
| **Confirmation increment** |  | **6,038,400** |
| Prior pilot |  | 135,360 |
| **Cumulative total** |  | **6,173,760** |

Cumulative split: 5,144,800 API decisions and 1,028,960 local decisions. Applying
the pilot's 1% retry rate to pilot calls and 3% to confirmation calls produces
**5,296,888 billable API requests**.

Estimated cumulative standard API cost is **$80,463.99** through 2026-08-31
or **$85,844.65** after the Claude price change. The $100,000 API ceiling adds
approximately 15% contingency to the later price and rounds by provider.

### High sensitivity call count

The twenty-seed design replaces the ten-seed base matrix; it is not twenty
additional seeds after completing all ten base seeds. Only the pilot is added
to its total.

| Component | Calculation | Decisions |
|---|---|---:|
| MPHIQ sensitivity | 32 × 8 × 20 × 120 × 8 | 4,915,200 |
| Expanded semantic equivalence | 8 schemes × 5 variants × 8 × 20 × 120 × 8 | 6,144,000 |
| Full prompt pressure | 24 cells (`3×2×2×2`) × 8 × 20 × 120 × 8 | 3,686,400 |
| Exchange/AI share | 6 shares × 3 regimes × 20 × 80 × 8 | 230,400 |
| Trust/delegation | 6 endpoints × 24 personas × 5 variants × 12 vignettes × 20 | 172,800 |
| **Sensitivity matrix** |  | **15,148,800** |
| Prior pilot |  | 135,360 |
| **Cumulative total** |  | **15,284,160** |

Cumulative split: 12,736,800 API decisions and 2,547,360 local decisions.
Stage-specific retries produce **14,000,328 API requests**.

Estimated cumulative standard API cost is **$435,225.50** through 2026-08-31
or **$464,166.97** afterward. Fifteen percent contingency raises the later
case to about **$534,000**; the provider-rounded ceiling is **$536,000**.

### Local inference and mechanistic-interpretability budget

Local serving hours include model loading, prompt prefill, generation, and
idle/orchestration loss. They are deliberately ranges because effective
throughput depends on continuous batching and the final reasoning effort.

| Scenario | Local serving | Mech pilot | Mech confirmation | Total H100 GPU-hours |
|---|---:|---:|---:|---:|
| Pilot | 50–120 | 80–160 on 1 H100 | — | 130–280 |
| Base | 900–2,300 | 80–160 on 1 H100 | 200–500 wall hours on 8 H100s = 1,600–4,000 | 2,580–6,460 |
| High | 3,300–8,700 | 80–160 on 1 H100 | 200–500 wall hours on 8 H100s = 1,600–4,000 | 4,980–12,860 |

At the listed prices, those totals cost:

| Scenario | Runpod | CoreWeave equivalent | GCP equivalent |
|---|---:|---:|---:|
| Pilot | $376–$809 | $800–$1,723 | $1,438–$3,097 |
| Base | $7,456–$18,669 | $15,880–$39,761 | $28,538–$71,456 |
| High | $14,392–$37,165 | $30,652–$79,153 | $55,085–$142,248 |

The CoreWeave and GCP figures are normalized GPU-hour comparisons; their
eight-GPU minimum shapes can create additional idle cost. Mechanistic work on
quantized MXFP4 weights must not automatically be interpreted as equivalent
to BF16/full-precision mechanisms. Confirmatory activation-patching and
causal-tracing results should therefore use the precision stated in the
pre-registration and record it in every artifact manifest.

The H13 24/80-hour funnel supersedes the assumption that an 80–160-hour mechanistic pilot should
start before a precision-related behavioral question is established. The older table remains the
ceiling for the broader H8 program. H13 first streams logit and activation summaries from the local
screen, retains raw tensors only for shortlisted layers/tokens, and makes the 80-hour confirmation
eligible for separate authorization only after frozen behavioral and reconstruction gates pass.

### CPU and storage

Ordinary result records are estimated at 3–8 KB per decision before caches and
backups: roughly 0.4–1.1 GB pilot, 19–50 GB base, and 46–123 GB high. The
rounded reservations are 10 GB, 100 GB, and 500 GB respectively.

Mechanistic activation tensors dominate storage. Temporary reservations are:

| Scenario | Activations | Runpod high-performance storage/month | Analysis VM hours | CPU estimate |
|---|---:|---:|---:|---:|
| Pilot | 0.5 TB | ~$70 | 250 | ~$34 |
| Base | 2 TB | ~$280 | 1,700 | ~$228 |
| High | 10 TB | ~$1,400 | 6,000 | ~$804 |

Stream aggregate statistics and discard raw activations after their hashes,
derived artifacts, and verification checks are complete. Do not retain every
layer × token × prompt tensor indefinitely.

### Stop/go controls

Before expanding beyond the pilot, verify all of the following:

- Provider invoice token counts reconcile with decision-log usage fields.
- Thinking/reasoning tokens are included in the logged output total.
- Parse-repair rates remain within the pre-registered exclusion threshold.
- The local H100 benchmark reports effective throughput at the actual context,
  output cap, reasoning effort, precision, and concurrency.
- H13 same-checkpoint pairs reconcile tokenizer, prompt, quantizer, calibration, runtime, and
  hookable/deployed logits; native low-precision-only weights are excluded from causal precision
  claims.
- The H13 frontier bridge stops at its call and dollar caps; local cells expand only where the
  attainable interval can resolve the frozen equivalence or difference margin.
- Exact model snapshots are available for confirmatory runs. A moving alias or
  preview model is not sufficient for reproducibility.
- Pilot variance and intraclass correlation justify the required number of independent
  trajectories, windows, or replicas. The legacy ten- or twenty-seed workload multiplier does not
  itself define independent evidence, and repeated agent calls are not independent market evidence.
- Every stage has a hard provider spend limit and aborts before exhausting the
  next stage's reserved credits.

### Important caveats and exclusions

- The repository's content-addressed response cache prevents paying twice for
  an exact rerun. It does not discount the first run: keys include model,
  temperature, seed, prompts, and dynamic portfolio observations.
- Provider-side prompt caching is not assumed. The dynamic observation and
  portfolio make up much of each prompt, and cache accounting is not yet
  represented completely in the usage schema.
- Google bills Gemini output including thinking tokens. The cost ledger must
  verify that the SDK usage fields include them rather than recording only
  visible candidate tokens.
- Anthropic has no seed parameter. Its reproducibility depends on exact model
  versions, recorded prompts, and the local response cache.
- The current prices can change. Re-verify all sources immediately before a
  paid sweep and preserve a dated pricing snapshot in the run manifest.
- H9–H11 signature transport, market detection, causal attribution, and data
  packaging primarily add analysis work, not new LLM calls. They are covered
  in the CPU/storage allowance.
- Trust/adoption vignette LLM calls prepare and validate experimental stimuli;
  they are not a substitute for human participants. Participant recruitment,
  compensation, IRB/ethics review, consent administration, survey hosting,
  and study operations are excluded and remain TBD.
- The budget excludes taxes, network egress, commercial market-data licenses,
  paid survey recruitment, legal/compliance review, and human annotation. The
  current estimate assumes the planned public market/reference datasets can
  be acquired without license fees.
