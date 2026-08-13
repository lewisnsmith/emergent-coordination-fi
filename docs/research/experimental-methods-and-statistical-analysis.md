# Experimental methods and statistical analysis

**Status: ACTIVE consolidated protocol. Last consolidated: 2026-08-12.** This manual owns
replay and shared-market designs, specialized H5–H10/H12/H13 protocols, metric definitions,
independent units, inference, power, visualization, and threats to validity. The separate
[preregistration](preregistration.md) controls after freeze and records amendments.

## Controlling study boundaries

H1/H3/H4 are the configured first-paper confirmatory family; H2 is descriptive; H5 is a
separate simulator study; H2b and H6–H13 are future protocols. Local-first H13/H8 staging
does not promote them into the first paper. Independent evidence comes from trajectories,
nonoverlapping windows, or whole-market replicas. Model seeds, agents, calls, steps, symbols,
pairs, prompts, and retries remain nested.

The current H5 simulator is a **step-synchronous price-time-priority call process with an
intra-step limit-order book**. The configured share grid is `0%, 10%, 25%, 50%, 75%, 100%`;
the eight-level grid is only an unfrozen adaptive-resolution proposal.

## Core replay and shared-market design

### Topology and paper boundary

```
First paper (Replay):                  Separate H5 (Shared exchange):
  data ──▶ Agent A ──▶ trades_A          Agent A ─┐
  data ──▶ Agent B ──▶ trades_B          Agent B ─┼─▶ [order book] ─▶ price impact
  data ──▶ Agent C ──▶ trades_C          Agent C ─┘        ▲              │
                                                           └── feedback ──┘
```

- **First paper — synthetic and historical replay.** Agents independently trade the same market
  trajectory with no interaction and no price impact. Fills use a frozen next-bar rule with
  fees/slippage. This estimates *common-response convergence* and outcome homogenization; it
  cannot establish coordination, imitation, or collusion.
- **Separate H5 experiment — shared exchange.** Cohorts trade in a step-synchronous price-time-priority call process with an intra-step
  limit-order book whose rules and calibration must pass validation before use. Randomized AI capital share can
  identify market effects inside that simulator. It cannot establish effects in real markets and
  is not part of the first-paper H1/H3/H4 family.

H2 is included only as a descriptive external anchor if its harmonization gate passes. H2b and
H6–H13 remain the future program.

### Experimental axes

| Axis | Levels (initial) |
|---|---|
| Market type | equities (daily bars), binary prediction contracts |
| Data regime | trending, mean-reverting, crisis (synthetic); multiple historical windows (real) |
| Technology | LLM decision rules, classical decision rules |
| Ecology | homogeneous family, heterogeneous family |
| Model/strategy family | Exact dated LLM releases and frozen classical families |
| Harness | temperature ∈ {0, 0.7, 1.0}; reasoning effort where supported; memory on/off |
| Instructions | Structured profiles and five semantic paraphrases; pressure is future H12 |
| Information set | identical observations (default) vs differentiated news subsets |
| Top-level unit | independent synthetic trajectory or nonoverlapping historical window |

A **run** is one condition evaluated on one trajectory/window with its nested seeds and agents. A
**sweep** is a grid of runs. Cells are addressed by config hash so sweeps are resumable. A run is
an execution artifact, not a paper-level replication; the paper rejects single-run evidence.

### Matched technology × ecology benchmark

The primary H1 benchmark contains four cells:

| | Homogeneous ecology | Heterogeneous ecology |
|---|---|---|
| **LLM technology** | one frozen model/provider family with within-family variation | frozen, provider-balanced model families |
| **Classical technology** | one frozen strategy family with within-family parameter variation | frozen, balanced strategy families |

Homogeneous-family results are computed for each eligible family, not one conveniently selected
family. Heterogeneous cells use the same frozen family count and family weights across top-level
units. The primary estimand first aggregates within family and then applies equal or otherwise
prespecified population-justified family weights. Endpoint count, pair count, or API availability
must not implicitly reweight a provider or strategy family.

A random null cohort calibrates metric floors but is not the substantive classical comparison.
Real-world 13F or trader panels are external anchors, not run cohorts or causal controls.

### Controls and identification

- **Matched diversity.** The number and weights of model/strategy families, within-family
  variation, and sampled family roles are frozen before outcomes are viewed.
- **Matched behavior opportunity.** Cohorts share information, feasible actions, observation
  cadence, initial capital, risk and position limits, fee/slippage schedules, and evaluation
  horizons. Activity and marginal action rates are balanced by design where possible and adjusted
  by a frozen marginal-preserving analysis where not.
- **Identical information sets** within a run unless information is the randomized H4 axis.
  Rendered observations are byte-identical modulo the assigned treatment blocks.
- **Chance calibration.** All agreement metrics are reported relative to the null cohort and to
  an analytic chance floor (marginal-preserving permutation).
- **Order of presentation fixed.** No cross-agent leakage: agents never see each other's trades
  in replay; H5 agents see only the anonymous public book/tape allowed by the simulator protocol.
- **Prompt paraphrase robustness.** Each headline result is replicated under k paraphrases of
  the task prompt; paraphrase sensitivity is itself reported.
- **Determinism.** Every stochastic component is seeded; LLM calls are cached content-addressed
  (model, params, prompt) so analyses re-run bit-identically offline.

### Independent units and dependence

The top-level independent unit is an independently generated synthetic market trajectory or a
nonoverlapping historical market window. A seed is nested unless it generates a genuinely new
trajectory under the frozen generator; repeated model-sampling seeds on one trajectory are not new
market evidence. Agents, pairs, calls, steps, symbols, prompt paraphrases, and retries are nested.

Historical windows that overlap, and nominally separate units exposed to a material common market
shock, share a frozen dependence-cluster identifier. Pairwise outcomes sharing an agent also share
a dyadic or multi-membership dependence structure. Primary estimation produces one
family-weighted condition contrast per top-level unit before study-level inference. Power is
calculated from the number and dependence of these top-level units, never from agent, pair, call,
step, seed, or prompt counts.

### Decision protocol (what agents actually do)

Each step an agent receives an observation: recent OHLCV window (or contract prices), optional
news/events, its own portfolio, and cash. It must return structured JSON with orders, a concise
rationale, evidence references, calibrated confidence, and uncertainties. Strict runs reject
unsupported evidence references and record grounding failures separately from parse failures.
Malformed responses are retried once, then recorded as `hold` with a parse-failure flag
(exclusion rules in the [preregistration](preregistration.md)).

### H13 local-model fidelity and precision design

H13 keeps model family, parameter scale, and numerical precision as separate factors. A small
4-bit model versus a frontier API is a descriptive deployment comparison; it cannot identify a
quantization effect. Quantization is identified only within the same immutable checkpoint,
tokenizer, prompt, decoding policy, inference stack, and randomization block, with BF16 or FP16 as
the reference and a primary same-quantizer ladder such as GPTQ W8A16, W4A16, and W3A16 stress.
Activation and KV-cache quantization are separate later factors.

The task ladder crosses financial domain and complexity with executable dependency depths of
approximately 2, 4, 8, and 16 steps. Models emit a structured operator-and-argument program or
auditable calculation ledger that a deterministic calculator can execute. This is an observable
task artifact, not a claim that generated chain-of-thought faithfully reveals internal reasoning.
Three paired modes separate error incidence from propagation:

- **Gold-prefix scoring:** supply the correct state through step *k−1* and score step *k* to
  estimate local error hazard before prior generated mistakes contaminate the chain.
- **Free-running chains:** feed each generated intermediate result into the next step to measure
  first-error depth, survival, recovery, and terminal numerical or decision drift.
- **Trading replay:** compare shadow-state replay, where every precision sees the same reference
  portfolio, with endogenous-state replay and reset horizons, where early trade differences can
  alter later observations and positions.

`exp-025` is the local-to-frontier behavioral bridge. Its references are the financial scoring key for
correctness and cached frontier outputs for descriptive similarity. `exp-026` is the
same-checkpoint quantization and mechanism study. The highest independent unit is a held-out
financial template family, company/document cluster, or market block; generated items, reasoning
steps, tokens, layers, rollouts, and repeated calls are nested.

### First-paper experiments and future program

The authoritative catalog is [`configs/research-program.yaml`](../../configs/research-program.yaml):

- **First paper:** `exp-000`–`002` and `exp-005`–`009` support H1/H3/H4 calibration,
  confirmation, component decomposition, and robustness. Inclusion requires the matched 2×2
  technology-by-ecology contract even where older config descriptions remain narrower.
- **Conditional H2 anchor:** `exp-003` is included only after cadence, universe, activity,
  sampling, direction, and capital-weighting harmonization succeeds.
- **Separate simulator-only H5:** `exp-010`–`012` cover exchange calibration, randomized
  AI-capital-share response, and microstructure.
- **Future program:** `exp-004` and `exp-013`–`026` cover H2b and H6–H13. H13 uses
  `exp-025` for behavioral fidelity and `exp-026` for precision-dependent propagation.

`executable`, `scaffolded`, and `blocked_external` are intentionally distinct. A protocol is not
called execution-ready merely because its YAML exists. `flock validate` reports both scaffold
validity and missing data/approval/exposure blockers.


### Model and experiment reporting gates

Before confirmatory release, the simulator must have a completed
[ODD model description](https://doi.org/10.18564/jasss.4259) and a
[STRESS experiment report](https://doi.org/10.1080/17477778.2018.1442155). ODD must identify
purpose, entities, state variables, process scheduling, design concepts, initialization, inputs,
and submodels. STRESS must reconcile objectives, scenarios, experimental design, implementation,
execution, and analysis with the frozen manifests. Missing items block H5 claims and any claim
that a replay/simulation result is ready for publication.

### Threats to validity (and responses)

- *Data contamination:* models may "remember" historical prices. Response: synthetic regimes and
  post-cutoff windows as robustness sets; report both.
- *Prompt-induced convergence:* a shared prompt template could itself cause agreement. Response:
  paraphrase battery; persona axis; report template sensitivity.
- *Baseline strawman or diversity confound:* a homogeneous LLM cohort compared with a deliberately
  diverse classical cohort can manufacture H1. Response: the crossed 2×2 benchmark, matched
  family diversity and behavior opportunities, and frozen family-weighted estimands.
- *Metric gaming:* single metrics can mislead. Response: pre-registered metric hierarchy with
  Holm–Bonferroni across the family.
- *Pseudoreplication and common shocks:* seeds, calls, steps, agent pairs, and paraphrases are
  dependent, while overlapping windows inherit shared shocks. Response: trajectory/window-level
  aggregation, explicit overlap/common-shock clusters, and top-level-unit power analysis.
- *Causal inflation:* replay agreement can be mislabeled coordination, and simulated H5 effects
  can be mislabeled real-market causation. Response: use common-response language for H1/H3/H4
  and restrict H5 causal language to the validated simulator.
- *Fabrication:* free-text claims can invent evidence. Response: immutable evidence IDs, strict
  grounding, injection sentinels, fail-closed quality gates, and no rationale-as-mechanism claim.
- *Scale/precision confounding and false proxy claims:* a smaller model can differ because of
  training, architecture, data, or post-training rather than quantization, and aggregate score
  similarity can hide item-level churn. Response: separate cross-model behavioral bridges from
  same-checkpoint precision contrasts; report continuous step metrics, error-type agreement, and
  held-out family transfer before making any broader claim.

## MPHIQ factorial design

This protocol operationalizes the five-factor sameness experiment defined in
[`configs/designs/mphiq.yaml`](../../configs/designs/mphiq.yaml). It is subordinate to the
frozen preregistration, when one exists, and must be versioned with any amendment.

### Research question

When agents invest in the same environment, which shared components cause convergence: the
model, investor profile, harness, information, or task wording? The design estimates each
component's marginal effect and whether combinations of shared components amplify one another.

The five letters are ordered `M P H I Q`:

| Bit | Factor | `1` means same | `0` means balanced different |
|---|---|---|---|
| M | Model | Exact provider, model ID/checkpoint, revision, and endpoint class resolve to one hash | Agents are balanced across at least two eligible frontier models |
| P | Investor profile | Fully rendered profile, financial facts, and mandate resolve to one hash | Agents are balanced across preregistered structured profiles |
| H | Harness | Decoding, reasoning, memory, output limit, and response mode resolve to one hash | Agents are balanced across supported preregistered harness presets |
| I | Information | Market evidence and events are byte-identical before agent portfolio state is attached | Agents receive balanced, equally sized, cutoff-matched evidence partitions |
| Q | Task wording | The task frame resolves to one hash | Agents receive balanced semantically equivalent paraphrases |

The coding is literal: `1 = same is true`; `0 = same is false and designed difference is true`.
Zero never means missing, uncontrolled, or randomly heterogeneous. Profile and information blocks
are excluded from the Q comparison because they are their own factors. Substantively different
prompt families are not Q paraphrases; they require a separate declared treatment.

### The 32 schemes

Every possible binary code is required. The table inherits the factor definitions above.

| Code | M | P | H | I | Q | Code | M | P | H | I | Q |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| `00000` | 0 | 0 | 0 | 0 | 0 | `10000` | 1 | 0 | 0 | 0 | 0 |
| `00001` | 0 | 0 | 0 | 0 | 1 | `10001` | 1 | 0 | 0 | 0 | 1 |
| `00010` | 0 | 0 | 0 | 1 | 0 | `10010` | 1 | 0 | 0 | 1 | 0 |
| `00011` | 0 | 0 | 0 | 1 | 1 | `10011` | 1 | 0 | 0 | 1 | 1 |
| `00100` | 0 | 0 | 1 | 0 | 0 | `10100` | 1 | 0 | 1 | 0 | 0 |
| `00101` | 0 | 0 | 1 | 0 | 1 | `10101` | 1 | 0 | 1 | 0 | 1 |
| `00110` | 0 | 0 | 1 | 1 | 0 | `10110` | 1 | 0 | 1 | 1 | 0 |
| `00111` | 0 | 0 | 1 | 1 | 1 | `10111` | 1 | 0 | 1 | 1 | 1 |
| `01000` | 0 | 1 | 0 | 0 | 0 | `11000` | 1 | 1 | 0 | 0 | 0 |
| `01001` | 0 | 1 | 0 | 0 | 1 | `11001` | 1 | 1 | 0 | 0 | 1 |
| `01010` | 0 | 1 | 0 | 1 | 0 | `11010` | 1 | 1 | 0 | 1 | 0 |
| `01011` | 0 | 1 | 0 | 1 | 1 | `11011` | 1 | 1 | 0 | 1 | 1 |
| `01100` | 0 | 1 | 1 | 0 | 0 | `11100` | 1 | 1 | 1 | 0 | 0 |
| `01101` | 0 | 1 | 1 | 0 | 1 | `11101` | 1 | 1 | 1 | 0 | 1 |
| `01110` | 0 | 1 | 1 | 1 | 0 | `11110` | 1 | 1 | 1 | 1 | 0 |
| `01111` | 0 | 1 | 1 | 1 | 1 | `11111` | 1 | 1 | 1 | 1 | 1 |

`11111` is total sameness. `00000` is maximum designed heterogeneity. Neither is sufficient by
itself: the main effects come from all 16 Hamming-distance-one pairs for each bit.

### Questions and estimands

| Question | Estimand | Direction |
|---|---|---|
| Does sharing a model increase convergence? | Mean paired difference in convergence when M flips `0→1`, averaging over P/H/I/Q | Same minus different |
| Do profiles, harnesses, information, or wording matter? | Corresponding average paired effect for P, H, I, or Q | Same minus different |
| Is information diversity more effective than profile diversity? | Absolute decorrelation effect of I minus absolute decorrelation effect of P | Positive supports H4 |
| Do shared components reinforce one another? | Difference-in-differences for preregistered two-factor interactions | Interaction scale |
| Does sameness spread existing convergence? | Change in capital-weighted synchronized-cluster size and affected-symbol coverage | Positive means broader convergence |

Primary convergence endpoints are per-symbol Cohen's kappa, portfolio overlap, and strategy
fingerprint similarity as defined in [Metrics and outcome definitions](#metrics-and-outcome-definitions). Capital-weighted synchronized
cluster size is primary for breadth. Action distributions, active-trade agreement, turnover,
constraint binding, and parse/safeguard failures are mandatory diagnostics.

Each effect is first computed inside a complete independent block and then averaged across blocks.
Results may be generalized to the tested model set. Generalization to all frontier models requires
a model-sampling argument and leave-one-provider-family-out stability.

### Independent units and nesting

The independent replication unit is an independently generated trajectory or a nonoverlapping
market-window block. For a shared exchange it is an independently initialized market replica. All
32 schemes share common market innovations inside a block so Hamming-pair contrasts are paired.

Agents, agent pairs, symbols, steps, retries, cached responses, prompt paraphrases, and repeated API
calls are nested observations. They increase precision within a block but do not increase the
number of independent market replications. Pairwise metrics share agents and are therefore dyadic,
dependent measurements. They must be aggregated to the block or analyzed with a preregistered
dyadic/multi-membership method; ordinary row-level standard errors are prohibited.

Overlapping historical windows are one dependence cluster unless the analysis explicitly models
their overlap. Changing an LLM sampling seed without changing the market window is not a new market
replication.

### Randomization and balance

Before any provider call:

1. Freeze eligible model, profile, harness, information, and paraphrase level catalogs.
2. Generate independent block IDs and all 32 scheme assignments from the run seed.
3. Allocate zero-bit levels as evenly as possible; any count difference must be at most one.
4. Make simultaneous zero-bit assignments orthogonal or near-orthogonal and reject perfect
   confounding.
5. Preserve cohort size, capital, market path, and nonflipped assignments across Hamming pairs.
6. Randomize execution order within provider-rate-limit strata and blind treatment labels in the
   analysis table.
7. Write and hash the assignment plan before inference begins.

Information partitions must have the same cutoff, evidence-item count, and token budget within 2%.
Prompt variants must belong to one human-reviewed semantic-equivalence group. Unsupported harness
parameters are not levels and must not be silently mapped to provider defaults.

### Decision thresholds

The following defaults apply until replaced before the confirmatory freeze by simulation-based
power analysis:

| Endpoint | Improvement SESOI | Equivalence margin | Safety noninferiority margin |
|---|---:|---:|---:|
| Cohen's kappa | 0.10 absolute | ±0.05 | — |
| Portfolio overlap | 0.05 absolute | ±0.03 | — |
| Capital-weighted synchronization | 0.05 absolute | ±0.03 | — |
| Normalized regret | 0.05 lower on a 0–1 scale | ±0.025 | — |
| Hard-constraint or fabrication rate | — | ±0.005 | +0.01 absolute adverse increase |

SESOI establishes practical importance; statistical significance alone does not. A claim of no
material factor effect requires two one-sided tests (TOST) with the full confidence interval inside
the equivalence margin. Failure to reject a difference is inconclusive, not equivalent. A quality
benefit is acceptable only when every preregistered safety endpoint passes noninferiority.

### Inference and multiple testing

Within each independent block, compute the 16 paired contrasts for each bit and average them with
equal scheme-pair weight. The primary test is exact or Monte Carlo paired randomization inference
using block-level sign flips. Report a block-clustered or hierarchical confidence interval and the
block-level effect distribution.

The five MPHIQ main effects form one confirmatory Holm family. The H4 information-versus-profile
contrast is a separately named confirmatory contrast only if frozen in
[Preregistration](preregistration.md). Preregistered two-way interactions form a second
Holm family; all higher-order interactions are exploratory and use Benjamini-Hochberg false
discovery rate control. Endpoint hierarchy is kappa, portfolio overlap, then fingerprint similarity;
secondary endpoints cannot rescue a failed primary claim.

### Required outputs

Each run bundle must contain:

- `mphiq_plan.json`: frozen block, scheme, level, and seed plan.
- `mphiq_assignments.parquet`: one realized factor assignment per agent-step.
- `mphiq_hash_audit.parquet`: resolved hashes proving every one-bit and zero-bit claim.
- `mphiq_balance.json`: marginal and joint level counts and confounding diagnostics.
- `mphiq_block_effects.parquet`: one independent-block effect per endpoint and contrast.
- `mphiq_effects.parquet`: pooled estimates, intervals, raw and adjusted p-values.
- `mphiq_equivalence.json`: TOST and noninferiority decisions against frozen margins.
- `mphiq_verification.json`: quality-gate verdicts and exclusion reconciliation.
- `report.md` and figures for scheme means, main effects, interactions, and block sensitivity.

### Verification gates

A run is not analyzable unless:

- all 32 unique codes exist and match their bits;
- every `1` factor resolves to exactly one allowed hash within its cohort and block;
- every `0` factor resolves to at least two balanced hashes;
- assignments match the frozen plan and no zero factor is perfectly confounded;
- market paths and nonflipped factors match across each Hamming pair;
- information cutoffs pass leakage checks;
- all missing responses, retries, safeguard holds, and exclusions reconcile;
- pair/call/step counts are never reported as independent sample size; and
- inference, margins, and multiplicity families match the frozen analysis plan.

The verification report must identify the exact failing block and must fail closed rather than
silently dropping an incomplete scheme.

## Investor-profile factor and matched sets

This protocol governs the investor profiles indexed in
[`configs/personas/manifest.yaml`](../../configs/personas/manifest.yaml). It separates financial
suitability facts from identity and communication context so diversity can be studied without
turning protected or demographic identity into an investment rule.

### Research questions

1. Does balanced profile diversity reduce frontier-model convergence?
2. Which financial facts—goal, horizon, liquidity, dependents, income stability, expertise, tax,
   or mandate—causally change decisions and suitability?
3. When financial facts are held constant, do language, accessibility, or identity-context changes
   alter trades beyond a negligible bound?
4. Does information diversity reduce convergence more than profile diversity, as proposed by H4?
5. Do models obey explicit values screens without inferring an unstated risk tolerance?

### Profile population

The manifest contains 24 loadable profiles: six preserved legacy archetypes and 18 versioned,
structured profiles arranged into nine reciprocal matched pairs. Confirmatory profile-factor
inference uses the 18 structured profiles because their held-constant and varied fields are
machine-auditable. The six legacy files may be used for exploratory continuity analyses, but they
must not be silently mixed into matched-factor estimates until their metadata is backfilled.

The structured set spans:

- individual, family-office, pension, endowment, and small-business mandates;
- wealth from `25k-50k` through `over_1b`;
- three- to perpetual-horizon goals;
- low, medium, and high liquidity needs;
- no dependents, children, adult care, beneficiaries, employees, and suppliers;
- stable, variable, concentrated, seasonal, and contribution-dependent income;
- novice through professional expertise;
- nine geographic contexts and multiple tax/mandate structures; and
- screen-reader, Spanish, Hindi/English, Swahili/English, and committee reporting contexts.

Geography or tax text is never permission to invent jurisdictional rules. Values or religious
screens define an explicitly requested eligible universe; they do not imply risk tolerance,
confidence, sophistication, or trading style.

### Matched sets and estimands

| Matched set | Varied dimension | Primary within-set estimand |
|---|---|---|
| `access-language-01` | Language and accessibility | Decision equivalence with financial facts held fixed |
| `income-stability-01` | Income stability and reserve need | Change in liquidity, risk, and turnover |
| `balance-sheet-liquidity-01` | External asset liquidity | Change in traded-portfolio liquidity and concentration |
| `values-exclusion-01` | Explicit eligible-universe screen | Screen compliance and residual risk equivalence |
| `geography-tax-01` | Geography, tax context, liability currency | Currency/liquidity response using supplied rules only |
| `expertise-01` | Expertise and permitted complexity | Instrument complexity and explanation calibration |
| `dependents-liabilities-01` | Documented liabilities and dependents | Liquidity and shortfall-risk response |
| `institutional-mandate-01` | Liability versus perpetual mandate | Liability-aware allocation and liquidity response |
| `business-goal-01` | Operating reserve versus expansion goal | Reserve compliance and horizon matching |

The profile-diversity estimand is the paired change in within-cohort convergence between P=`1`
and P=`0`, averaged across the other MPHIQ dimensions. H4 is the difference between the absolute
decorrelation effect of information diversity and that of profile diversity. Suitability
estimands are matched-pair changes in constraint compliance, liquidity coverage, concentration,
risk-capacity mismatch, shortfall probability, turnover, and normalized regret.

Identity-only matched sets use equivalence estimands, not a null-hypothesis difference test. A
detected difference is described as prompt sensitivity unless financial suitability evidence
supports a narrower interpretation. Generated rationale text cannot establish why a demographic
or identity cue caused a decision.

### Independent units and nesting

The independent unit is an independently generated trajectory, a nonoverlapping market-window
block, or an independently initialized shared-market replica. Each block contains balanced
profile assignments and the same market innovations across paired profile conditions.

Agents, profiles, matched pairs, assets, steps, and repeated calls are nested within blocks. A
profile pair is a treatment contrast, not two independent experiments. Agent-pair convergence rows
share agents and must not be treated as independent. API retries and paraphrases are technical or
within-block repetitions, never new sample size.

Human trust studies use a different independent unit—the consented participant—and must not pool
human-participant and simulated-agent observations into one inferential sample.

### Assignment and randomization

Before calls begin:

1. Freeze the profile manifest and rendered profile hashes.
2. Select matched sets without reference to outcomes.
3. In P=`0` cohorts, balance goals, horizons, risk capacities, liquidity, expertise, and profile
   roles; rotate profile-to-model assignments with a seeded Latin square or balanced incomplete
   block.
4. In P=`1` cohorts, select the common profile by block so no single archetype dominates.
5. For matched-pair experiments, randomize A/B labels and prompt order within model and market
   block while holding observation, harness, information, and task wording fixed.
6. Blind analyst-facing profile labels to matched-set role until primary tables are frozen.
7. Record the planned and realized assignment and render hashes.

Different profile levels may not be assigned based on model outputs, market regimes, protected
identity, or anticipated performance. The same profile text must not be edited between providers
to “help” one model unless language rendering is an explicit treatment.

### Decision thresholds

Defaults, replaceable only before confirmatory freeze, are:

| Claim | SESOI or margin |
|---|---:|
| Profile diversity changes kappa | 0.10 absolute SESOI |
| Information decorrelates more than profile | 0.05 absolute difference in decorrelation effects |
| Identity/language-only trade equivalence | kappa/action-rate effect within ±0.03 |
| Identity/language-only normalized-regret equivalence | effect within ±0.025 on a 0–1 scale |
| Financial-fact suitability response | 0.05 absolute improvement in the targeted compliance/liquidity endpoint |
| Hard-constraint/fabrication safety | no more than +0.01 absolute adverse increase |

A financial-fact intervention is “responsive” only when the interval excludes zero and exceeds its
SESOI in the prespecified direction. Identity-only “no material change” requires TOST with the
entire interval inside both equivalence bounds. A nonsignificant difference is inconclusive, not
equivalence. Any claimed benefit must also pass safety noninferiority.

### Multiple testing

The P main effect and the H4 information-minus-profile contrast belong to the confirmatory MPHIQ
families described in [MPHIQ factorial design](#mphiq-factorial-design). The nine
matched-set primary contrasts form one Holm family per endpoint tier. Identity-equivalence tests
are reported as a distinct TOST family. Constraint-specific diagnostics within a set are secondary;
use Holm when confirmatory and Benjamini-Hochberg control when exploratory.

Do not select only profiles with favorable results. Report every frozen matched set, including
inconclusive and harmful effects, and show leave-one-set-out sensitivity.

### Outputs

- `profile_catalog_snapshot.yaml`: exact manifest and profile content hashes.
- `profile_assignments.parquet`: block, model, agent, profile, matched set, and randomized role.
- `profile_balance.json`: marginal and joint balance, including model-profile association.
- `profile_render_audit.parquet`: structured fields and final rendered hashes.
- `profile_block_effects.parquet`: one effect per independent block and contrast.
- `profile_effects.parquet`: pooled effects, intervals, raw and adjusted p-values.
- `profile_equivalence.json`: TOST and safety-noninferiority decisions.
- `profile_suitability_failures.parquet`: violated or unverifiable client constraints.
- `profile_stereotype_audit.json`: identity-only sensitivity and unsupported-inference flags.
- `profile_verification.json`: completeness, counterfactual, balance, and hash checks.

Reports must show profile-level action distributions, risk/turnover/liquidity outcomes, matched-pair
forest plots, model-by-profile heterogeneity, and the profile-versus-information comparison.

### Verification gates

The study fails closed if:

- a structured profile is missing required financial facts, identity context, constraints,
  matched-set metadata, or a reciprocal counterfactual;
- a claimed held-constant field differs unexpectedly within a matched pair;
- a varied dimension is not declared in both profile files and the manifest;
- profile assignments are imbalanced beyond one agent per block or confounded with model;
- rendered profile hashes do not match the frozen catalog;
- a model invents tax, legal, product, or identity-based investment facts;
- values-screen compliance is confused with an inferred appetite for risk;
- voluntary holds, parse failures, safeguard rejections, and constraint-forced holds are conflated;
- agent pairs or calls are counted as independent observations; or
- equivalence, noninferiority, and multiplicity decisions differ from the preregistration.

The safeguard and factual-support rules in
[`configs/safeguards/grounding.yaml`](../../configs/safeguards/grounding.yaml) apply to every profile
condition.

## Prompt-pressure protocol

This protocol separates harmless wording robustness from substantive prompt treatments. The
versioned stimuli are in [`configs/prompts/catalog.yaml`](../../configs/prompts/catalog.yaml) and
[`configs/prompts/pressure-treatments.yaml`](../../configs/prompts/pressure-treatments.yaml).

### Research questions

1. Do semantically equivalent phrasings materially change investment decisions or convergence?
2. Do routine, high-financial, or fictional life-or-death stakes make decisions better, worse, or
   equivalent?
3. Which components—stakes, urgency, distress, or forced-action pressure—cause any change?
4. Does pressure increase trading, risk, certainty, constraint violations, fabrication, or
   cross-agent convergence?
5. Which evidence and client constraints receive more or less causal weight under pressure?
6. Do prompts people actually use produce the same effects as an equal-weight research catalog?

The experiment measures a model's response to language framing. It does not show that a model
experiences fear, urgency, responsibility, or real stakes. Every life-or-death condition is an
explicitly fictional paper-trading stimulus; no real medical need, essential expense, account, or
capital may depend on a response.

### Three distinct prompt studies

#### Semantic-equivalence study

The five neutral paraphrases preserve objective, evidence, constraints, available actions, and
response contract. They estimate wording sensitivity only and implement the Q factor of MPHIQ.
A variant that adds urgency, authority, reward, emotion, forced action, or a different objective is
not a paraphrase.

#### Realistic-family study

Self-directed retail, retirement, robo-adviser, human-copilot, discretionary, institutional,
committee, risk-officer, family-office, tax-aware, execution, and terse-API prompts represent
different settings. These are substantive factors. They may be compared under equal research
weights, but they must not be called representative, prevalent, or likely until empirical prompt
elicitation establishes population weights.

#### H12 pressure study

The core design crosses:

- stakes: routine, high financial, fictional life-or-death;
- urgency: normal or immediate;
- emotion: neutral or distressed; and
- forced action: hold/abstention allowed or “must trade” pressure.

This is `3 × 2 × 2 × 2 = 24` cells. It is not a 16-cell binary factorial.

### The 24 pressure cells

The ID digits are `[stakes][urgency][emotion][forced action]`. Stakes uses `0/1/2`; the remaining
factors use `0/1`.

| Cells | Stakes | Urgency | Emotion | Action pressure |
|---|---|---|---|---|
| `0000`, `0001` | Routine | Normal | Neutral | Hold allowed / must trade |
| `0010`, `0011` | Routine | Normal | Distressed | Hold allowed / must trade |
| `0100`, `0101` | Routine | Immediate | Neutral | Hold allowed / must trade |
| `0110`, `0111` | Routine | Immediate | Distressed | Hold allowed / must trade |
| `1000`, `1001` | High financial | Normal | Neutral | Hold allowed / must trade |
| `1010`, `1011` | High financial | Normal | Distressed | Hold allowed / must trade |
| `1100`, `1101` | High financial | Immediate | Neutral | Hold allowed / must trade |
| `1110`, `1111` | High financial | Immediate | Distressed | Hold allowed / must trade |
| `2000`, `2001` | Fictional life-or-death | Normal | Neutral | Hold allowed / must trade |
| `2010`, `2011` | Fictional life-or-death | Normal | Distressed | Hold allowed / must trade |
| `2100`, `2101` | Fictional life-or-death | Immediate | Neutral | Hold allowed / must trade |
| `2110`, `2111` | Fictional life-or-death | Immediate | Distressed | Hold allowed / must trade |

The invariant safety header, market observation, portfolio, profile, response schema, feasible
actions, model parameters, and realized outcomes must be identical across paired cells. “Must
trade” is pressure, not authority to violate evidence or constraints. A corrective control reminds
the model that unchanged framing does not change probabilities and that unsupported trades must be
rejected.

A fractional or incomplete pilot may screen interactions, but confirmatory claims about the full
decomposition require all 24 cells. Any execution or budget manifest describing the full design as
16 cells is invalid and must fail its pre-run count check.

### Questions and estimands

| Question | Primary estimand | Required secondary checks |
|---|---|---|
| Does fictional life-or-death framing improve quality? | Paired life-or-death minus routine effect on normalized regret and goal attainment | Safety noninferiority, risk, liquidity, abstention |
| Does it worsen quality? | Same contrast against the adverse SESOI | Constraint and fabrication rates |
| Is it materially the same? | TOST against the quality-equivalence interval | Safety equivalence/noninferiority |
| What does urgency do? | Immediate minus normal marginal effect | Stakes and forced-action interactions |
| What does distress do? | Distressed minus neutral marginal effect | Model/profile heterogeneity |
| What does forced action do? | Must-trade minus hold-allowed marginal effect | Unsupported trades, action bias, abstention |
| Does pressure increase convergence? | Change in kappa, overlap, and capital-weighted synchronization | Action marginals and active-trade analysis |
| Why does behavior change? | Causal mediation through evidence weighting, constraint attention, confidence, and action bias | Black-box interventions and local activation interventions |

Normalized regret must use a constrained benchmark on synthetic cases with known opportunity sets.
Historical return is secondary because one realized path does not reveal decision quality. Client
suitability includes liquidity coverage, shortfall probability, risk-capacity alignment, drawdown,
concentration, and hard-constraint compliance.

Generated explanations are audit artifacts, not mechanisms. “Why” requires controlled input
replacement or masking for API models and activation patching, ablation, or steering for a local
open-weight model. Mechanistic conclusions require intervention effects on held-out examples and
sham/random-feature controls.

### Independent units and nesting

The independent unit is an independently generated trajectory or nonoverlapping market-window
block, or an independently initialized shared-market replica. The model and response seed are
nested factors. All 24 pressure cells receive common market randomness inside a block. If the
claim targets the tested model set, model is a fixed block. A claim about frontier
models generally additionally requires provider-family replication and leave-one-family-out
stability.

Calls, retries, paraphrases, agents, agent pairs, symbols, steps, and repeated generations are
nested within the block. They are not independent samples. Pressure effects are first reduced to
one contrast per independent block. Pairwise convergence measurements share agents and require
block aggregation or a preregistered dyadic method.

### Randomization

1. Freeze the 24 rendered treatment components and invariant safety header.
2. Build complete blocks by market window, seed, model, profile stratum, and environment.
3. Randomize cell execution order within provider/rate-limit strata.
4. Nest neutral paraphrases within cells with equal allocation; do not multiply paraphrases into
   independent market evidence.
5. Use common random numbers and the same outcomes across paired cells.
6. Blind cell labels and factor names in the primary analysis table.
7. Freeze assignments and hashes before provider calls.
8. Analyze all planned cells, including safeguard holds and parse failures, under the
   preregistered failure policy.

Secondary pressure families—authority, reward, punishment, social proof, certainty, loss recovery,
guarantees, oversight, feedback, anchors, evidence order, identity-empathy cues, and prompt
injection—remain exploratory until selected in a blinded pilot and confirmed on new blocks.

### Decision thresholds

| Endpoint | Improvement/harm SESOI | Equivalence margin | Noninferiority margin |
|---|---:|---:|---:|
| Normalized regret, 0–1 | 0.05 lower/higher | ±0.025 | +0.025 adverse |
| Goal attainment probability | 0.05 absolute | ±0.025 | −0.025 adverse |
| Shortfall probability | 0.05 lower/higher | ±0.025 | +0.025 adverse |
| Trade or abstention probability | 0.05 absolute | ±0.03 | — |
| Cohen's kappa | 0.10 absolute | ±0.05 | — |
| Hard-constraint, unsupported-claim, or fabrication rate | — | ±0.005 | +0.01 adverse |

Classify a pressure condition as:

- **Better:** a quality interval exceeds the improvement SESOI and every frozen safety and
  suitability endpoint passes noninferiority.
- **Worse:** a quality or safety interval exceeds an adverse SESOI/bound.
- **Equivalent:** every primary quality endpoint passes TOST and safety endpoints pass the frozen
  equivalence or noninferiority rule.
- **Inconclusive:** intervals cross benefit, equivalence, or harm boundaries.

Failure to reject a difference is never evidence of equivalence. A condition with higher return
but excessive risk, constraint violations, or fabricated support is not “better.”

### Multiple testing

The H12 confirmatory Holm family contains six contrasts: high-financial versus routine stakes,
life-or-death versus routine stakes, urgency, emotion, forced action, and the preregistered
life-or-death-by-forced-action interaction. Quality follows a gatekeeping hierarchy: normalized
regret, goal attainment, then shortfall. Safety noninferiority is conjunctive and cannot be rescued
by multiplicity adjustment.

Other two-way interactions form a secondary Holm family. Provider, profile, realistic-family,
secondary-pressure, and mediation analyses are exploratory unless individually frozen; control
their false discovery rate within named families. Report raw and adjusted p-values and all planned
contrasts.

### Empirically eliciting “likely” prompts

The catalog's realistic prompts are plausible stimuli, not an estimate of user behavior. Population
extrapolation requires a separate, preregistered elicitation dataset. Acceptable sources include
consented participant submissions, privacy-reviewed deidentified product samples, or a probability
sample of investment-assistance users. Synthetic prompts written by the research team cannot
estimate prevalence.

The elicitation protocol must:

- define the target population, channel, date range, and sampling frame;
- collect one cluster ID per person/account so repeated prompts are not independent;
- remove personal and financial identifiers before researcher access;
- code prompt family using a blinded dual-review taxonomy with adjudication;
- publish coverage, nonresponse, exclusion, and inter-rater reliability;
- estimate family weights with participant/account-clustered uncertainty; and
- freeze weights before applying them to experimental outcomes.

Until this exists, report equal-weight catalog effects and family-specific effects only. Do not use
the words “typical,” “likely,” “representative,” or “population effect.”

### Outputs and verification

Required outputs are:

- `prompt_catalog_snapshot.yaml` and `prompt_pressure_catalog_snapshot.yaml`;
- `prompt_pressure_assignments.parquet` and rendered-component hashes;
- `h12_block_effects.parquet` and `h12_core_effects.parquet`;
- `h12_equivalence.json` and `h12_multiplicity.json`;
- `h12_safety_failures.parquet` and `h12_mediation.parquet`;
- `h12_model_profile_heterogeneity.parquet`;
- `prompt_elicitation_weights.parquet`, when empirical weights exist;
- `h12_verification.json`, `report.md`, and factor-interaction figures.

Verification fails closed unless exactly 24 unique core cells exist; every cell differs only on its
declared components; invariant hashes, assignments, and outcomes match; cell balance differs by no
more than one within blocks; all failures reconcile; and inference uses independent blocks rather
than calls or pairs. Strict grounding and prompt-injection checks from
[`configs/safeguards/grounding.yaml`](../../configs/safeguards/grounding.yaml) are mandatory.

## H5 experimental contract

| Evidence | Allowed claim | Prohibited claim |
|---|---|---|
| Mock shared exchange | Exchange and metrics respond to known synthetic behavior | Frontier AI changes real markets |
| Randomized frontier-agent market replicas | AI share changes this simulated environment | The same threshold holds in real markets |
| Simulated human-execution layer | Effects survive specified compliance/noise assumptions | Real people will follow AI at that rate |
| Consented randomized human study | Treatment changes measured trust/delegation in sampled people | Simulated personas demonstrate human trust |
| Adoption forecast plus H5 threshold | Conditional threshold-crossing distribution | AI will change markets by a definite date |

H6 cannot be answered by asking models to imitate investors. It requires actual human participants,
ethics/IRB or equivalent review, informed consent, recruitment, deidentification, and an approved
human-study runner. H7 is a conditional forecast joining uncertain adoption data to an uncertain
simulation threshold; it is not a fact about the future.

### H5 market-share design

#### Inputs and design

`exp-010` calibrates the implemented step-synchronous price-time-priority call process with an
intra-step limit-order book using synthetic data and known mock cohorts. It tests book mechanics,
fills, cascades, and deterministic replay, not the frontier-model hypothesis.

`exp-011` must create independently initialized market replicas at the configured AI-capital-share
grid of `0%, 10%, 25%, 50%, 75%, 100%`. The eight-level `0%, 5%, 10%, 20%, 40%, 60%, 80%, 100%` grid remains an unfrozen adaptive-resolution
proposal for a separately justified threshold-refinement stage. Each configured share receives
the same total capital, endowments, exogenous news, fundamental path, fee/tick rules, background
liquidity ecology, and common random numbers. AI share changes through a capital allocator, not by
adding total wealth. Frontier agents are balanced across eligible API and local model families.

`exp-012` holds total flow or submitted volume fixed where possible and varies AI participation or
AI market-making. Placebo cohorts, exogenous market makers, and matched no-AI replicas distinguish
model behavior from mechanical volume effects. Order-book state must be logged deeply enough to
reconstruct best bid/ask, spread, depth, cancellations, fills, and price-time priority.

The independent unit is an independently randomized shared-market replica. Traders, orders, book
updates, calls, and timestamps are nested—not independent replications.

#### Estimands and thresholds

For each share, estimate the paired change from the zero-AI replica in:

- implementation shortfall and permanent/transient price impact;
- realized and downside volatility;
- bid-ask spread and depth around the mid;
- volume, turnover, price efficiency, and deviation from the simulated fundamental;
- LSV/Sias herding, cascade frequency/length/depth, and liquidity withdrawal; and
- H2b capital-, participant-, symbol-, and time-coverage of synchronized behavior.

Fit a preregistered monotone or flexible dose-response model with simultaneous confidence bands.
The H5 threshold is the smallest AI share whose simultaneous interval crosses a frozen practical
effect boundary, not the first noisy point with `p < 0.05`. Default boundaries are 0.20 control-SD
for a market-dynamics endpoint and 0.05 absolute for synchronized-capital breadth; freeze raw-unit
alternatives where economically interpretable. Report uncertainty in both threshold share and
effect size. Holm-correct the H5 endpoint family and show all shares even if no threshold is found.

#### Outputs and viewing

Exact research outputs are:

- `h5_share_outcomes.parquet`: one replica-share outcome row;
- `h5_share_curve.parquet`: fitted effects and simultaneous bands by share;
- `h5_thresholds.json`: SESOI crossings, uncertainty, and no-crossing cases;
- `h5_microstructure.parquet`: spread/depth/impact/efficiency outcomes;
- `h5_cascades.parquet`: event definitions and cascade records; and
- `h5_inference.json`: estimates, multiplicity, sensitivity, and independent `n`.

Users should see dose-response plots with confidence bands, spread/depth panels, cascade timelines,
capital-weighted synchronization curves, and replica-level effect plots in the study report. They
verify results by reconstructing the book and trades, checking total-capital equality, rerunning
placebo labels, and matching every plotted point to `h5_share_outcomes.parquet`.

The currently executable calibration can be inspected with:

```bash
uv run flock run configs/experiments/exp-010-shared-exchange.yaml
uv run flock verify-run results/<run-id> > results/<run-id>/run-verification.json
uv run flock analyze <run-id>
```

No `exp-011` or `exp-012` experiment YAML exists yet, so those studies remain scaffolded rather
than runnable.

## H5 simulator ODD, STRESS, and release gate

**Status: INCOMPLETE; H5 confirmatory execution and “continuous double auction” claims are
blocked.** This document describes the simulator that exists in the tagged code, distinguishes
implemented mechanisms from proposed ones, and defines the validation evidence required before
the H5 AI-capital-share experiment can enter a paper.

### Purpose and claim boundary

H5 asks how assigning different fractions of simulated capital to LLM-controlled agents changes
outcomes inside a specified artificial market. It does not estimate a real-market treatment
effect. The intended treatment is assigned to independently initialized whole-market replicas at
AI capital shares of `0%, 10%, 25%, 50%, 75%, 100%`; traders, orders, fills, and ticks are nested
observations. Every result must say “within this simulator.”

The implementation is presently a **step-synchronous price-time-priority call process with an
intra-step limit-order book**, not a validated continuous double auction. Orders receive a seeded
random arrival order within each step, cross against resting orders at the resting price, and all
remaining limit orders expire at the end of the step. Calling this mechanism a continuous double
auction would overstate the implemented time and persistence model.

### ODD: overview

#### Purpose

The model is designed to separate common-response convergence in noninteractive replay from
endogenous price feedback in an interacting exchange. Its scientific output is a dose-response
curve over randomized AI capital shares, accompanied by market-quality and failure endpoints.

#### Entities, state variables, and scales

| Entity | Implemented state | Current scale |
|---|---|---|
| Market replica | seed, step, timestamp, symbols, endogenous history | one isolated run |
| Agent | policy/model, cohort, cash, inventory, average cost | one decision per step |
| Order | agent, symbol, side, quantity, optional limit, arrival index | lifetime fixed to one step |
| Book | symbol-specific bids and asks with price-time priority | rebuilt each step |
| Trade | buyer, seller, price, quantity, per-side fee, tape sequence | one counterparty-linked record |
| Bar | endogenous OHLCV or zero-volume carried close | one per symbol and step |
| News | timestamped exogenous event | read from input bundle |

The time unit inherits the dataset timestamp cadence. This is a modeling convention and is not
yet calibrated to any real venue's message or auction clock.

#### Process overview and scheduling

At a step, all agents observe the same public bar/news state plus their private portfolio. They
submit orders without observing other agents' current-step submissions. The exchange applies a
deterministic shuffle from `(replica seed, step)`, processes orders serially, skips self-matches,
fills crossing quantity at the resting price, records the counterparty-linked tape, snapshots
remaining depth, expires all remaining limits, and synthesizes an endogenous bar. A no-trade
symbol carries its prior close with zero volume.

The runner clips simultaneous orders against cash, inventory, position limits, and fee reserves
before submission. Unfilled buys cannot finance sells, and unfilled sells cannot finance buys.
The ledger rejects fills that would create negative cash, negative inventory, or a position above
the cap.

#### Design concepts

- Common random numbers are used only where specified by a paired design.
- Arrival is randomized within a step but reproducible from the replica seed.
- Public feedback occurs through completed bars; agents do not observe the intra-step book.
- A trade creates equal buyer and seller quantities and charges each side separately.
- Background liquidity, fundamental demand, noise demand, and persistent orders are **not yet
  implemented**.
- Cancel/replace messages, latency, queue position across steps, dividends, borrowing, shorting,
  and exchange halts are **not modeled**.

#### Initialization and input data

Input bars seed each symbol's observation history and reference price; events seed public news.
The data-bundle hash covers every input file and metadata artifact. Agent endowments, position
caps, fees, tick size, observation window, order lifetime, seed, and assigned AI share must be
present in the release manifest. The current exchange requires a positive initial inventory if
long-only agents are expected to supply the sell side.

### STRESS: experiment report contract

#### Objectives and scenarios

The confirmatory objective is the prespecified simultaneous dose-response family across all six
AI-share levels. No threshold may be selected after seeing outcomes. Required stress dimensions
are arrival rule, initial endowment, tick size, fee, agent capital distribution, order-type mix,
book persistence, background-liquidity intensity, information regime, and replica seed.

#### Data collection

A release must preserve reconstructable submissions, clipped orders, book states, cancellations
or expirations, fills, counterparty-linked trades, endogenous bars, portfolios, failures, model
usage, and costs. The current run writer preserves decisions, fills, and portfolios but does **not**
yet export submissions, book snapshots, expirations, or the exchange trade tape. That is a release
blocker, even though these objects exist in memory.

#### Verification tests

The following invariants must pass property and interruption tests:

1. cash, inventory, and fees reconcile from the event stream;
2. each trade has one buyer and one different seller with equal quantity and price;
3. self-trades, negative inventory, negative cash, and over-cap positions are impossible;
4. simultaneous reservations remain valid under partial fills and gaps;
5. price-time priority and tick rounding are deterministic;
6. restart reproduces assignments and outcomes without duplicate model billing;
7. changing any input or exchange parameter changes the resolved hash; and
8. exchange analyses use endogenous bars and tape rather than the seeding dataset's future bars.

Implemented unit tests currently cover several conservation, self-trade, reservation, partial-fill,
and timestamp-alignment cases. They do not yet establish all eight release invariants for the
compiled H5 matrix.

#### Validation targets

Before confirmatory execution, an outcome-blind calibration split must freeze plausible target
ranges or empirical reference distributions for:

- quoted and effective spread;
- depth by distance from the best quote;
- volume, turnover, and fill rate;
- return volatility, autocorrelation, and tail behavior;
- temporary and persistent price impact by order size;
- no-trade frequency and duration; and
- wealth, inventory, and liquidity concentration.

Validation is multivariate. Matching one stylized fact cannot compensate for degenerate depth,
near-zero volume, mechanically carried prices, or implausible fill rates. Target choice, tolerance,
calibration data, and failed targets must be reported rather than tuned away.

#### Sensitivity, uncertainty, and stopping

Treat whole replicas as the independent units. Plot every replica and simultaneous uncertainty
bands over the complete dose-response. The blinded pilot may update replica counts from pooled
variance, completeness, throughput, and failure rates, but may not choose favorable endpoints,
AI-share thresholds, models, or simulator parameters from treatment effects. Provider failure,
parse failure, strict-grounding rejection, no-liquidity failure, and incomplete tape each receive
distinct terminal states.

### H5 release checklist

H5 remains disabled until all items are checked in a frozen commit:

- [ ] Persistent order lifetime and explicit cancel/expiry policy are implemented and tested.
- [ ] Seeded fundamental, noise, and background-liquidity agents are implemented and documented.
- [ ] Submissions, order events, book snapshots, expirations, fills, and tape are exported and
  reconstruct the same bars exactly.
- [ ] The compiled plan assigns all six AI shares to independent replicas with frozen blocking.
- [ ] Conservation, matching, leakage, restart, and hash-invalidating tests pass for every H5 cell.
- [ ] Calibration targets and tolerances are frozen on data disjoint from confirmatory replicas.
- [ ] Every mandatory market-quality target passes or the simulator is reported as invalid.
- [ ] Arrival, endowment, tick, fee, persistence, liquidity, order-type, and capital-share stress
  results are included without specification selection.
- [ ] `claims.json` labels all H5 claims `simulator_bounded` and links them to this report.

Until then, exchange runs are engineering diagnostics and cannot populate the manuscript.

## Human trust and AI-adoption forecasting

### H6 human trust and delegation

#### Human-subject requirement

`exp-013` is correctly marked `blocked_external`. Before data collection it requires ethics/IRB or
equivalent approval, consent language, eligibility criteria, recruitment and compensation plan,
power analysis, privacy/deidentification plan, adverse-event/contact procedure, preregistration, and
a human-study application that cannot place real trades.

The independent unit is the consented participant. Repeated vignettes and choices are clustered
within participant. The primary outcome should be incentive-compatible delegated capital share,
supplemented by advice acceptance, autonomous-management choice, confidence, comprehension, and
revocation behavior. Pure attitude ratings are secondary.

Randomize, in balanced order:

- AI identity disclosure versus human-adviser control;
- advice-only, human-review, and autonomous execution;
- independently audited versus asserted performance evidence;
- explanation availability and uncertainty disclosure;
- ordinary versus stressed market conditions; and
- reversible versus locked delegation.

Use identical fees, historical evidence, risk, and outcome distributions across labels. Include
attention/comprehension checks without conditioning the primary effect on post-treatment variables.
Analyze at participant assignment level with participant-clustered intervals and nonresponse/
attrition sensitivity. Test heterogeneous effects only in frozen families.

Required outputs are `h6_deidentified_choices.parquet`, `h6_effects.parquet`, and
`h6_inference.json`, plus `human_study_verification.json` containing approval identifier, consent
version, randomization audit, exclusions, deidentification checks, and sample reconciliation. Raw
identifiers and free text must never enter the public repository.

`exp-014` is a simulation of recommendation compliance, latency, and sizing noise. Its outputs,
`advisor_transmission.parquet` and `advisor_thresholds.json`, answer how convergence survives stated
executor assumptions. They do not answer whether humans trust AI.

### H7 adoption forecasting

`exp-015` joins a verified adoption time series to the full distribution of H5 thresholds. Inputs
must identify what is measured—AI advice exposure, assets with AI recommendations, or autonomous
AI-controlled capital. These quantities are not interchangeable. Sources need retrieval dates,
definitions, coverage, revisions, and uncertainty; vendor marketing estimates are sensitivity
inputs, not ground truth.

Use multiple diffusion/forecast models, rolling forecast origins, and backtests at historical
origins. Combine adoption and H5 threshold uncertainty by simulation without replacing either with
a point estimate. Publish named scenarios rather than a single deterministic curve. “Soon” must be
fixed before analysis, for example within 1, 3, or 5 years.

The estimand is the conditional probability and date distribution for crossing the simulated H5
threshold under each adoption definition and scenario. Report calibration, interval coverage,
model weights, threshold-not-reached probability, and sensitivity to structural breaks. The claim
must read:

> Under scenario S, adoption measure A, and simulated threshold definition T, the estimated
> crossing probability within horizon H is P with interval I.

It must not read “AI will change markets by date D.”

Exact outputs are `adoption_scenarios.parquet`, `threshold_forecasts.parquet`, and
`forecast_calibration.json`. Users see scenario fans, rolling-origin errors, calibration plots, and
threshold-crossing probability curves. They verify source hashes, reproduce each forecast origin,
and confirm that scenario labels are never presented as observed facts.

### Readiness and verification

Run `uv run flock validate --output readiness.json` and inspect both `scaffold_ok` and
`execution_ready`. The verifier exposes human-study and adoption-data dependencies as blockers.
H5–H7 claims are releasable only when their exact research-program outputs exist, independent units
reconcile, practical thresholds were frozen, and the study-specific verification file passes.

## AI trading-agent input attribution and local mechanisms

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

### Evidence boundary

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

### Questions and estimands

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

### Lane A: closed-API black-box attribution

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

### Lane B: local open-weight mechanisms

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

### H13 precision mechanisms and transfer

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

### H12 pressure mechanisms

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

### Practical thresholds and multiple testing

Freeze target-specific SESOIs before confirmation. Recommended defaults are 0.10 standardized
target-score change, 0.05 absolute action/abstention probability, or 0.10 recovered fraction for an
activation patch, with a +0.01 adverse noninferiority margin for fabrication or hard-constraint
failure. Null claims require TOST against a frozen equivalence band; nonsignificance is not evidence
that a feature is unused.

Black-box feature families and local intervention families receive separate Holm corrections in
confirmation. Discovery maps use false-discovery-rate control and may not be relabeled
confirmatory. Layer, token, head, sparse feature, target, direction, and prompt family all count
toward the declared multiplicity family.

### Exact outputs

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

### How users verify and see results

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

## Simulation-to-real attribution

This protocol defines the path from a causal effect inside the configurable simulation to a
carefully bounded statement about real markets. The contracts are `exp-018` through `exp-021` in
[`configs/research-program.yaml`](../../configs/research-program.yaml).

### The evidentiary ladder

| Tier | Question | Allowed label | Causal status |
|---|---|---|---|
| 1. Simulation truth | What changes when AI participation is randomized in simulation? | Simulated AI effect | Causal inside the specified simulator |
| 2. Signature discovery | Which public features distinguish simulated AI/no-AI replicas? | Simulation signature | Predictive, held-out within simulation |
| 3. Transport | Does the locked signature retain calibration out of domain? | Transported signature | Predictive in validated domains |
| 4. Real detection | Where does the signature appear in real market windows? | AI-like event | Observational, not causal |
| 5. Exposure attribution | Does verified AI exposure change the outcome versus a credible counterfactual? | AI-caused effect | Causal only under the stated design assumptions |

An AI-like pattern is not evidence that AI caused it. Common strategies, shared news, index flows,
funding shocks, execution algorithms, market structure, or chance can produce similar signatures.
Detection is a prerequisite for some attribution designs, never a substitute for exposure and a
counterfactual.

### H9: Discovering simulation signatures

#### Inputs and split discipline

`exp-018` requires verified shared-market replicas with randomized AI participation, complete
order/book/tape logs, known treatment labels, market regimes, agent/capital shares, and all
simulation seeds. Candidate public features may include herding, flow persistence, synchronized
capital breadth, order timing, size discretization, cancellation behavior, price impact, spreads,
depth, volatility, and cascade structure.

Split by entire trajectory lineage before feature selection. Replicas sharing a market seed,
fundamental path, prompt cache, or derived perturbation family stay in one fold. Nested cross-
validation performs feature selection and tuning inside training folds. The locked test set is used
once. Placebo labels and classical-crowding controls measure how easily the detector mistakes
ordinary convergence for AI.

The independent unit is the held-out market replica. Orders, agents, events, and windows within a
replica are nested. Primary metrics are discrimination, precision-recall at frozen prevalence,
calibration error, Brier/log loss, false-positive rate on non-AI crowded controls, and stability
across regimes and model families.

Exact outputs are `signature_library.parquet`, `simulation_predictions.parquet`, and
`discovery_metrics.json`. `signature_library.parquet` freezes feature IDs, transformations,
lookbacks, model coefficients/parameters, training hashes, intended market domain, and thresholds.

### H9: Transport validation

`exp-019` applies the locked signature without refitting to unseen simulated regimes and then a
real-market feature panel. Temporal separation must be strict. The real panel needs instrument,
venue, timestamp, corporate-action, trade/quote, and data-cleaning provenance appropriate to each
feature. Domain-shift diagnostics compare feature support, missingness, dependence, and calibration.

The independent unit is a nonoverlapping held-out market window; overlapping windows share a
dependence cluster. Estimate external discrimination where labels exist, calibration drift,
prediction-set coverage, and change from simulation performance. If labels do not exist in real
markets, calibration cannot be claimed from score distributions alone.

Exact outputs are `transport_predictions.parquet`, `transport_metrics.json`, and
`domain_shift.json`. A failed transport gate ends population use of that signature; it may remain a
simulation-only result.

### H10: Real-market AI-like detection

`exp-020` applies only transport-approved, preregistered signatures to nonoverlapping real windows.
It estimates calibrated score and event prevalence where calibration support exists. Every detected
row must include:

- event/window ID, venue, instrument universe, and time bounds;
- locked signature/version and input-feature hashes;
- score, threshold, uncertainty, calibration domain, and domain-shift flag;
- negative-control and data-quality results; and
- `causal_status: ai_like_not_attributed`.

Outputs are `ai_like_events.parquet` and `detection_calibration.json`. The report shows timelines,
score distributions, expected false positives, negative-control periods, feature contributions, and
domain-shift warnings. It must not rank an institution or trader as AI-operated without verified
exposure evidence and an authorized disclosure basis.

### H10: Causal attribution to AI

`exp-021` is blocked until both requirements exist:

1. **Verified exposure:** independently documented model deployment/advice or AI-controlled capital,
   with institution/desk/product scope, start/end time, autonomy, affected assets, capital, model
   family/revision when available, and provenance/permission.
2. **Credible counterfactual:** randomized or staggered rollout, an externally caused natural
   experiment, a defensible discontinuity/instrument, or another preregistered design that estimates
   what would have occurred without that exposure.

The exposure definition must precede outcome inspection. Self-reported “uses AI,” generic software
procurement, or an AI-like detector score is not verified exposure. Exposure timing must precede the
outcome and cannot be backfilled from the detected event.

The independent unit and estimator follow the identification design, for example institution-
market-time rollout clusters in a randomized/staggered deployment. Mandatory falsifications include
pretrend/event-study diagnostics, placebo dates, placebo assets/outcomes, negative-control exposure,
spillover/interference checks, anticipation windows, concurrent-policy/deployment checks, and
unmeasured-confounding sensitivity. Standard errors cluster at the assignment/exposure level, not
the trade row.

Required outputs are:

- `causal_analysis_panel.parquet`: exposure, outcome, covariates, assignment, cluster, and provenance;
- `causal_effects.parquet`: frozen estimands, effects, intervals, and multiplicity;
- `falsifications.json`: every planned placebo, pretrend, spillover, and sensitivity result;
- `exposure_provenance.jsonl`: source, permission, timestamp, and verification records; and
- `causal_attribution_verification.json`: identification and claim-language verdict.

A causal claim is permitted only when exposure provenance passes, the counterfactual design is
credible, temporal order is correct, required falsifications do not invalidate the design, and the
effect survives frozen sensitivity/multiplicity rules. Otherwise publish the score as AI-like or
the analysis as inconclusive.

### Existing repository support and missing pieces

The repository currently computes herding/cascade features in
[`analysis/coordination.py`](../../src/flock/analysis/coordination.py), convergence features in
[`analysis/convergence.py`](../../src/flock/analysis/convergence.py), and strategy fingerprints in
[`analysis/strategy.py`](../../src/flock/analysis/strategy.py). The SEC 13F reference builder in
[`data/builders/real_world_refs.py`](../../src/flock/data/builders/real_world_refs.py) can create a
quarterly institutional-holdings anchor with:

```bash
export EDGAR_USER_AGENT='flock research your-email@example.com'
uv run flock data build refs13f
```

That 13F panel is an external convergence anchor; it is not an AI exposure registry and cannot
identify AI causation. There is currently no detector-training, real-market feature-panel,
exposure-registry, or causal-estimator CLI. `exp-018` is scaffolded; `exp-019`–`exp-021` are blocked
on the declared external data and runner dependencies.

### How users verify and see results

Run `uv run flock validate --output readiness.json` to see the explicit blockers rather than a
silent readiness pass. For each completed tier, users should:

1. verify input and split hashes and confirm trajectory-lineage separation;
2. reproduce nested cross-validation and the one-time locked test evaluation;
3. compare calibration and false positives against placebo/crowding controls;
4. inspect `domain_shift.json` before interpreting a real score;
5. confirm every real event says `ai_like_not_attributed` unless exposure verification passes;
6. reproduce pretrends, placebos, spillover tests, and sensitivity for any causal effect; and
7. trace each report figure/table to its exact prediction/effect row and signature/exposure version.

The final report should visibly separate simulation truth, transported performance, AI-like real
events, and causally attributed effects into different sections and colors. They must never be
merged into one “AI events” count.

## H13 financial-chain propagation design

### Core question

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

### Error propagation

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

### Customization output

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

### Success criterion

The project succeeds if it maps where a low-cost configuration is equivalent, noninferior, or
materially different on frozen financial, behavioral, convergence, safety, and trajectory margins;
replicates the result on held-out domains or model families; and reports the cost per verified
chain and decision. Nonsignificance is not equivalence. Convincing prose, final-answer accuracy
alone, or one open checkpoint cannot establish fidelity or a general mechanism.

## Metrics and outcome definitions

All metrics are computed within-cohort and reported alongside the null-cohort value and a
marginal-preserving chance floor. Implementations live in `src/flock/analysis/`.

### Notation

Cohort *C* with agents *i = 1..n*; steps *t = 1..T*; symbols *s*. Agent *i*'s action at *(t, s)*
is *a_i(t,s) ∈ {buy, sell, hold}* with signed size *q_i(t,s)*. Position vector *w_i(t)* is the
agent's portfolio weights at *t*.

### Decision-level convergence (`convergence.py`)

- **Pairwise action agreement**: for each pair (i, j),
  `A_ij = mean_t,s [ 1{a_i(t,s) = a_j(t,s)} ]`. Cohort statistic: mean over pairs.
- **Chance-corrected agreement (Cohen's κ)** per pair, using each pair's empirical action
  marginals; cohort mean κ. This is the primary decision-level statistic (robust to hold-heavy
  behavior).
- **Trade-direction correlation**: Pearson correlation of sign(q_i) with sign(q_j) over (t, s)
  cells where at least one trades.

### Portfolio-level convergence (`convergence.py`)

- **Position cosine similarity**: `cos(w_i(t), w_j(t))` averaged over t and pairs.
- **Portfolio overlap** (fund-overlap style, comparable to 13F panels):
  `O_ij(t) = Σ_s min(|w_i(t,s)|, |w_j(t,s)|)` for long weights; cohort mean over pairs, t.
- **Return correlation**: correlation of per-step portfolio returns across agents.

### Strategy-level convergence (`strategy.py`)

- **Strategy fingerprint**: regress agent i's signed trade flow on canonical signals computed
  from market data only — momentum (12-1 style lookback), short-term reversal, distance from
  moving average, realized volatility. The coefficient vector β_i is the fingerprint.
  **Fingerprint dispersion** = mean pairwise Euclidean distance between standardized β_i.
- **Rationale clustering**: embed decision rationales (locally, hash-TF-IDF by default so the
  pipeline stays offline; sentence-embedding model optional) and report mean pairwise cosine
  similarity plus cluster count at fixed threshold.

### Headline dispersion statistic

For any similarity metric *m* above, define **dispersion** `D(C) = 1 − mean_pairs m`.
H1 reports both the ecology-averaged technology contrast and the technology-by-ecology interaction
defined in the statistical contract. Their directions and exact decision rules remain unfrozen.
Inference uses the frozen cluster-aware top-level-unit procedure; permutation or sign-flip output
is sensitivity analysis only for H1. Report κ as primary, followed by portfolio overlap and
fingerprint distance converted to a similarity through negative standardization.

The implementation scores actions on the full `(step, symbol)` grid. Portfolio-net actions are
retained only for display; they are not the confirmatory endpoint because offsetting buy/sell
orders could otherwise be mislabeled as a hold.

### Breadth and market-dynamics outcomes

- **Convergence breadth (H2b):** fraction of investors, capital, assets, and consecutive periods
  contained in a convergence cluster above a preregistered threshold. Pairwise convergence and
  breadth are separate estimands.
- **AI-share dose response (H5):** paired change from the zero-AI market in impact, realized
  volatility, spreads, depth, efficiency, tail loss, cascade frequency, and capital-weighted
  synchronization. The unit is a whole independently randomized market replica.
- **Trust/adoption (H6/H7):** incentive-compatible delegated share and conditional threshold-
  crossing distributions. Stated trust is secondary to revealed delegation.
- **Transport/detection (H9/H10):** held-out discrimination and calibration. Detection is not a
  causal endpoint; H10 additionally requires verified exposure and a credible counterfactual.

### Quality, suitability, and safety outcomes

Prompt-pressure results use normalized regret against a constrained benchmark, goal attainment,
shortfall probability, liquidity preservation, drawdown, turnover, hard-constraint violations,
unsupported evidence, fabricated facts, unsupported certainty, and abstention. “Better” requires
practical quality improvement plus safety/suitability noninferiority. “Equivalent” requires TOST;
a nonsignificant difference is inconclusive.

### H13 local fidelity and quantization propagation

H13 reports three references separately: financial-scoring-key correctness, same-checkpoint
full-precision loss, and local-to-frontier behavioral similarity. Its headline families are:

- **Behavioral fidelity:** exact program and terminal-answer accuracy, item-level action agreement,
  Cohen's κ, total-variation distance where output distributions are available, signed-quantity
  error, portfolio distance, strategy-fingerprint distance, normalized regret, calibration,
  abstention, and hard-constraint or unsupported-claim rates.
- **Convergence transport:** difference between within-local and within-frontier cohort
  convergence, cross-model paired agreement on the same observations, and each class's difference
  from the matched classical benchmark. Aggregate similarity and identical error choices are
  distinct outcomes.
- **Customization fidelity:** distance and rank agreement between paired client-fact intervention
  effect vectors for risk capacity, horizon, liquidity, dependents, tax constraints, mandate
  limits, and information access, reported with suitability and constraint outcomes.

For a chain of dependency depth *d*, let *T* be the first invalid operation or value. Report the
gold-prefix next-step error by depth, the free-running first-error hazard
`P(T = k | T ≥ k)`, survival `S(d) = P(T > d)`, terminal numerical drift, decision-threshold
flip rate, recovery probability after an injected error, and a preregistered standardized terminal-
to-injected-error amplification measure. Cross context length with dependency depth so retrieval
failure is not called propagation.

Replay reports time to first action and persistent portfolio divergence, divergence growth rate,
and the state-mediated amplification contrast between endogenous-state and shadow-state runs.
Reset horizons `{1, 5, 20, all}` form a propagation-length dose response. Mechanistic outputs add
same-tokenizer logit divergence, top-token flips and margin collapse, layerwise activation drift,
SAE feature preservation, and target recovery under two-direction activation patches. These are
invalid for closed APIs or cross-tokenizer comparisons.

The independent unit is a held-out template family, company/document cluster, or market block.
Generated questions, numerical instantiations, chain steps, tokens, model calls, layers, patches,
agents, and reset horizons are nested. The local-frontier bridge uses equivalence tests; the
same-checkpoint precision study uses paired precision-by-depth-by-family models. Behavioral,
propagation, customization, and mechanistic confirmation are separate multiplicity families.

### Herding / coordination (`coordination.py`, Phase 2 + real-world panels)

- **LSV herding statistic** (Lakonishok–Shleifer–Vishny 1992): for each (t, s),
  `H(t,s) = |p(t,s) − E[p(t)]| − AF(t,s)` where p is the fraction of active traders buying and
  AF the adjustment factor under binomial null. Cohort statistic: mean over (t,s) with ≥k
  active traders. Also computed on 13F and prediction-market panels for H2.
- **Sias (2004) serial herding**: cross-sectional correlation of standardized buyer fractions
  between t−1 and t, decomposed into own-persistence and following components.
- **Cascade detection**: runs of consecutive steps with one-sided net cohort flow beyond a
  null-calibrated threshold; report cascade frequency, length, and depth (price move during
  cascade, Phase 2 only).
- **Liquidity withdrawal** (Phase 2): book depth around mid before/after cohort-wide sells.


### Reporting rules

- Every figure/table states: cohort sizes, top-level-unit count, nested seed count, chance floor,
  null-cohort value, and interval.
- No metric is reported in isolation; the pre-registered hierarchy (κ → overlap → fingerprint)
  is always shown together.
- Every claim records its independent unit, effect, interval, raw and corrected p-value or
  equivalence verdict, sensitivity checks, config/data hashes, and linked output artifact.

## Statistical analysis contract

This document is the operational statistical contract for the expanded research program. It
extends [Metrics and outcome definitions](#metrics-and-outcome-definitions) and must be reconciled with and frozen through
[Preregistration](preregistration.md) before confirmatory provider calls. If the documents
conflict after freeze, the tagged preregistration and its dated amendments control.

### Core principles

1. Define the scientific question, estimand, independent unit, and assignment before choosing a
   test.
2. Randomize and infer at the level where treatment is independently assigned.
3. Preserve paired structure through common market randomness.
4. Treat agents, pairs, steps, assets, paraphrases, retries, and calls as nested observations.
5. Report effect sizes and uncertainty; a p-value is not a measure of practical importance.
6. Use equivalence and noninferiority tests for sameness and safety claims.
7. Freeze confirmatory families and margins before outcomes are inspected.
8. Separate simulated causation, real-market detection, and real-market causal attribution.

### Question-to-analysis registry

Every executable experiment must have one frozen registry row with these fields:

| Field | Required content |
|---|---|
| `question_id` | H1–H13 or named secondary question |
| `population` | Exact markets, windows, models, profiles, and prompts covered |
| `treatment` / `control` | Fully rendered and hashed conditions |
| `estimand` | Mathematical contrast and aggregation weights |
| `independent_unit` | Unit independently assigned or sampled |
| `blocking` | Market, model, provider, regime, profile, and seed strata |
| `endpoint` | Primary, secondary, diagnostic, or safety role |
| `SESOI` | Smallest practically important benefit/harm |
| `equivalence_margin` | Symmetric or asymmetric negligible-effect interval |
| `noninferiority_margin` | Maximum acceptable adverse safety/suitability change |
| `missingness_rule` | Failure, retry, safeguard, and partial-block handling |
| `inference` | Randomization test/model and confidence interval |
| `multiplicity_family` | Family name and correction/gatekeeping order |
| `output` | Artifact and table/figure destination |

An analysis without this row is exploratory regardless of the language used in its report.

### Independent units

| Design | Independent unit | Nested, non-independent observations |
|---|---|---|
| Historical or synthetic replay | Nonoverlapping independent trajectory or nonoverlapping market-window block | Agents, pairs, symbols, steps, calls, prompts |
| Shared exchange | Independently initialized market replica | Traders, orders, fills, book updates, calls |
| MPHIQ or pressure pairing | Block receiving all paired conditions | Scheme/cell observations and Hamming pairs |
| Real-investor panel | Independently sampled manager/trader cluster and nonoverlapping period, subject to panel dependence model | Holdings, assets, quarters, trades |
| Human trust/delegation | Consented participant | Vignettes, repeated choices, response items |
| Adoption forecast | Independent forecast origin/source series | Horizons and scenarios from that origin |
| Local mechanistic study | Held-out observation-by-checkpoint intervention block | Layers, heads/features, tokens, patches |
| H13 financial-chain study | Held-out template family, company/document cluster, or market block paired across model/precision conditions | Generated items, numerical variants, chain steps, tokens, calls, reset horizons |
| Real-market causal study | Unit assigned/exposed under the identification design | Trades and timestamps within that unit |

Nonoverlapping market windows are preferred. Overlapping windows share a dependence cluster and do
not independently increase `n`. A model sampling seed alone does not create a new market replicate.
Repeated API calls answer response-variability questions; they do not create independent evidence
that market dynamics changed.

### Prohibited pseudoreplication

The following practices are invalid:

- using agent-step rows as the sample size for a market-level treatment;
- treating every pairwise similarity as independent when pairs share agents;
- treating prompt paraphrases, retries, cache misses, or repeated calls as independent blocks;
- treating assets inside one common market shock as independent replications without clustering;
- counting overlapping historical windows as independent;
- pooling simulated agents and human participants into one inferential sample; or
- training and evaluating a detector on replicas from the same market seed or trajectory family.

Pairwise metrics must be aggregated to the independent block or modeled with a preregistered dyadic
or multi-membership structure. Cluster-robust standard errors with very few clusters are not a
substitute for adequate replication; use randomization inference and small-sample corrections.

### Primary estimands

| Program question | Primary estimand | Unit-level contrast |
|---|---|---|
| H1 ecology-averaged technology contrast | `½[(κ[LLM,hom] − κ[classical,hom]) + (κ[LLM,het] − κ[classical,het])]` | Independent trajectory or nonoverlapping-window block |
| H1 technology-by-ecology interaction | `(κ[LLM,hom] − κ[LLM,het]) − (κ[classical,hom] − κ[classical,het])` | Independent trajectory or nonoverlapping-window block |
| H2 real-investor comparison | LLM minus matched real-panel convergence | Matched-frequency/activity panel block |
| H2b convergence breadth | AI-share effect on synchronized capital/participant/asset coverage | Market replica or matched panel period |
| H3 lineage | Within-lineage minus cross-lineage similarity | Block-aggregated dyadic contrast |
| H4 profile versus information | Information decorrelation minus profile decorrelation | MPHIQ block |
| H5 market dynamics | AI-capital-share dose response and threshold | Shared-market replica |
| H6 trust/delegation | Randomized disclosure/oversight effect on delegated share | Participant |
| H7 near-term crossing | Calibrated probability/date distribution for H5 threshold crossing | Forecast origin |
| H8 causal inputs/mechanisms | Paired output change under input or activation intervention | Intervention block |
| H9 signature transport | Locked detector discrimination/calibration on held-out domain | Held-out replica or period |
| H10 real AI causation | Assignment/exposure effect under a credible counterfactual | Design-specific exposure unit |
| H11 actionable dataset | Predefined data-quality, calibration, and utility metrics | Independently held-out dataset unit |
| H12 pressure | Factorial pressure effect on quality, safety, behavior, and convergence | Pressure block |
| H13 local fidelity | Local-versus-frontier equivalence and same-checkpoint precision-by-depth propagation | Held-out template/document/market block |

The sign and exact success rule for both H1 contrasts remain unfrozen. Consolidation does not
choose a scientific direction; the preregistration must resolve both before confirmatory calls.

Real-market pattern resemblance estimates detection, not cause. H10 causal language requires
verified AI exposure plus randomized deployment, a defensible natural experiment, or another
specified counterfactual. Without that, results must be labeled “AI-like,” never “AI-caused.”

H13 contains two nonexchangeable analyses. The cross-model bridge estimates descriptive
equivalence or difference between deliberately sampled local and frontier endpoints; model class
is not randomized. The quantization analysis uses paired variants of one immutable checkpoint to
estimate precision effects, with a deterministic financial scoring key for correctness. The primary
propagation model estimates precision×dependency-depth×family effects on conditional step-error
hazard and chain survival, then a paired endogenous-minus-shadow-state contrast for replay
amplification. Generalization beyond sampled models requires an untouched family-level test, not a
significant pooled model coefficient.

### Randomization inference

For H1, technology labels are not randomized. Use the top-level-unit, cluster-aware model frozen
through outcome-blind simulation, with an appropriate small-sample or wild-cluster procedure. A
paired sign-flip test is sensitivity analysis only under an explicit symmetry assumption; it is not
design-based randomization inference. For experiments with genuinely randomized assignment,
calculate one treatment contrast per independent block and permute according to the actual blocked
assignment mechanism. Report the randomization seed, assignment set, and attainable minimum p-value.

For multi-arm or dose-response experiments, permute treatment according to the actual blocked
assignment mechanism, not unrestricted row labels. For human studies, preserve participant-level
assignment and cluster repeated choices by participant. For observational panels, randomization
inference is unavailable unless justified by the design; use a prespecified panel model and report
identification assumptions and sensitivity analyses.

Confidence intervals must resample independent blocks or use a compatible hierarchical model.
Bootstrap resampling of calls, steps, or pair rows is prohibited. BCa intervals require enough
independent blocks for stable acceleration; otherwise use randomization intervals, wild-cluster
bootstrap, or a clearly labeled small-sample alternative.

### Practical thresholds

These defaults apply until replaced before preregistration freeze using synthetic calibration,
domain expertise, and power simulation:

| Endpoint | Benefit/harm SESOI | Equivalence margin | Safety noninferiority margin |
|---|---:|---:|---:|
| Cohen's kappa | 0.10 absolute | ±0.05 | — |
| Portfolio overlap | 0.05 absolute | ±0.03 | — |
| Capital-weighted synchronization/breadth | 0.05 absolute | ±0.03 | — |
| Normalized regret, 0–1 | 0.05 | ±0.025 | +0.025 adverse |
| Goal-attainment or shortfall probability | 0.05 absolute | ±0.025 | 0.025 adverse |
| Trade/abstention probability | 0.05 absolute | ±0.03 | — |
| Hard-constraint/fabrication/unsupported-claim rate | — | ±0.005 | +0.01 adverse |
| Executable program or terminal-answer accuracy | 0.05 absolute | ±0.03 | +0.03 adverse |
| First-step error hazard or chain survival | 0.05 absolute | ±0.03 | +0.03 adverse |
| Spread, depth, volatility, or price impact | 0.20 baseline SD | ±0.10 SD | 0.10 SD adverse when a safety endpoint |
| Human delegated-capital share | 0.10 absolute | ±0.05 | — |

Raw-unit thresholds take precedence over standardized thresholds when interpretation is clearer.
Margins must not be chosen from observed confirmatory effects. Report estimates against zero, the
SESOI, and all equivalence/noninferiority boundaries.

### Significance, equivalence, and noninferiority

- **Difference/superiority:** reject the null and show the confidence interval exceeds the SESOI in
  the prespecified direction for a practically important claim.
- **Equivalence:** perform TOST at the family-adjusted alpha and require the entire compatible
  interval to fall inside the frozen lower and upper equivalence bounds.
- **Noninferiority:** test the one-sided adverse bound; all mandatory safety/suitability endpoints
  must pass.
- **Inconclusive:** use when intervals include meaningful benefit and harm, or when a difference is
  nonsignificant but equivalence was not established.

“No significant difference,” `p > 0.05`, overlapping confidence intervals, or low power never prove
sameness. A quality benefit with failed safety noninferiority is not a successful treatment.

### Multiple testing

Before unblinding, create named families with one row per planned contrast:

- First-paper confirmatory family: the frozen ordered H1/H3/H4 contrasts with Holm control unless
  the preregistration uses a stricter hierarchical gate.
- H2: descriptive and outside the first-paper multiplicity family.
- H5: a separate simulator-only family using its actual randomized share assignment.
- MPHIQ main effects: one five-contrast Holm family.
- MPHIQ interactions: separate preregistered Holm family; higher-order discovery uses BH-FDR.
- H12 pressure: six-contrast Holm family defined in
  [Prompt-pressure protocol](#prompt-pressure-protocol).
- Profile matched sets: one nine-contrast Holm family per endpoint tier.
- Safety: conjunctive noninferiority; every required endpoint must pass.
- Mechanistic features: discovery and confirmation must use separate data; discovery uses FDR and
  held-out confirmation uses Holm over the frozen feature set.
- H13 behavioral fidelity, chain propagation, customization, and mechanistic transfer are four
  separate frozen families. Model sizes, precisions, depths, contexts, error positions, replay
  reset horizons, outcomes, and feature sites all count toward their declared family.
- Detector feature selection: nested inside training folds; the locked test set is evaluated once.

Always report the family name, number of hypotheses, raw p-value, adjusted p-value, adjusted alpha
or interval, effect, and margin. Creating narrower post-hoc families is prohibited. Exploratory
results must remain labeled exploratory even if small p-values survive FDR control.

### Power and replication

Determine independent-block counts by simulation using the full assignment, within-block
correlation, model/provider heterogeneity, dyadic aggregation, missingness, and intended correction.
Do not infer power from agent or call count. The pilot may estimate nuisance variance but must not
select confirmatory endpoints or favorable models based on outcomes.

Use a blinded stop/go rule based on data completeness, variance, cost, and safety failure rates.
Re-estimation of sample size may use blinded pooled variance. If effect estimates are examined,
adaptation requires a preregistered group-sequential rule and alpha accounting. Confirmatory data
must use trajectories, nonoverlapping windows, and model revisions held out from design development
where feasible. A response seed remains nested unless it generates a genuinely independent
trajectory under the frozen data-generating process.

For H13, use 8–12 discovery clusters only for engineering and nuisance estimates, simulate power
for roughly 24–32 paired confirmatory clusters, and allow a blinded interval-width re-estimation to
a hard cap near 48 only if frozen in advance. A 25–50-item-per-depth local screen is a nested
precision diagnostic, not 25–50 independent replications. Stop a cell for futility only when the
attainable interval cannot resolve its frozen difference/equivalence claim; failure to establish
equivalence remains inconclusive.

### Missingness and failures

Every planned unit receives one terminal status: complete, provider failure, parse failure,
safeguard rejection, infeasible order, or missing. Retries remain linked to the original call.
Voluntary hold, parse-failure hold, safeguard hold, and constraint-forced hold are distinct outcomes.

Partial independent blocks are not silently analyzed. The default is to rerun the missing cell under
the frozen retry policy or mark the block incomplete. Any complete-case analysis and inverse-
probability sensitivity must be prespecified. Report failure rates by treatment, model, provider,
and block because treatment-dependent failure is itself an outcome.

### Model and population scope

Provider/model effects are fixed effects when the tested releases were deliberately selected. A
claim about the broader frontier-model population requires an explicit sampling frame, multiple
independent model families, random or defensible selection, and provider-family sensitivity.
Changing API revisions during a study creates a new model level. Cached responses preserve
reproducibility but do not remove model-release scope limitations.

Real-investor comparisons must match time aggregation, eligible assets, activity thresholds, long
versus short treatment, and capital weighting. If direct matching is impossible, report separate
estimands and avoid ranking them as though identical.

### Required statistical outputs

Every confirmatory study writes:

- `estimand_registry.json`: frozen question and analysis rows.
- `randomization_plan.json` and `realized_assignments.parquet`.
- `independent_units.parquet`: one row per actual replication unit and terminal status.
- `block_effects.parquet`: unit-level contrasts used for inference.
- `effects.parquet`: estimates, intervals, SESOIs, and equivalence/noninferiority margins.
- `multiplicity.json`: family membership, raw and adjusted results.
- `equivalence_noninferiority.json`: TOST and one-sided safety decisions.
- `missingness_failures.parquet` and `sensitivity_results.parquet`.
- `statistical_verification.json`: automated audit verdicts.
- `claims.json`: each claim linked to its estimand, data hashes, table, and figure.

Reports must show independent `n`, nested observation counts separately, unit-level effect plots,
raw action/failure distributions, adjusted and unadjusted results, and robustness across model,
provider, market, regime, and profile blocks.

### Statistical verification checklist

Release fails closed unless an automated audit confirms:

- every confirmatory claim resolves to one frozen estimand row;
- the reported independent `n` equals the independent-unit artifact;
- block IDs are unique and overlapping windows share a dependence cluster;
- assignment and analysis permutations reproduce the actual randomization;
- paired cells share required market paths and non-treatment hashes;
- no agent, pair, call, step, paraphrase, or retry is counted as independent evidence;
- all planned cells and failures reconcile;
- margins were frozen before outcome access;
- equivalence uses TOST and safety uses the declared noninferiority direction;
- multiplicity families include every planned contrast;
- held-out, discovery, and confirmatory datasets are disjoint by trajectory lineage;
- causal language matches the identification design; and
- all tables and figures regenerate from hashed analysis inputs.

The audit output must include executable reproduction commands, package/code versions, random
seeds, data/config hashes, and an explicit pass/fail status. A failed gate blocks confirmatory
release; it may be reported only as a labeled diagnostic or failed-run artifact.

## Pipeline

The pipeline should be understood as a chain:

```text
input market data
  -> observations shown to agents
  -> prompts / agent decision functions
  -> structured decisions
  -> orders
  -> fills
  -> portfolios
  -> convergence / coordination metrics
  -> statistical inference
  -> figures / tables / paper claims
```

Every claim should be traceable through this chain.

If a result seems surprising, debug it by walking backward:

```text
claim
  -> metric
  -> portfolio / decision rows
  -> fills
  -> orders
  -> observation
  -> input data
  -> dataset builder / config / seed
```

---
## Project components

#### Data layer

Location:

- `src/flock/data/`
- `src/flock/data/builders/`
- `datasets/`

Purpose:

- Build, store, hash, and load market datasets.

Important outputs:

- `bars.parquet`
- `events.parquet`
- `meta.json`
- `datasets/manifests.json`

---

#### Agent layer

Location:

- `src/flock/agents/`

Purpose:

- Define trading agents.
- Implement baseline strategies.
- Implement LLM agent prompting and JSON parsing.
- Connect to providers.
- Cache LLM responses.

Agent types:

- LLM agents.
- Momentum baseline.
- Mean-reversion baseline.
- Market-maker baseline.
- Buy-and-hold baseline.
- Random/null baseline.

---

#### Market layer

Location:

- `src/flock/markets/`

Purpose:

- Simulate how orders become fills.

Modes:

1. Replay market
   - No interaction between agents.
   - No price impact.
   - Historical/synthetic prices are replayed.
   - Best for isolating independent strategy convergence.

2. Shared exchange
   - Agents interact through an order book.
   - Prices can be affected by agent flow.
   - Best for studying emergent coordination, cascades, and liquidity effects.

---

#### Experiment layer

Location:

- `src/flock/experiments/`
- `configs/experiments/`
- `configs/sweeps/`

Purpose:

- Load experiment configs.
- Build markets and agents.
- Run agent decisions over time.
- Log decisions, fills, portfolios, and manifests.

Important result files:

- `results/<run-id>/decisions.jsonl`
- `results/<run-id>/fills.parquet`
- `results/<run-id>/portfolio.parquet`
- `results/<run-id>/manifest.json`

---

#### Analysis layer

Location:

- `src/flock/analysis/`

Purpose:

- Compute convergence metrics.
- Compute coordination/herding metrics.
- Run permutation tests and bootstrap confidence intervals.
- Generate reports and figures.

Important report files:

- `results/<run-id>/report.md`
- `results/<run-id>/report/convergence_by_cohort.png`
- `results/<run-id>/report/kappa_heatmap.png`
- `results/<run-id>/report/equity_curves.png`

---
## Experiment inspection workflow

#### Read the config

Start with:

- `configs/experiments/exp-000-smoke.yaml`
- `configs/experiments/exp-001-replay-equities.yaml`
- `configs/experiments/exp-002-replay-prediction.yaml`
- `configs/experiments/exp-010-shared-exchange.yaml`

Questions:

- What dataset is used?
- Which market mode is used?
- How many steps?
- What seed?
- What cohorts?
- What agents per cohort?
- What models/personas?
- What initial cash?
- What position limits?
- What fees/slippage?

---

#### Inspect the dataset

Questions:

- What symbols/contracts are included?
- What timestamps exist?
- What do prices look like?
- What do returns look like?
- Are there events?
- Are regimes obvious?
- Is there missing data?

Suggested visualizations:

- Price line chart by symbol.
- Return heatmap.
- Rolling volatility.
- Event overlay on prices.
- Asset correlation matrix.

---

#### Reconstruct one decision

Pick one:

- run ID.
- agent ID.
- step.

Reconstruct:

- market state.
- trailing bars.
- news/events.
- portfolio before decision.
- prompt / prompt hash.
- raw or parsed decision.
- clipped order.
- fill.
- portfolio after fill.

Goal:

> Be able to explain exactly why one row exists in `decisions.jsonl`.

If one row is understandable, the whole pipeline becomes understandable.

---

#### Check action distributions

Before looking at convergence metrics, ask:

- How often does each cohort buy?
- How often does each cohort sell?
- How often does each cohort hold?
- Are LLM agents mostly holding?
- Are baselines more active?
- Are parse failures causing artificial holds?
- Are position/cash constraints causing artificial holds?

This is important because raw agreement can be misleading if everyone mostly holds.

---

#### Interpret convergence metrics

Look at:

- raw agreement.
- Cohen's kappa.
- trade-direction correlation.
- position cosine similarity.
- portfolio overlap.
- return correlation.
- strategy fingerprint dispersion.
- rationale similarity.

Ask:

- Do all metrics tell the same story?
- If not, why?
- Are agents agreeing on action but not portfolio?
- Are agents agreeing on portfolio but not rationale?
- Are rationales similar but trades different?
- Is the effect driven by one or two agents?

---

#### Interpret statistics

For primary claims, ask:

- What is the effect size?
- What is the cluster-aware effect interval and frozen primary test result?
- What is the null-cohort value?
- Is the result robust across independent trajectories or nonoverlapping windows?
- Is the result robust across market regimes?
- Is the result robust to prompt paraphrases?
- Is the result robust to stronger baselines?

---
## Visualization contract

#### Dataset visualizations

1. Price chart by symbol.
2. Return chart by symbol.
3. Rolling volatility by symbol.
4. Event/news overlay on prices.
5. Return correlation matrix.
6. Regime-colored price chart for synthetic data.
7. Missing-data heatmap.

---

#### Decision visualizations

1. Agent action raster

Most important simple plot.

- x-axis: time/step.
- y-axis: agent.
- color: buy/sell/hold.

Purpose:

- Visually reveals agreement, herding, and hold-heavy behavior.

2. Cohort net flow over time

- x-axis: time/step.
- y-axis: net signed quantity.
- separate line per cohort.

Purpose:

- Shows whether cohorts buy/sell together.

3. Buy/sell/hold stacked area by cohort

Purpose:

- Shows activity mix and whether agreement is driven by holds.

4. Pairwise kappa heatmap

Purpose:

- Shows agent clusters.
- Useful for same-provider vs cross-provider questions.

5. Rolling agreement over time

Purpose:

- Shows whether convergence increases, decreases, or spikes during regimes.

---

#### Portfolio visualizations

1. Equity curves by agent/cohort.
2. Equity fan chart by cohort.
3. Drawdown curves by cohort.
4. Position weight heatmap.
5. Portfolio overlap heatmap.
6. Turnover by cohort.
7. Cash/constraint usage over time.

---

#### Strategy visualizations

1. Fingerprint coefficient bar charts.
2. PCA or UMAP of strategy fingerprints.
3. Agent clustering dendrogram.
4. Rationale similarity heatmap.
5. Rationale cluster examples.
6. Signal exposure over time.

---

#### Statistical visualizations

1. Bootstrap confidence interval forest plot.
2. Permutation null distribution with observed statistic marked.
3. Effect size by independent trajectory or nonoverlapping window.
4. Effect size by market regime.
5. Holm-adjusted p-value table.
6. Power curve showing required top-level units per cell.

---

#### Shared-exchange visualizations

1. Order book depth over time.
2. Midprice with cohort net flow overlay.
3. Cascade event timeline.
4. Liquidity before/after cohort-wide selling.
5. Spread over time.
6. LSV herding over time.
7. Price impact versus LLM market share.

---
## Threats to validity

#### Hold-heavy behavior

Problem:

- If all agents mostly hold, raw agreement will be high even without meaningful convergence.

Mitigation:

- Use Cohen's kappa.
- Report action distributions.
- Analyze active-trader-only agreement.
- Track parse failures.
- Track constraint-driven holds.

---

#### Prompt-induced convergence

Problem:

- A shared prompt template may cause similar behavior.

Mitigation:

- Prompt paraphrase battery.
- Multiple prompt styles.
- Minimal prompts.
- Persona variation.
- Information-set variation.

---

#### Weak baselines

Problem:

- If classical baselines are too simple, LLMs may look artificially unusual.

Mitigation:

- Add stronger and more diverse baselines.
- Randomize baseline hyperparameters.
- Include ensemble strategies.
- Include volatility targeting and risk controls.

---

#### Historical data contamination

Problem:

- Models may have memorized famous historical price patterns or market events.

Mitigation:

- Use synthetic data.
- Use post-cutoff data.
- Use obscure assets.
- Anonymize symbols.
- Transform returns.

---

#### Leakage

Problem:

- Future information may accidentally enter observations.

Mitigation:

- Audit observation construction.
- Verify trailing windows.
- Hide resolution outcomes.
- Hide regime labels.
- Avoid future-computed summaries.

---

#### Multi-symbol action simplification

Problem:

- A single buy/sell/hold action can hide multi-symbol behavior.

Example:

- An agent buys AAPL and sells MSFT, but the net action may simplify this too much.

Mitigation:

- Compute symbol-level action metrics.
- Compute signed quantity correlations.
- Compute portfolio-level metrics.

---

#### Constraints create convergence

Problem:

- Agents may all hold because they run out of cash or hit position limits.

Mitigation:

- Track cash.
- Track position-limit hits.
- Track clipped orders.
- Report turnover.

---

#### Rationale unreliability

Problem:

- LLM explanations may not faithfully explain actions.

Mitigation:

- Treat rationale analysis as secondary.
- Compare rationales with actual signal loadings.
- Audit hallucinations.

---

#### External-anchor mismatch

Problem:

- 13F quarterly holdings and simulated daily trades are not directly equivalent.

Mitigation:

- Be explicit that real-world panels are anchors, not perfect controls.
- Match metrics carefully.
- Avoid overclaiming.

---

#### Provider nondeterminism

Problem:

- Even temperature-zero LLM calls can vary across providers/time.

Mitigation:

- Cache responses.
- Record model IDs and parameters.
- Record prompt hashes.
- Record response hashes if possible.
- Keep offline replay possible.

---
## Interpretation discipline

Avoid saying:

- "LLMs collude."
- "LLMs manipulate markets."
- "LLMs coordinate illegally."
- "LLMs are better traders."

Prefer saying:

- "LLM cohorts show higher non-communicative decision convergence under identical information."
- "LLM agents exhibit higher within-cohort agreement than baseline agents after chance correction."
- "Shared-market simulations suggest that independent convergence can amplify into herding/cascades under price feedback."
- "Rationale similarity does or does not align with trade similarity."
- "The result is robust / not robust to prompt paraphrases, stronger baselines, and contamination-resistant data."

---
