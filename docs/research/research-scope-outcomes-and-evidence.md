# Research scope, outcomes, and evidence

**Status: ACTIVE research contract. Last consolidated: 2026-08-12.** The machine-readable
catalog remains [`configs/research-program.yaml`](../../configs/research-program.yaml). The
configured first paper remains H1/H3/H4 until its study contracts are reconciled. The
local-first H13/H8 lane changes affordable execution order, not publication status.

## Project outputs

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

## Primary question

**Which shared components make LLM trading agents converge, and how does that convergence compare
with classical strategies under matched homogeneous and heterogeneous cohort ecologies?**

The first paper studies **common-response convergence** and **outcome homogenization**. Phase-1
agents do not interact, observe each other, or move prices, so agreement there is not emergent
coordination or collusion. The motivating risk is that many participants may independently respond
similarly because they share model lineage, training priors, prompts, harnesses, or information.
Whether that common response causes market harm is a separate simulator-bounded question under H5.

## Why the question matters

- **Systemic risk.** Crowded trades and correlated liquidation are classic amplifiers of market
  stress (quant quake 2007, March 2020 dash-for-cash). If LLM agents share a common prior — the
  same pre-training distribution, the same RLHF objectives — correlation may arise *without any
  communication*, which existing surveillance (focused on communication and common ownership)
  would not detect.
- **Market efficiency.** Convergent agents may arbitrage away the same signals faster, or may
  collectively neglect signals outside the models' shared blind spots.
- **Model-risk policy.** Shared decision components may create correlated errors without
  communication. That possibility is relevant to concentration, stress testing, and model-risk
  governance, but convergence alone is not evidence of tacit collusion.
- **Scientific access and deployment realism.** Frontier APIs provide a useful behavioral ceiling
  but not stable weights or internal activations. Smaller open-weight checkpoints make paired
  precision experiments and causal activation interventions possible. The open question is
  whether they preserve the frontier behaviors we care about, and whether small quantization
  errors remain local or compound through long financial calculations into different trades.

## Program and publication boundaries

H1, H3, and H4 form the configured first-paper confirmatory family. H2 is descriptive and
conditional on harmonization. H5 is a separate simulator-bounded experiment. H2b and H6–H13
are future protocols. H13 and H8 are the first affordable owned execution lane under the
current personal budget, but that staging does not replace or silently redesign the configured
first paper.

H1 uses cluster-aware inference at the top-level unit. Sign flips are sensitivity analysis
only because technology is not randomized. Independent evidence comes from independently
generated trajectories, nonoverlapping historical windows, or whole-market replicas—not model
seeds, agents, calls, steps, symbols, or prompt variants. The direction and exact decision rule
for both H1 contrasts remain explicitly unfrozen until the draft preregistration resolves them.

## Hypothesis registry

### H1

- **Question:** Do frontier LLM investment agents converge more than heterogeneous classical investment algorithms under matched conditions?
- **Proposed claim:** Frontier LLM cohorts have greater chance-corrected per-symbol decision and portfolio convergence than matched classical cohorts.
- **Claim boundary:** Applies to sampled models, markets, windows, prompts, and constraints; it does not establish universal model behavior or superior investment performance.
- **Program role:** first-paper confirmatory family.
- **Cost status:** frontier replay factorials.

### H2

- **Question:** Is AI-agent convergence unusual relative to convergence among real investors measured on comparable outcomes?
- **Proposed claim:** AI-cohort convergence differs from harmonized real-investor panel convergence after matching universe, cadence, activity, and sampling.
- **Claim boundary:** Descriptive matched comparison only; unmatched 13F or trader panels cannot establish that AI is more convergent than all real investors.
- **Program role:** descriptive conditional anchor.
- **Cost status:** not designated high cost; still subject to its data and validity gates.

### H2b

- **Question:** If pairwise AI convergence is ordinary, does AI adoption spread existing convergence across more investors and capital?
- **Proposed claim:** Increasing shared-AI delegation can increase the breadth and capital-weighted prevalence of correlated behavior even when pairwise convergence is held at real-investor levels.
- **Claim boundary:** A simulated delegation response does not establish present adoption, actual capital exposure, or a real-market causal effect.
- **Program role:** future protocol.
- **Cost status:** not designated high cost; still subject to its data and validity gates.

### H3

- **Question:** Do agents using the same frontier model or provider converge more than agents using different frontier model families?
- **Proposed claim:** Same-model and same-provider pairs have different convergence from provider-balanced cross-family pairs.
- **Claim boundary:** Inference is limited to exact verified models and provider lineages sampled in the study.
- **Program role:** first-paper confirmatory family.
- **Cost status:** frontier replay factorials.

### H4

- **Question:** Does genuine information differentiation reduce convergence more than diverse investor profiles or persona wording?
- **Proposed claim:** Information-set heterogeneity has a larger convergence effect than profile heterogeneity under a balanced factorial design.
- **Claim boundary:** Profile wording, identity cues, and financially relevant client constraints must be analyzed separately.
- **Program role:** first-paper confirmatory family.
- **Cost status:** frontier replay factorials.

### H5

- **Question:** Does increasing AI-managed capital change market dynamics, and when do material effects begin?
- **Proposed claim:** AI capital share causally changes preregistered simulated-market impact, volatility, liquidity, herding, or cascade outcomes relative to paired zero-AI markets.
- **Claim boundary:** Causality is internal to the configurable exchange; real-market effects require external identification under H10.
- **Program role:** separate simulator experiment.
- **Cost status:** shared exchange and signatures.

### H6

- **Question:** Do people trust AI to advise on or autonomously manage investments, and what changes delegation?
- **Proposed claim:** Randomized oversight, performance, explanation, and risk conditions change incentive-compatible human delegation choices.
- **Claim boundary:** Requires approved, consented, appropriately sampled human data; model behavior cannot answer human trust.
- **Program role:** future protocol.
- **Cost status:** human study.

### H7

- **Question:** Will AI investment delegation plausibly cross a market-impacting adoption threshold soon?
- **Proposed claim:** Verified adoption evidence and H5 thresholds support a calibrated forecast distribution for threshold crossing.
- **Claim boundary:** Forecasts are conditional scenarios with backtested uncertainty, never facts about future adoption.
- **Program role:** future protocol.
- **Cost status:** not designated high cost; still subject to its data and validity gates.

### H8

- **Question:** What supplied information causally drives investment decisions, and which internal mechanisms weight it most heavily?
- **Proposed claim:** Controlled input and activation interventions identify causal influences on decisions in sampled API and local frontier models.
- **Claim boundary:** Closed APIs support black-box input attribution only; generated rationales are not mechanistic evidence.
- **Program role:** future protocol.
- **Cost status:** mechanistic interventions.

### H9

- **Question:** Do causal convergence signatures learned in simulation transport to held-out simulated and real market data?
- **Proposed claim:** Locked signatures retain preregistered discrimination and calibration on independent domains.
- **Claim boundary:** Pattern transport indicates similarity, not AI presence or causation.
- **Program role:** future protocol.
- **Cost status:** shared exchange and signatures, real market attribution and release.

### H10

- **Question:** Can detected real-market signatures be attributed to AI rather than merely resembling simulated AI behavior?
- **Proposed claim:** Under verified exposure and a credible assignment or quasi-experimental design, AI exposure causally changes preregistered signatures or outcomes.
- **Claim boundary:** Detection scores alone never justify causal language; pretrends, placebos, spillovers, and confounding sensitivity are mandatory.
- **Program role:** future protocol.
- **Cost status:** real market attribution and release.

### H11

- **Question:** Can verified findings become useful reproducible datasets without overstating causal status?
- **Proposed claim:** Separately labeled simulation truth, detected patterns, exposure records, and causally verified events meet release and held-out utility gates.
- **Claim boundary:** Dataset tiers cannot be merged into a single ground-truth AI-causation label.
- **Program role:** future protocol.
- **Cost status:** real market attribution and release.

### H12

- **Question:** Do high-stakes, urgent, emotional, or forced-action instructions make investment decisions better, worse, equivalent, or merely different, and why?
- **Proposed claim:** Stakes, urgency, emotion, and forced action have separable effects on quality, suitability, safety, risk, abstention, and convergence.
- **Claim boundary:** Treatments are fictional language frames; equivalence requires TOST, safety requires noninferiority, and models are not claimed to experience emotion or stakes.
- **Program role:** future protocol.
- **Cost status:** prompt pressure.

### H13

- **Question:** When do lower-weight local models preserve frontier-model convergence and behavior, and how do quantization errors propagate through long financial reasoning chains?
- **Proposed claim:** Model scale, checkpoint family, precision, reasoning depth, and state feedback have measurable effects on behavioral equivalence, conditional step-error hazard, and downstream trading-path divergence.
- **Claim boundary:** A financial scoring key defines correctness, same-checkpoint full precision identifies quantization loss, and frontier outputs supply a descriptive behavioral bridge; none is interchangeable and transfer beyond sampled families requires held-out replication.
- **Program role:** future protocol and current local-first execution priority.
- **Cost status:** local fidelity and quantization.

## Hypothesis retention and cost rule

The canonical program retains H1–H13 and H2b regardless of their execution cost. Cost may change
funding, sequencing, evidence reuse, or execution timing, but it may not delete a hypothesis,
silently merge it away, or relabel it out of scope. A high-cost label means staged or deferred,
not rejected.

External results may reduce redundant collection when provenance, comparability, and the frozen
estimand permit synthesis, but citation alone does not mark a hypothesis complete. Removing or
substantively merging a hypothesis requires a scientific rationale unrelated to cost and a visible
preregistration amendment.

## High-cost registry

| Component | Hypotheses | Experiments | Why it costs so much |
|---|---|---|---|
| frontier replay factorials | H1, H3, H4 | exp-001, exp-002, exp-005, exp-006, exp-007, exp-008, exp-009 | millions of sequential frontier-model decisions |
| shared exchange and signatures | H5, H9 | exp-011, exp-012, exp-018 | frontier calls across independent market replicas plus simulator validation |
| human study | H6 | exp-013 | ethics review recruitment compensation and study operations |
| mechanistic interventions | H8 | exp-017 | multi-gpu activation capture and causal interventions |
| real market attribution and release | H9, H10, H11 | exp-019, exp-020, exp-021, exp-022 | licensed data exposure verification causal design and release engineering |
| prompt pressure | H12 | exp-023, exp-024 | large factorial and held-out frontier-model validation |
| local fidelity and quantization | H13 | exp-025, exp-026 | paired precision ladders across open-weight families plus targeted frontier bridges and activation interventions |

## Evidence substitution

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

External evidence may replace redundant validation only when it is at least as strong as the
project question on construct, population, intervention, outcome, identification, and
provenance. Otherwise it is background evidence, not a completed hypothesis.

## Operational definitions

- An **agent** is a decision function `observe → decide` producing orders each step; LLM agents
  are parameterized by (provider, model, temperature, reasoning effort, persona prompt, memory).
- A **strategy** is operationalized two ways: (a) the realized decision stream itself, and
  (b) a *strategy fingerprint* — loadings from regressing the agent's trades on canonical factor
  signals (momentum, reversal, value proxy, volatility).
- **Common-response convergence** is low within-cohort dispersion across the metric hierarchy:
  decision-level (per-step action agreement), portfolio-level (position similarity over time),
  and strategy-level (fingerprint distance, rationale-embedding distance).
- The **top-level independent unit** is an independently generated synthetic market trajectory or
  a nonoverlapping historical market window. Windows that overlap or share a material common shock
  remain in one dependence cluster. Seeds, agents, pairs, calls, steps, symbols, and prompt variants
  are nested and cannot increase the paper-level sample size.
- The **internal control** is the matched classical technology-by-ecology benchmark. Real-investor
  panels are conditional external anchors, not interchangeable controls.
- H13 uses three noninterchangeable references: a deterministic financial scoring key for correctness,
  the same checkpoint at BF16 or FP16 for the causal effect of quantization, and cached frontier
  outputs for descriptive behavioral similarity. Agreement with a frontier endpoint is not
  correctness, and a small open checkpoint is not a mechanistic proxy until transfer is tested.

## Scope and non-claims

The first paper covers synthetic trajectories and nonoverlapping historical replay windows in US
equities, with binary prediction-market replay as a held-out market-type replication if its data
gate passes. It tests H1/H3/H4 only. H5 uses a separate shared simulated exchange, and H2 is
included only under its harmonization gate. H6–H13 remain future papers. Real-money trading,
automated live deployment, claims of individual financial advice, and real-market causal claims
from simulated resemblance remain out of scope.

The public H11 product may be useful and actionable without being a profitable signal. That
boundary applies to the public dataset product; it does not prohibit a separately labeled,
strictly out-of-sample owned-alpha evaluation.

## Secondary and exploratory questions

The expanded H1–H13 program is no longer a loose backlog. Its canonical experiment mapping is
[`configs/research-program.yaml`](../../configs/research-program.yaml). The items below are
secondary moderators or extensions; they must not silently enter the confirmatory family.

Secondary questions, ordered by proximity to the primary result. Experiment IDs below are
planned; only exp-000, exp-001, exp-002, and exp-010 currently have configs.

1. **Within-family vs cross-family convergence.** Does Claude agree with Claude more than with
   GPT/Gemini? Is there a "foundation-model fingerprint" detectable from trades alone?
   → provider-blocked MPHIQ/model-pair study (`exp-005` in the canonical catalog).
2. **Capability scaling and local fidelity.** Does convergence rise with model tier, and are
   lower-weight open models behaviorally equivalent to sampled frontier endpoints within frozen
   margins? Keep this descriptive cross-model bridge (`exp-025`, H13) separate from reasoning-
   effort robustness among dated frontier models (`exp-009`).
3. **Temperature & sampling.** How much decorrelation does temperature buy, and at what
   performance and safety cost? (`exp-009`)
4. **Persona/demographic sensitivity.** Which instruction dimensions (risk tolerance, horizon,
   demographic framing, mandate) actually change *strategy* rather than *style*? How much
   dispersion can prompt engineering restore? (`exp-006`/`exp-008`)
5. **Information-set differentiation.** Does giving agents different news subsets decorrelate
   them more than personas do (H4)? What is the marginal substitution rate between information
   heterogeneity and prompt heterogeneity? (`exp-007`/`exp-008`)
6. **Memory & context.** Do agents with trade memory converge more over time (self-reinforcing
   strategies) or less (path dependence)? (exp-008)
7. **Regime dependence.** Is convergence stronger in crises (flight to the same safety) than in
   calm regimes? Compare synthetic regime blocks and historical windows. (exp-009)
8. **Shared-market amplification (H5).** Cascade frequency/depth vs cohort LLM-share: sweep the
   fraction of market capital held by LLM agents from 0% to 100%; find the threshold where
   price dynamics change. (exp-011)
9. **Tacit coordination / collusion.** In the shared market with market-maker LLM agents, do
   spreads widen supra-competitively without communication (Calvano-style)? (exp-012)
10. **Contamination.** Do agents behave differently on pre-cutoff vs post-cutoff vs synthetic
    data in ways consistent with memorization? (robustness battery attached to exp-001)
11. **Advisor mode.** If LLMs advise heterogeneous executors (humans with noise/latency) rather
    than trade directly, how much convergence survives the execution layer?
12. **Cross-market consistency.** Are the *same* models the convergence drivers in equities and
    prediction markets, or is convergence market-structure dependent?
13. **Detection.** Can a locked simulation-derived signature transport to held-out public tape?
    This is H9/`exp-018`–`019`; it cannot establish AI causation without H10/`exp-020` evidence.
14. **Decorrelation interventions.** Can information diversification, model-provider diversity,
    randomized execution, or human review reduce breadth without unacceptable performance or
    safety loss?
15. **Mechanism convergence.** Do agents reach similar trades through the same causally active
    features/circuits, or do distinct mechanisms converge behaviorally? H13/`exp-026` requires
    representation alignment, transferred intervention, and behavioral recovery before a
    cross-family mechanism claim.
16. **Adversarial robustness.** Which injection, authority, FOMO, forced-certainty, anchoring,
    and conflicting-mandate prompts defeat grounding or constraint compliance?
17. **Quantization propagation.** For the same checkpoint, where does BF16/W8/W4 divergence first
    appear as financial dependency depth increases, and how much additional portfolio divergence
    arises under endogenous versus shadow-state replay? (`exp-026`, H13)
18. **Customization fidelity.** Does quantization attenuate causal response to risk capacity,
    horizon, liquidity, dependents, taxes, mandate constraints, or information access? Compare
    profile-response vectors before any LoRA or fine-tuning treatment. (`exp-025`/`exp-026`)

## Research directions and backlog

### Core convergence result

Question:

- Do LLM cohorts show higher within-cohort decision agreement than baseline algorithm cohorts?

Why it matters:

- This is the central paper claim.

Required controls:

- Null/random cohort.
- Chance-corrected metrics.
- Multiple independent trajectories or nonoverlapping windows.
- Strong baseline strategies.
- Prompt paraphrases.
- Synthetic and real data.

---

### Same-provider versus cross-provider convergence

Question:

- Do agents from the same model family agree more than agents from different model families?

Possible result:

- Claude agents cluster together.
- GPT agents cluster together.
- Gemini agents cluster together.

Why it matters:

- Could imply foundation-model-specific trading fingerprints.

---

### Model capability scaling

Question:

- Does convergence increase with model capability, model size, or reasoning effort?
- Under frozen equivalence margins, which lower-weight open models preserve sampled frontier
  behavior and convergence on held-out financial tasks?
- Within one checkpoint, does BF16/W8/W4 precision change first-error hazard as executable
  financial dependency depth grows, and does portfolio feedback amplify the difference?

Two competing interpretations:

1. Smarter agents find the same optimal strategy.
2. More capable/aligned agents share more priors and therefore converge.

H13 separates this descriptive local-to-frontier bridge from the causal same-checkpoint
quantization contrast. A financial scoring key defines correctness; frontier agreement is not truth,
and a structured calculation ledger is not a faithful hidden chain-of-thought.

---

### Temperature and sampling diversity

Question:

- Does higher temperature reduce convergence?

Follow-up:

- Does it reduce performance?
- Does it diversify actions or only rationales?

---

### Persona sensitivity

Question:

- Do personas change strategy or only style?

Examples:

- retail daytrader.
- retail saver.
- institutional value.
- institutional quant.
- risk-averse mandate.

Important distinction:

- Language diversity is not strategy diversity.

---

### Information-set differentiation

Question:

- Does giving agents different information reduce convergence more than giving them different personas?

Why it matters:

- If yes, market diversity may require information diversity, not just model/persona diversity.

---

### Memory and path dependence

Question:

- Does agent memory make agents converge or diverge over time?

Possible outcomes:

1. Memory increases convergence because agents learn the same lessons.
2. Memory decreases convergence because different portfolio histories create path dependence.

---

### Regime dependence

Question:

- Is convergence stronger in crises than calm markets?

Possible interpretation:

- In stress, many agents may flee to the same perceived safe behavior.

Regimes to compare:

- trending.
- mean-reverting.
- crisis.
- low volatility.
- high volatility.
- post-cutoff real windows.

---

### Contamination robustness

Question:

- Do LLMs behave differently on historical data they may have memorized versus synthetic or post-cutoff data?

Robustness tools:

- synthetic markets.
- anonymized symbols.
- post-training-cutoff windows.
- obscure assets/contracts.
- transformed return series.

---

### Shared-market amplification

Question:

- Does independent convergence become systemic herding when agents share a market?

Experiment:

- Vary LLM share of market capital from 0% to 100%.

Metrics:

- cascade frequency.
- cascade depth.
- LSV herding.
- liquidity withdrawal.
- spread widening.
- price impact.

---

### Tacit collusion and market-maker behavior

Question:

- Can LLM market makers widen spreads or reduce competition without explicit communication?

Why it matters:

- Connects to algorithmic tacit collusion literature.

Important caution:

- Use careful language. Do not claim illegal collusion unless there is explicit evidence and a legal framework.

---

### Detection and surveillance

Question:

- Can a market observer detect LLM-agent participation from public market data?

Possible detector inputs:

- order timing.
- trade direction.
- herding statistics.
- flow persistence.
- spread/depth changes.
- action regularity.

Why it matters:

- Could inform market surveillance and regulation.

---

### Decorrelation interventions

Question:

- What interventions reduce harmful convergence while preserving useful performance?

Possible interventions:

- model diversity.
- prompt diversity.
- information diversity.
- temperature.
- execution noise.
- randomized risk limits.
- heterogeneous objectives.
- ensemble methods.
- delayed or partitioned information.

---

### Rationale faithfulness

Question:

- Do LLM rationales faithfully explain trades?

Tests:

- Compare rationale similarity to trade similarity.
- Compare stated signal use to regression-implied signal use.
- Look for hallucinated reasons.
- Use counterfactual observations.

---

### Market ecology experiments

Question:

- What happens as markets contain different mixtures of participant types?

Sweep participant shares:

- LLM agents.
- classical algos.
- random/noise traders.
- market makers.
- trend followers.
- mean-reversion agents.
- human-like heuristic agents.

Goal:

- Identify thresholds where LLM share changes market dynamics.

---

## Stronger baseline candidates

Current baselines include:

- momentum.
- mean reversion.
- market maker.
- buy and hold.
- random.

Potential stronger baselines:

- volatility targeting.
- moving-average crossover.
- trend/reversal ensemble.
- risk parity.
- simple supervised ML trained only on past data.
- cross-sectional momentum.
- pairs/stat-arb toy model.
- noise trader with realistic constraints.
- heterogeneous retail heuristic agents.
- stop-loss / take-profit agents.
- value proxy strategy.
- liquidity-aware execution agent.

Key question:

> Does the LLM result survive comparison against a genuinely diverse baseline ecology?

---

## Recommended framing

The strongest version of the project is:

> As financial decision-making becomes increasingly mediated by a small number of foundation models, market diversity may decline even without explicit communication. `flock` measures this by comparing LLM-agent cohorts against classical algorithmic baselines and real-world reference panels across decision-level, portfolio-level, and strategy-level convergence metrics. It then tests whether this non-communicative convergence can amplify into herding, cascades, or liquidity effects when agents share a market.

This framing is stronger than:

- "Can LLMs trade profitably?"
- "Can LLMs beat the market?"
- "Do LLMs collude?"

The project is really about:

- non-communicative convergence.
- shared model priors.
- loss of market participant diversity.
- systemic herding risk.
- foundation-model fingerprints in financial behavior.
- interventions that restore diversity.
- whether lower-weight open models preserve those findings well enough to support causal
  interpretability and targeted customization.
- where quantization errors enter verifiable financial chains and whether state feedback turns
  them into different portfolios or market paths.

---

## Priority unresolved questions

If you only focus on a short list, focus on these:

1. Can I reconstruct exactly what one agent saw and did at one step?
2. Are LLM agents more convergent than baselines after chance correction?
3. Is the result driven by holds, parse failures, or constraints?
4. Does the result survive across independent trajectories or nonoverlapping windows?
5. Does the result survive across regimes?
6. Does the result survive prompt paraphrases?
7. Does the result survive stronger baselines?
8. Does information diversity reduce convergence more than persona diversity?
9. Are trades, portfolios, fingerprints, and rationales telling the same story?
10. Does convergence become herding or cascades in the shared exchange?
11. Can model/provider identity be detected from behavior alone?
12. What intervention best reduces harmful convergence without destroying performance?

---

## Prior work and novelty boundaries

Working claim map for the design. The dated, reproducible search protocol and screening decisions
are in [`literature-search-and-screening-log.yaml`](literature-search-and-screening-log.yaml); `paper/references.bib` is the
bibliographic source of record. Refresh both before preregistration and submission.

### Novelty boundary

The generic novelty territory is occupied. Prior work already reports concentrated cross-model
investment recommendations, reduced LLM-trader dispersion relative to humans, common errors in
mixed model markets, prompt-sensitive market effects, and LLM trading in price-forming order-book
simulations. This project must not claim to be the first demonstration that LLM financial agents
converge, herd, or affect simulated markets.

The defensible proposed contribution is narrower: a matched
`technology (LLM/classical) × ecology (homogeneous/heterogeneous)` benchmark, family-weighted
estimands, a design intended to decompose model/profile/harness/information/wording components,
and inference over independent trajectories or nonoverlapping windows. H5 is a separate,
simulator-bounded consequence experiment; H2 is a conditional descriptive anchor.

For H13, prior work already occupies generic claims that quantization changes reasoning, that
some 4-bit configurations preserve aggregate accuracy, and that early low-bit errors can cascade.
The proposed extension is finance-specific and process-level: separate scale from precision,
measure gold-prefix error incidence versus free-running and state-mediated propagation, connect
verifiable financial steps to later trades, and causally test activation differences. It must not
claim the first quantization study or assume that one local mechanism generalizes to frontier APIs.

### Herding measurement (our H2/H5 statistics come from here)

- **Lakonishok, Shleifer & Vishny (1992)**, "The impact of institutional trading on stock
  prices," *JFE*. The LSV herding statistic: excess one-sidedness of trades vs binomial null.
  We apply it symmetrically to LLM cohorts and 13F panels.
- **Sias (2004)**, "Institutional herding," *RFS*. Serial cross-sectional correlation of
  institutional demand; decomposition into own-following and crowd-following.
- **Wermers (1999)**, mutual-fund herding; grounds activity filters and interpretation.
- **Wylie (2005)** and **Frey, Herbst & Walter (2014)** show that traditional LSV estimates can
  be biased by the data structure and activity process. H2 therefore requires period-specific
  expected-buy fractions, quarter-to-quarter holdings changes, activity reporting, and structural
  sensitivity analysis rather than treating 13F overlap as a universal human benchmark.

### Algorithmic coordination and collusion

- **Calvano, Calzolari, Denicolò & Pastorello (2020)**, “Artificial intelligence, algorithmic
  pricing, and collusion,” *AER*. Q-learning pricers converge to supra-competitive prices
  without communication. This is a strategic pricing result, not authority to call correlated
  Phase-1 decisions collusion.
- **Klein (2021)** studies sequential Q-learning pricing. DOI
  `10.1111/1756-2171.12383` is the article identifier, not a correction notice.
- **Colliard, Foucault & Lovo (2026)** show that Q-learning market makers can fail to learn
  competitive pricing because experimentation is limited and profit feedback is noisy. This is a
  direct benchmark for H5 competitive/null/deviation tests.

### Crowding & systemic risk

- **Khandani & Lo (2011)**, "What happened to the quants in August 2007?" Evidence that crowded
  quant strategies unwound together — the historical template for convergence risk.
- **Stein (2009)**, "Presidential address: Sophisticated investors and market efficiency" —
  crowding and leverage externalities among sophisticated traders.
- **Brunnermeier & Pedersen (2009)**, funding/market liquidity spirals — mechanism for
  Phase-2 cascade interpretation.

### Direct LLM-finance precedents

- **Henning et al. (2025),
  [“LLM Agents Do Not Replicate Human Market Traders”](https://arxiv.org/abs/2502.15800).** Six
  API-accessed LLMs trade in homogeneous and mixed experimental markets alongside a human-market
  comparison. The paper directly reports lower strategy and portfolio-value dispersion among LLM
  traders, occupying any broad “LLMs are more homogeneous than humans” claim.
- **Joglar (2026),
  [“Converging Echoes”](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6852518).** Five LLMs
  generate investment recommendations in a crossed client-profile design. Inter-model portfolio
  overlap exceeds a size-matched random benchmark and capital concentrates in a small issuer set.
  The distinction here must be sequential replay and matched classical ecologies, not discovery of
  recommendation convergence.
- **Saxena et al. (2026),
  [“Machine Spirits”](https://arxiv.org/abs/2604.18602).** Fifteen LLMs/providers trade in
  homogeneous and heterogeneous experimental markets. Common errors and mixed model ecologies can
  produce instability, directly motivating rather than replacing the proposed ecology factor.
- **Ouyang and Sui (2026),
  [“Dissecting AI Trading”](https://arxiv.org/abs/2604.18373).** Autonomous LLM traders operate in
  an auction, and targeted prompt interventions alter behavioral mechanisms and bubble magnitude.
  This occupies generic prompt-to-market-effect novelty; MPHIQ's balanced component decomposition
  remains the differentiator.
- **Lopez-Lira (2025),
  [“Can Large Language Models Trade?”](https://arxiv.org/abs/2504.10789).** LLM agents trade with
  a persistent order book, market and limit orders, partial fills, heterogeneous strategies and
  information, and endogenous liquidity and price behavior. Exchange infrastructure and simulated
  price effects are therefore enabling methods, not firsts.
- **Ma et al. (2025),
  [“Agent Trading Arena”](https://aclanthology.org/2025.findings-emnlp.294/).** A competitive
  zero-sum stock arena studies numerical and visual reasoning under endogenous agent interaction.
  It further occupies generic multi-agent trading-arena novelty.
- **“Agentic Trading: When LLM Agents Meet Financial Markets” (2026),
  [systematic review](https://arxiv.org/abs/2605.19337).** The review maps 77 studies and identifies
  recurring weaknesses in temporal splits, transaction costs, survivorship controls, and
  reproducibility. Its evidence map should be updated at preregistration and submission, and its
  identified weaknesses should be treated as minimum design gates.

### Local-to-frontier scaling and behavioral transport

- **Ruan, Maddison & Hashimoto (2024),
  [“Observational Scaling Laws and the Predictability of Language Model Performance”](https://arxiv.org/abs/2405.10938).**
  A low-dimensional capability model fitted across public model families predicts several smooth
  scaling phenomena and aggregate agent performance. This supports estimating a scale-dependent
  response surface, not treating small models as item-level or mechanistic substitutes. H13 must
  report per-item agreement and error topology alongside aggregate scores.
- **Schaeffer, Miranda & Koyejo (2023),
  [“Are Emergent Abilities of Large Language Models a Mirage?”](https://proceedings.neurips.cc/paper_files/paper/2023/hash/adc98a266f45005c403b8311ca7e8bd7-Abstract-Conference.html).**
  Discontinuous metrics can create apparent capability jumps. H13 therefore uses continuous
  numeric drift, step-error hazard, logit divergence where tokenizers match, and chain-survival
  curves rather than terminal accuracy alone.

### Quantization, reasoning depth, and propagation

- **Liu et al. (2025),
  [“Quantization Hurts Reasoning?”](https://arxiv.org/abs/2504.04823).** Across multiple
  reasoning-model families and sizes, W8A8 and W4A16 can be effectively lossless while more
  aggressive settings become model-, origin-, task-, and difficulty-dependent. This motivates a
  same-checkpoint precision ladder and explicit precision×scale×difficulty interactions.
- **Li et al. (2025),
  [“Quantization Meets Reasoning”](https://arxiv.org/abs/2505.11574).** Step-aligned math
  experiments find that low-bit failures often appear at an early vulnerable step and cascade to
  the answer. H13 tests this result in finance while separating conditional next-step incidence,
  free-running propagation, and portfolio-state feedback.
- **Kumar et al. (2024),
  [“Scaling Laws for Precision”](https://arxiv.org/abs/2411.04330).** Precision-aware scaling laws
  imply that post-training quantization loss can vary with model scale and training data. The
  result rules out a constant “4-bit penalty” pooled across checkpoints.
- **Mekala et al. (2025),
  [“Does Quantization Affect Models' Performance on Long-Context Tasks?”](https://aclanthology.org/2025.emnlp-main.479/).**
  Eight-bit performance was close to full precision on average, whereas some four-bit
  model×method×task cells degraded sharply. H13 crosses reasoning depth with context length so
  retrieval failure is not mislabeled chain propagation.

### Verifiable financial reasoning tasks

- **Xie et al. (2026),
  [FinChain](https://aclanthology.org/2026.acl-long.662/).** Parameterized templates cover 58
  topics across 12 financial domains with executable traces and step-aware evaluation. This is the
  cheapest primary engine for controlled depth and fresh numerical instantiations; synthetic
  templates still require a real-document bridge.
- **Chen et al. (2021), [FinQA](https://aclanthology.org/2021.emnlp-main.300/),** provides expert
  questions over financial reports with gold reasoning programs. **Reddy et al. (2024),
  [DocFinQA](https://aclanthology.org/2024.acl-short.42/),** extends the task to full documents and
  much longer contexts. Use stratified held-out subsets for ecological validation, not as the sole
  identification set because contamination and context length are harder to control.

### Open mechanistic tools and generalization limits

- **Lieberum et al. (2024),
  [Gemma Scope](https://arxiv.org/abs/2408.05147),** releases evaluated sparse autoencoders across
  Gemma 2 2B and 9B layers and selected 27B sites. This makes the family a low-cost discovery
  candidate because feature-training compute is already paid, but SAE features remain candidates
  until causal interventions validate them under each precision.
- **Wang et al. (2025),
  [“Towards Universality”](https://arxiv.org/abs/2410.06672),** reports many similar SAE features
  and analogous induction circuits across Transformer and Mamba models while retaining
  architecture-specific differences. H13 therefore requires three levels of transfer evidence:
  representational alignment, transferred intervention, and behavioral recovery. Correlation
  alone does not establish a universal mechanism.

### Adjacent foundations

- **Homogenization / algorithmic monoculture**: Kleinberg & Raghavan (2021) on monoculture in
  algorithmic decision-making; Bommasani et al. (2022), “Picking on the Same Person,” on outcome
  homogenization from shared algorithmic components; and Gorecki & Hardt (2025) on empirical
  monoculture versus model multiplicity across 50 language models. The proposed study applies
  these mechanisms to a matched trading benchmark; it does not originate them.
- **LLM behavioral finance**: Horton, Filippas & Manning (2023, revised 2026), “LLMs as simulated
  economic agents,” motivates the persona axis while also reinforcing that simulated-agent
  behavior is not evidence about humans without external validation.

### Experimental market microstructure

- **Smith (1962)** and the experimental-economics tradition of induced-value double auctions
  motivate the market-design benchmark. The current H5 simulator is not yet a validated continuous
  double auction and remains disabled until its explicit gates pass.
- **Gode & Sunder (1993)**, zero-intelligence traders: market institutions can produce
  efficiency without agent rationality — the reason our null cohort exists.

### Terminology and positioning contract

Phase-1 agents cannot coordinate because they neither interact nor observe one another. Agreement
there is **common-response convergence**, **correlated decisions**, or **outcome homogenization**.
LSV, Sias, one-sided cascades, or pairwise agreement can establish statistical herding or
synchronization under their assumptions, but not strategic collusion. “Tacit collusion” is
reserved for evidence of strategic response, profitable joint deviation, punishment, or a
comparable supra-competitive mechanism.

The proposed study should be positioned as a replication and extension: reproduce static/advisory
convergence and reduced dispersion in bridge cells, then ask *which shared components cause the
effect, whether it survives a fair classical comparison, and how ecology changes it*. It must not
promise that LLM cohorts are more convergent than human or institutional infrastructure unless the
H2 harmonization gate passes, and it must not carry simulator-bounded H5 causality into real
markets.
