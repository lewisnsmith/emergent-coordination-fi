# Budget-constrained local-first research plan

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

## Outcome contract

The program has three coequal outcome tracks. Do not optimize one by quietly weakening or dropping
another.

| Outcome track | Required product | Claim boundary |
|---|---|---|
| Public research datasets | Documented, lawful, versioned datasets and reproduction artifacts that other researchers can inspect and extend | Release only artifacts that pass provenance, licensing, privacy, leakage, and verification gates |
| Owned alpha evaluation | Historical and prospective tests of whether locked agent-derived patterns have useful net trading information | Report every tested variant, costs, failed signals, uncertainty, and overfitting controls; do not equate a backtest or paper result with durable alpha |
| Validated AI-agent trading risks | An evidence-backed assessment of observed failure modes, correlated behavior, convergence, cascades, quantization effects, and deployment conditions | Distinguish simulated risk, observational resemblance, verified exposure, and causal attribution; issue guidance only at the strongest level the evidence supports |

Every experiment, external-paper substitution, and paid expansion must state which track it serves.
Shared artifacts may support multiple tracks, but each track keeps its own estimands, labels, gates,
and verdicts. A dataset release does not prove alpha, alpha does not prove AI causation, and a
simulated failure does not by itself establish real-market risk.

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

## Evidence-substitution rule

Use external papers to avoid repeating a result only when the external artifact matches the
question strongly enough to support the same bounded claim. Record one of four uses for every
candidate source:

- `method_only`: Reuse a statistic, protocol, benchmark, or tool, but no empirical conclusion.
- `prior_only`: Cite the result for motivation, novelty boundaries, or a prior distribution.
- `partial_substitute`: Reuse a comparable result for a named cell or robustness check while
  retaining the unmatched cells.
- `full_substitute`: Treat the external result as answering the registered question within the
  declared population boundary.

Require all of the following before assigning `full_substitute`:

- The population, treatment, comparator, estimand, outcome, and highest independent unit match.
- Exact model or checkpoint lineage and the relevant market or task domain match.
- Code, data, prompts, exclusions, and enough raw artifacts are available for reproduction.
- The analysis handles dependence, multiplicity, leakage, missingness, and negative controls at
  least as strictly as this program.
- Held-out or external validation supports the claim, and the result is not only an abstract,
  leaderboard, single run, or selected success.
- The artifact passes license, provenance, and comparability review before the analysis plan is
  frozen.

If any requirement fails, use the source as `method_only`, `prior_only`, or `partial_substitute`.
Citation alone never completes a hypothesis. Existing direct LLM-finance papers currently define
novelty boundaries and priors; they do not replace the matched local-to-frontier, precision, market
transport, or prospective trading tests in this plan.

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

## Conversation-derived context

**Context date:** 2026-08-10.

This appendage preserves the research-planning context that produced this plan. It is a concise
decision record, not a verbatim transcript, scientific evidence, preregistration, or authorization.
If it conflicts with a later signed decision, frozen preregistration, or machine-readable study
contract, the later explicit artifact controls and this section must record an amendment.

### Original research objective

The project began with a broad question: can results and experiments from adjacent research
projects reduce cost while still answering the project's questions, concerns, and hypotheses?
The desired endpoint was not only a simulation demonstration. The project should create
publishable artifacts and real-world datasets that:

- Identify statistical patterns in financial agents and agent populations.
- Test which shared model, provider, profile, information, prompt, and harness components produce
  convergence or correlated behavior.
- Determine whether those patterns appear in real market data without mislabeling resemblance as
  AI causation.
- Support prospective signal evaluation and paper trading under strict out-of-sample controls.
- Preserve enough provenance and uncertainty for independent reproduction and publication.

The practical motivation includes learning whether these patterns contain trading information.
The research record must keep that motivation separate from claims of proven alpha, investment
advice, verified AI exposure, or real-market causation.

### Three-output mandate

The project must preserve three coequal outputs throughout planning, execution, and release:

- Public datasets and reproducible artifacts that other researchers can use.
- Owned evaluation of whether agent-derived patterns provide net out-of-sample trading information.
- Evidence-backed findings and guidance about validated risks from using AI agents to trade.

These outputs can share raw observations, but they cannot borrow one another's evidentiary status.
The project must track which experiments and external results support each output and must report a
separate supported, inconclusive, rejected, or blocked verdict for each registered claim.

### Cost constraint that changed the execution order

The full frontier-heavy program was found to be incompatible with a personally funded project.
Its expensive components include millions of sequential frontier calls, independent shared-market
replicas, human recruitment and study administration, multi-GPU activation work, licensed market
or exposure data, large prompt factorials, and release engineering.

The available personal resources were stated as:

- About $2,000 for hardware acquisitions.
- About $200–300 for software, data, or direct API purchases.
- An existing workstation with 64 GB of system RAM and an RTX 2080 Ti.
- The option to apply for OpenAI and Anthropic research-credit programs.

This constraint led to a local-first proposal rather than a reduced hypothesis list. The plan
prioritizes experiments whose marginal cost becomes electricity, storage, engineering time, and a
small held-out API bridge after an appropriate local GPU is available.

### Non-negotiable hypothesis-retention rule

No hypothesis may be removed because it is expensive. Cost may:

- Mark a component as high cost.
- Change execution order.
- Defer a stage.
- Narrow an initial sample through a preregistered gate.
- Motivate a research-credit application.
- Permit qualified external evidence to replace a genuinely equivalent cell.

Cost may not silently delete, merge, relabel, or declare a hypothesis complete. Scientific removal
requires a rationale unrelated to cost and a visible preregistration amendment.

### External-evidence requirement

The instruction to fill gaps with published results has a strict condition: use a paper result
only if it is as robust as the actual question. A paper that establishes a generic phenomenon does
not replace a narrower or differently identified experiment.

The conversation distinguished the following uses:

- Established statistics, executable tasks, public datasets, and pretrained interpretability
  artifacts can remove redundant method-development work.
- Direct LLM-finance studies can establish prior art and prevent unsupported novelty claims.
- Quantization studies can justify the precision ladder and expected interactions.
- None of those sources automatically answers finance-specific local-to-frontier equivalence,
  same-checkpoint error propagation, market transport, or prospective signal performance.

The evidence-substitution rule in this plan formalizes the phrase "as robust as the question."

### Why local-model fidelity became the affordable core

The local-first direction combines several questions that can share the same open checkpoints and
artifacts:

- When do smaller or quantized open models preserve frontier-model financial behavior?
- Which differences arise from checkpoint family or scale, and which arise from quantization?
- Where does the first financial reasoning error occur, and how does it propagate through later
  calculations, trades, portfolios, and market feedback?
- Which internal activations causally mediate a correct step, an error, a risk response, or a trade?
- Which model configurations preserve profile sensitivity and population diversity rather than
  collapsing into one response pattern?
- Can signatures discovered in controlled agent populations transport to unseen real-market data?

This lane can produce useful and publishable results even if local models fail the equivalence
test. A well-identified failure boundary, precision cliff, or nontransporting signature is still a
research result.

### Clarification of the financial scoring key

The phrase "financial oracle stage" caused confusion because it sounded like another model to
compare with local and frontier systems. The plan now calls it the *financial scoring key*.

The scoring key is ordinary executable code plus frozen intermediate values. It answers whether a
calculation is correct. It does not answer whether the local model resembles a frontier model.
Local precision is still compared with frontier models, but that is a separate axis:

| Comparison | Interpretation |
|---|---|
| Local W8/W4/W3 versus the same local checkpoint at BF16 or FP16 | Causal precision contrast when the remaining runtime and model lineage are held fixed |
| Local finalist versus sampled frontier endpoints on the same held-out inputs | Behavioral fidelity and difference |
| Any model output versus the financial scoring key | Financial correctness and step-error location |

All three comparisons can use the same task record. The scoring key prevents model agreement from
being mistaken for correctness and prevents a local-frontier difference from being mislabeled as
a quantization effect.

### Expected affordable research arc

The conversation converged on the following arc:

- Reuse only external results that pass the evidence-substitution rule.
- Benchmark the current RTX 2080 Ti before buying hardware.
- Acquire a 24 GB CUDA GPU only if it enables an otherwise blocked same-checkpoint comparison.
- Run the broad BF16/W8/W4/W3 precision and error-propagation ladder locally.
- Use one OpenAI and one Anthropic endpoint for a bounded held-out behavioral bridge if credits or
  a small direct authorization exist.
- Run targeted mechanistic interventions only after a behavioral effect or strong equivalence
  question identifies useful cases and sites.
- Expand the affordable local configurations into agent replay and controlled simulated-market
  work.
- Lock candidate signatures before testing transport in unseen real-market periods.
- Convert only transport-approved signatures into frozen rules for walk-forward evaluation and
  prospective paper trading.
- Publish nulls, failed signals, costs, and blocked claims alongside positive findings.

### Expected outputs

The desired artifacts include:

- A financial-chain task and scoring-key dataset.
- A same-checkpoint quantization transition and error-propagation dataset.
- A local-to-frontier behavioral equivalence map.
- Activation-intervention and mechanism records for sampled open checkpoints.
- Agent decision, order, fill, portfolio, convergence, and strategy datasets.
- A locked simulation-signature library.
- Real-market signature events labeled as observational and not attributed.
- A complete historical and prospective paper-trading ledger, including every failed signal and
  tried parameterization.
- A manuscript, dataset card, claim registry, lineage graph, checksums, and reproduction record.

These outputs do not guarantee profitable trading, identify actual AI use in a market, or permit a
causal claim without verified exposure and a credible counterfactual.

### Work that remains high cost or externally blocked

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

### Decisions already made

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

### Proposals that are not yet frozen

The following items remain proposals rather than canonical study decisions:

- Making H13/H8 the first owned empirical paper instead of the configured H1/H3/H4 paper.
- Buying a used RTX 3090 24 GB rather than another GPU or no GPU.
- Selecting the exact two open checkpoint families and two size tiers.
- Selecting the exact OpenAI and Anthropic frontier endpoints.
- Using the provisional 2, 4, 8, and 16 dependency-depth ladder and the current sample caps.
- Selecting equivalence, noninferiority, safety, and material-difference margins.
- Selecting the real-market feature panel, universe, frequency, and paper-trading venue.
- Selecting the prospective paper-trading duration and any later criteria for a separate
  real-money proposal.

Resolve these items through benchmark evidence, power calculations, licensing review, and a frozen
preregistration rather than conversational preference.

### Repository-governance context

The research record also adopted two repository rules during the conversation:

- Do not use numeric ordering prefixes in document filenames, titles, link labels, navigation, or
  indexes. Preserve meaningful dates, hypothesis labels, experiment identifiers, quantities, and
  scientific section numbers.
- Group and commit changes incrementally by logical purpose through the shared shipping workflow.

These rules affect documentation and change management, not the scientific evidentiary standard.
