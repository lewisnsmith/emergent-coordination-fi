# 02 — Experimental Design

## Topology and paper boundary

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
- **Separate H5 experiment — shared exchange.** Cohorts trade in a continuous double auction
  whose rules and calibration must pass validation before use. Randomized AI capital share can
  identify market effects inside that simulator. It cannot establish effects in real markets and
  is not part of the first-paper H1/H3/H4 family.

H2 is included only as a descriptive external anchor if its harmonization gate passes. H2b and
H6–H12 remain the future program.

## Experimental axes

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

## Matched technology × ecology benchmark

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

## Controls and identification

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

## Independent units and dependence

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

## Decision protocol (what agents actually do)

Each step an agent receives an observation: recent OHLCV window (or contract prices), optional
news/events, its own portfolio, and cash. It must return structured JSON with orders, a concise
rationale, evidence references, calibrated confidence, and uncertainties. Strict runs reject
unsupported evidence references and record grounding failures separately from parse failures.
Malformed responses are retried once, then recorded as `hold` with a parse-failure flag
(exclusion rules in 06-preregistration).

## First-paper experiments and future program

The authoritative catalog is [`configs/research-program.yaml`](../../configs/research-program.yaml):

- **First paper:** `exp-000`–`002` and `exp-005`–`009` support H1/H3/H4 calibration,
  confirmation, component decomposition, and robustness. Inclusion requires the matched 2×2
  technology-by-ecology contract even where older config descriptions remain narrower.
- **Conditional H2 anchor:** `exp-003` is included only after cadence, universe, activity,
  sampling, direction, and capital-weighting harmonization succeeds.
- **Separate simulator-only H5:** `exp-010`–`012` cover exchange calibration, randomized
  AI-capital-share response, and microstructure.
- **Future program:** `exp-004` and `exp-013`–`024` cover H2b and H6–H12.

`executable`, `scaffolded`, and `blocked_external` are intentionally distinct. A protocol is not
called execution-ready merely because its YAML exists. `flock validate` reports both scaffold
validity and missing data/approval/exposure blockers.

## Factorial assignment

MPHIQ uses bits `M P H I Q`, where `1 = same` and `0 = balanced different`. All 32 codes are
enumerated in [`configs/designs/mphiq.yaml`](../../configs/designs/mphiq.yaml). Prompt pressure is
a future H12 24-cell `3 stakes × 2 urgency × 2 emotion × 2 forced-action` design. Prompt
paraphrases are nested robustness observations, not independent market evidence. See
[09](09-mphiq-factorial-design.md) and [11](11-prompt-pressure-protocol.md).

## Model and experiment reporting gates

Before confirmatory release, the simulator must have a completed
[ODD model description](https://doi.org/10.18564/jasss.4259) and a
[STRESS experiment report](https://doi.org/10.1080/17477778.2018.1442155). ODD must identify
purpose, entities, state variables, process scheduling, design concepts, initialization, inputs,
and submodels. STRESS must reconcile objectives, scenarios, experimental design, implementation,
execution, and analysis with the frozen manifests. Missing items block H5 claims and any claim
that a replay/simulation result is ready for publication.

## Threats to validity (and responses)

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
