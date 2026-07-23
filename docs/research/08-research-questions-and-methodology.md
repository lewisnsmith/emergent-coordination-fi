# 08 — Research Questions and Methodology Guide

> **Working guide, not the canonical specification.** The research program has expanded beyond
> the original H1–H5 material below. Use
> [`configs/research-program.yaml`](../../configs/research-program.yaml) for H1–H12/H2b experiment
> IDs and claim boundaries, and [09–18](09-mphiq-factorial-design.md) for the operational MPHIQ,
> profile, prompt-pressure, statistical, safety, market/trust, interpretability, attribution,
> data-product, and cost protocols. If this guide conflicts with those sources, they control.

Purpose: this is a simple, editable working document for understanding the `flock` project, the data pipeline, the research questions, the interpretation process, and possible future research directions.

This document is intentionally practical. It is meant to answer:

- What am I looking at?
- What data am I working with?
- How does data move through the pipeline?
- What should I ask at each stage?
- How do I interpret agent/model behavior?
- How do I visualize the data and results?
- What research directions are worth pursuing?
- What might I be missing?

---

## 1. One-sentence project summary

`flock` studies whether LLM-powered trading agents independently converge on similar trading decisions, portfolios, strategies, and market behaviors more than classical trading algorithms or real-world market participants.

The main object of study is not profit.

The main object of study is convergence.

Profit, losses, drawdowns, and costs matter, but mostly as context for interpreting whether convergent behavior is economically meaningful or systemically risky.

---

## 2. Core research question

Primary question:

> Do LLM-powered trading agents converge on similar trading strategies to a greater extent than current market infrastructure — retail traders, institutional managers, and classical trading algorithms?

Practical version:

> If many LLM agents are given the same market information, do they buy, sell, hold, and build portfolios in unusually similar ways?

Systemic-risk version:

> If future markets rely heavily on a small number of foundation models, could market participants become correlated even without communicating with each other?

---

## 3. Central hypothesis family

### H1 — Primary convergence hypothesis

LLM cohorts have lower decision dispersion / higher agreement than baseline classical algorithm cohorts under identical information.

Operational question:

- Are LLM agents more likely to make the same buy/sell/hold decisions than baseline agents?

Primary metric:

- Pairwise Cohen's kappa across agent decisions.

---

### H2 — External-anchor hypothesis

LLM cohorts show convergence/herding levels comparable to or greater than empirical real-world trader panels.

Possible external anchors:

- 13F institutional holdings overlap.
- Prediction-market trader positioning.
- Other real participant panels if available.

Operational question:

- Do LLM-agent portfolios or flows look more correlated than real-world managers/traders?

---

### H3 — Provider-family hypothesis

Agents using the same foundation-model family agree more with each other than agents using different model families.

Example:

- Claude-Claude agreement > Claude-GPT agreement > chance.

Operational question:

- Is there a model-family fingerprint in trading behavior?

---

### H4 — Persona versus information hypothesis

Persona or demographic prompts reduce convergence, but less than genuinely different information sets.

Operational question:

- Does changing the agent's persona actually change strategy, or mostly change language/rationale style?

Important comparison:

- Same data + different personas.
- Different data/news subsets + same or similar personas.

---

### H5 — Shared-market amplification hypothesis

In a shared exchange where agents affect prices, LLM cohorts produce stronger herding, cascades, or liquidity effects than baseline cohorts.

Operational question:

- Does independent convergence become market-impacting coordination once agents trade together?

---

## 4. The basic pipeline

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

## 5. Major project components

### Data layer

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

### Agent layer

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

### Market layer

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

### Experiment layer

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

### Analysis layer

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

## 6. Data artifacts and what they mean

### `bars.parquet`

One row per timestamp-symbol market bar.

Expected columns:

- `ts`: timestamp or date.
- `symbol`: asset or contract identifier.
- `open`: opening price.
- `high`: high price.
- `low`: low price.
- `close`: closing/reference price.
- `volume`: traded volume or synthetic volume.

Questions to ask:

- What symbols are included?
- What date range is covered?
- Are timestamps aligned across symbols?
- Are there missing bars?
- Are prices adjusted?
- Is volume real or synthetic?
- Which price is used in observations?
- Which price is used for fills?
- Does the trailing observation window accidentally include future data?

---

### `events.parquet`

One row per event/news item.

Expected columns:

- `ts`: timestamp.
- `symbol`: related symbol, or empty/market-wide.
- `headline`: text shown or summarized to the agent.
- `sentiment`: numeric score, usually between -1 and 1.

Questions to ask:

- Are events synthetic or real?
- Are events visible to agents?
- Is sentiment visible to agents, or used only in analysis?
- Are events aligned with regime shifts?
- Could sentiment leak the correct future direction too directly?
- Are prediction-market outcomes hidden until after resolution?

---

### `meta.json`

Dataset metadata.

May include:

- builder name.
- parameters.
- seed.
- provenance.
- symbol list.
- date range.
- instrument type.

Questions to ask:

- Can this dataset be rebuilt exactly?
- Are all relevant parameters recorded?
- Does the dataset hash depend on all important inputs?

---

### `decisions.jsonl`

One row per agent-step decision.

Expected meaning:

- What did this agent decide at this time?
- What orders did it intend to place after parsing and clipping?
- What rationale did it provide?
- Was the response parsed successfully?
- How much did the call cost?

Important fields:

- `run_id`
- `step`
- `ts`
- `agent_id`
- `cohort`
- `kind`
- `model`
- `persona`
- `temperature`
- `seed`
- `observation_digest`
- `prompt_hash`
- `orders`
- `rationale`
- `parse_ok`
- `usage`
- `latency_s`

Questions to ask:

- Does `orders=[]` mean hold?
- Was this an actual hold or a parse-failure hold?
- Did the agent hallucinate unavailable information?
- Did the rationale match the order?
- Did multiple agents see byte-identical market information?
- Were orders clipped before logging?
- Is the action label too simple for multi-symbol decisions?

---

### `fills.parquet`

Executed trades.

Questions to ask:

- Did every submitted order fill?
- At what price?
- With what fee/slippage?
- Was the fill delayed to the next bar?
- Does replay mode fill differently from shared exchange mode?
- Do fills reconcile with portfolio changes?

---

### `portfolio.parquet`

Per-step per-agent portfolio state.

Typical contents:

- step.
- timestamp.
- agent_id.
- cohort.
- cash.
- equity.
- weights / positions.

Questions to ask:

- Are positions marked to current prices?
- Are long and short positions represented correctly?
- Is cash included in equity?
- Are position limits binding?
- Do portfolio weights explain the overlap metrics?

---

### `manifest.json`

Run provenance.

Should include:

- run ID.
- config.
- config hash.
- git SHA.
- dataset name/version/hash.
- model parameters.
- seed.
- number of agents.
- number of steps.
- total cost.

Questions to ask:

- Can this run be reproduced?
- Was the exact model ID recorded?
- Was the exact dataset hash recorded?
- Was the exact code version recorded?
- Are seeds and configs sufficient to reproduce non-LLM behavior?

---

## 7. Recommended process for understanding one experiment

### Step 1 — Read the config

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

### Step 2 — Inspect the dataset

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

### Step 3 — Reconstruct one decision

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

### Step 4 — Check action distributions

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

### Step 5 — Interpret convergence metrics

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

### Step 6 — Interpret statistics

For primary claims, ask:

- What is the effect size?
- What is the confidence interval?
- What is the permutation p-value?
- What is the null-cohort value?
- Is the result robust across seeds?
- Is the result robust across market regimes?
- Is the result robust to prompt paraphrases?
- Is the result robust to stronger baselines?

---

## 8. Main metric categories

### Decision-level convergence

Measures whether agents make similar buy/sell/hold decisions.

Key metrics:

1. Pairwise action agreement
   - Simple fraction of matching actions.
   - Easy to understand.
   - Can be inflated by hold-heavy behavior.

2. Cohen's kappa
   - Chance-corrected agreement.
   - More important than raw agreement.
   - Primary decision-level statistic.

3. Trade-direction correlation
   - Correlation of signed trade direction.
   - Useful when direction matters more than exact action labels.

Interpretation questions:

- Are agents truly agreeing, or just all holding?
- Are active trading decisions correlated?
- Does agreement remain after correcting for marginals?

---

### Portfolio-level convergence

Measures whether agents end up holding similar portfolios.

Key metrics:

1. Position cosine similarity
   - Are position vectors pointing in similar directions?

2. Portfolio overlap
   - Do agents hold the same assets in similar weights?
   - Useful for comparison with fund/13F-style overlap.

3. Return correlation
   - Do agents' portfolios make or lose money together?

Interpretation questions:

- Do similar decisions produce similar portfolios?
- Are agents exposed to the same assets?
- Are agents exposed to the same losses during stress?

---

### Strategy-level convergence

Measures whether agents appear to follow similar underlying strategies.

Key metrics:

1. Strategy fingerprint
   - Regress signed trade flow on market signals such as:
     - momentum.
     - short-term reversal.
     - distance from moving average.
     - realized volatility.
   - Compare coefficient vectors across agents.

2. Rationale clustering
   - Compare text rationales.
   - Useful but should be treated carefully.

Interpretation questions:

- Are agents using the same signals?
- Do they explain their trades similarly?
- Are trades similar even when rationales differ?
- Are rationales similar even when trades differ?

---

### Coordination / herding metrics

Mostly useful for Phase 2 shared-exchange experiments and real-world reference panels.

Key metrics:

1. LSV herding statistic
   - Are active traders disproportionately on the same side?

2. Sias serial herding
   - Does buying/selling pressure persist over time?

3. Cascade detection
   - Are there runs of one-sided cohort flow?

4. Liquidity withdrawal
   - Does order-book depth disappear around cohort-wide sell pressure?

Interpretation questions:

- Does convergence become price-impacting behavior?
- Are agents creating cascades?
- Are agents withdrawing liquidity together?
- Is shared-market feedback amplifying correlation?

---

## 9. Best visualizations to build or inspect

### Dataset visualizations

1. Price chart by symbol.
2. Return chart by symbol.
3. Rolling volatility by symbol.
4. Event/news overlay on prices.
5. Return correlation matrix.
6. Regime-colored price chart for synthetic data.
7. Missing-data heatmap.

---

### Decision visualizations

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

### Portfolio visualizations

1. Equity curves by agent/cohort.
2. Equity fan chart by cohort.
3. Drawdown curves by cohort.
4. Position weight heatmap.
5. Portfolio overlap heatmap.
6. Turnover by cohort.
7. Cash/constraint usage over time.

---

### Strategy visualizations

1. Fingerprint coefficient bar charts.
2. PCA or UMAP of strategy fingerprints.
3. Agent clustering dendrogram.
4. Rationale similarity heatmap.
5. Rationale cluster examples.
6. Signal exposure over time.

---

### Statistical visualizations

1. Bootstrap confidence interval forest plot.
2. Permutation null distribution with observed statistic marked.
3. Effect size by seed.
4. Effect size by market regime.
5. Holm-adjusted p-value table.
6. Power curve showing required seeds per cell.

---

### Shared-exchange visualizations

1. Order book depth over time.
2. Midprice with cohort net flow overlay.
3. Cascade event timeline.
4. Liquidity before/after cohort-wide selling.
5. Spread over time.
6. LSV herding over time.
7. Price impact versus LLM market share.

---

## 10. Best questions to ask about data quality

### General data quality

- Are timestamps consistent?
- Are time zones handled?
- Are there duplicate rows?
- Are there missing bars?
- Are all symbols present at every step?
- Are prices positive?
- Are returns plausible?
- Is volume plausible?
- Are splits/dividends adjusted in equities?
- Are prediction-market prices bounded between 0 and 1?
- Are resolved outcomes hidden before resolution?
- Are event timestamps realistic?
- Are synthetic data regimes balanced?

---

### Leakage questions

- Does any observation include future prices?
- Does an event mention something that would only be known later?
- Does sentiment reveal the future direction too directly?
- Does the agent know the final outcome of a prediction market?
- Are regime labels hidden from agents?
- Are fills based on future information only after the decision is made?
- Does the prompt include summary statistics computed using future data?

---

### Reproducibility questions

- Is every random draw seeded?
- Is the dataset hash recorded?
- Is the config hash recorded?
- Is the git SHA recorded?
- Is the model ID recorded?
- Are provider parameters recorded?
- Are prompts hashed?
- Are LLM responses cached?
- Can the same analysis be rerun offline?

---

## 11. Best questions to ask about agents

### Behavioral questions

- How often does each agent trade?
- Which symbols does each agent prefer?
- Does each agent follow momentum?
- Does each agent follow reversal?
- Does each agent respond to volatility?
- Does each agent respond to news sentiment?
- Does each agent diversify?
- Does each agent overtrade?
- Does each agent become more conservative after losses?
- Does each agent double down after losses?
- Does each agent obey risk constraints?
- Does each agent hallucinate information?
- Does each agent cite unavailable data?

---

### LLM-specific questions

- Does temperature change trades or only language?
- Does persona change trades or only language?
- Does reasoning effort increase or decrease convergence?
- Do stronger models converge more?
- Do weaker models follow prompt defaults more?
- Does memory increase convergence over time?
- Does memory create path dependence and divergence?
- Are rationales faithful to actions?
- Are rationales more diverse than decisions?
- Can provider/model be predicted from trades alone?
- Can provider/model be predicted from rationales alone?

---

### Error and failure questions

- How often does JSON parsing fail?
- Are parse failures concentrated in a model/provider?
- Are parse failures counted as holds?
- Do parse failures bias convergence metrics?
- Are invalid symbols produced?
- Are invalid quantities produced?
- Are orders clipped by cash or position limits?
- Are constraints causing artificial convergence?

---

## 12. Best research directions

### Direction 1 — Core convergence result

Question:

- Do LLM cohorts show higher within-cohort decision agreement than baseline algorithm cohorts?

Why it matters:

- This is the central paper claim.

Required controls:

- Null/random cohort.
- Chance-corrected metrics.
- Multiple seeds.
- Strong baseline strategies.
- Prompt paraphrases.
- Synthetic and real data.

---

### Direction 2 — Same-provider versus cross-provider convergence

Question:

- Do agents from the same model family agree more than agents from different model families?

Possible result:

- Claude agents cluster together.
- GPT agents cluster together.
- Gemini agents cluster together.

Why it matters:

- Could imply foundation-model-specific trading fingerprints.

---

### Direction 3 — Model capability scaling

Question:

- Does convergence increase with model capability, model size, or reasoning effort?

Two competing interpretations:

1. Smarter agents find the same optimal strategy.
2. More capable/aligned agents share more priors and therefore converge.

---

### Direction 4 — Temperature and sampling diversity

Question:

- Does higher temperature reduce convergence?

Follow-up:

- Does it reduce performance?
- Does it diversify actions or only rationales?

---

### Direction 5 — Persona sensitivity

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

### Direction 6 — Information-set differentiation

Question:

- Does giving agents different information reduce convergence more than giving them different personas?

Why it matters:

- If yes, market diversity may require information diversity, not just model/persona diversity.

---

### Direction 7 — Memory and path dependence

Question:

- Does agent memory make agents converge or diverge over time?

Possible outcomes:

1. Memory increases convergence because agents learn the same lessons.
2. Memory decreases convergence because different portfolio histories create path dependence.

---

### Direction 8 — Regime dependence

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

### Direction 9 — Contamination robustness

Question:

- Do LLMs behave differently on historical data they may have memorized versus synthetic or post-cutoff data?

Robustness tools:

- synthetic markets.
- anonymized symbols.
- post-training-cutoff windows.
- obscure assets/contracts.
- transformed return series.

---

### Direction 10 — Shared-market amplification

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

### Direction 11 — Tacit collusion / market-maker behavior

Question:

- Can LLM market makers widen spreads or reduce competition without explicit communication?

Why it matters:

- Connects to algorithmic tacit collusion literature.

Important caution:

- Use careful language. Do not claim illegal collusion unless there is explicit evidence and a legal framework.

---

### Direction 12 — Detection and surveillance

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

### Direction 13 — Decorrelation interventions

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

### Direction 14 — Rationale faithfulness

Question:

- Do LLM rationales faithfully explain trades?

Tests:

- Compare rationale similarity to trade similarity.
- Compare stated signal use to regression-implied signal use.
- Look for hallucinated reasons.
- Use counterfactual observations.

---

### Direction 15 — Market ecology experiments

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

## 13. Important threats to validity

### Threat 1 — Hold-heavy behavior

Problem:

- If all agents mostly hold, raw agreement will be high even without meaningful convergence.

Mitigation:

- Use Cohen's kappa.
- Report action distributions.
- Analyze active-trader-only agreement.
- Track parse failures.
- Track constraint-driven holds.

---

### Threat 2 — Prompt-induced convergence

Problem:

- A shared prompt template may cause similar behavior.

Mitigation:

- Prompt paraphrase battery.
- Multiple prompt styles.
- Minimal prompts.
- Persona variation.
- Information-set variation.

---

### Threat 3 — Weak baselines

Problem:

- If classical baselines are too simple, LLMs may look artificially unusual.

Mitigation:

- Add stronger and more diverse baselines.
- Randomize baseline hyperparameters.
- Include ensemble strategies.
- Include volatility targeting and risk controls.

---

### Threat 4 — Historical data contamination

Problem:

- Models may have memorized famous historical price patterns or market events.

Mitigation:

- Use synthetic data.
- Use post-cutoff data.
- Use obscure assets.
- Anonymize symbols.
- Transform returns.

---

### Threat 5 — Leakage

Problem:

- Future information may accidentally enter observations.

Mitigation:

- Audit observation construction.
- Verify trailing windows.
- Hide resolution outcomes.
- Hide regime labels.
- Avoid future-computed summaries.

---

### Threat 6 — Multi-symbol action simplification

Problem:

- A single buy/sell/hold action can hide multi-symbol behavior.

Example:

- An agent buys AAPL and sells MSFT, but the net action may simplify this too much.

Mitigation:

- Compute symbol-level action metrics.
- Compute signed quantity correlations.
- Compute portfolio-level metrics.

---

### Threat 7 — Constraints create convergence

Problem:

- Agents may all hold because they run out of cash or hit position limits.

Mitigation:

- Track cash.
- Track position-limit hits.
- Track clipped orders.
- Report turnover.

---

### Threat 8 — Rationale unreliability

Problem:

- LLM explanations may not faithfully explain actions.

Mitigation:

- Treat rationale analysis as secondary.
- Compare rationales with actual signal loadings.
- Audit hallucinations.

---

### Threat 9 — External-anchor mismatch

Problem:

- 13F quarterly holdings and simulated daily trades are not directly equivalent.

Mitigation:

- Be explicit that real-world panels are anchors, not perfect controls.
- Match metrics carefully.
- Avoid overclaiming.

---

### Threat 10 — Provider nondeterminism

Problem:

- Even temperature-zero LLM calls can vary across providers/time.

Mitigation:

- Cache responses.
- Record model IDs and parameters.
- Record prompt hashes.
- Record response hashes if possible.
- Keep offline replay possible.

---

## 14. Stronger baseline ideas

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

## 15. Suggested immediate next work

### Work item 1 — Data dictionary

Create or maintain a simple data dictionary for every input and output artifact.

Include:

- file path.
- row meaning.
- column definitions.
- producer code.
- consumer code.
- caveats.

---

### Work item 2 — One-decision audit tool

Build a tool that takes:

- run ID.
- agent ID.
- step.

And prints:

- observation.
- recent bars.
- news.
- portfolio before decision.
- prompt hash / prompt if available.
- decision.
- clipped order.
- fill.
- portfolio after decision.

This may be the most useful interpretability tool in the project.

---

### Work item 3 — Action raster visualization

Build a plot:

- x-axis: time/step.
- y-axis: agent.
- color: buy/sell/hold.

This will make convergence visually obvious.

---

### Work item 4 — Cohort net-flow visualization

Plot net signed flow by cohort over time.

Purpose:

- See when cohorts collectively buy or sell.

---

### Work item 5 — Constraint and parse-failure audit

Report:

- parse failure rate by model/cohort.
- clipped order frequency.
- position-limit hits.
- cash exhaustion.
- hold rate.

Purpose:

- Prevent artificial convergence from being mistaken for real convergence.

---

### Work item 6 — Stronger baseline suite

Add and test more classical baselines before relying on the main comparison.

---

### Work item 7 — Prompt paraphrase battery

Before real confirmatory sweeps, create multiple semantically equivalent task prompts.

Purpose:

- Test whether convergence is caused by the prompt template.

---

### Work item 8 — Pilot power analysis

Use exp-000 pilot variance to fill preregistration blanks:

- seeds per cell.
- cohort size.
- dataset windows.
- model list.
- paraphrase count.

---

## 16. Recommended interpretation discipline

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

## 17. Simple checklist before trusting a result

Before believing any result, check:

- [ ] Dataset is understood.
- [ ] Dataset hash is recorded.
- [ ] Config hash is recorded.
- [ ] Git SHA is recorded.
- [ ] Seeds are recorded.
- [ ] Agent list is known.
- [ ] Cohort sizes are equal or justified.
- [ ] Action distributions are reported.
- [ ] Parse failures are reported.
- [ ] Constraint clipping is reported.
- [ ] Null cohort is included.
- [ ] Baselines are strong enough.
- [ ] Cohen's kappa is reported, not just raw agreement.
- [ ] Portfolio metrics are reported.
- [ ] Strategy fingerprint metrics are reported.
- [ ] Confidence intervals are reported.
- [ ] Permutation tests are reported.
- [ ] Multiple comparisons are handled for confirmatory claims.
- [ ] Prompt-template sensitivity is checked.
- [ ] Regime sensitivity is checked.
- [ ] Contamination concerns are addressed.
- [ ] Claims are labeled confirmatory or exploratory.

---

## 18. The best high-level framing

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

---

## 19. Most important next questions

If you only focus on a short list, focus on these:

1. Can I reconstruct exactly what one agent saw and did at one step?
2. Are LLM agents more convergent than baselines after chance correction?
3. Is the result driven by holds, parse failures, or constraints?
4. Does the result survive across seeds?
5. Does the result survive across regimes?
6. Does the result survive prompt paraphrases?
7. Does the result survive stronger baselines?
8. Does information diversity reduce convergence more than persona diversity?
9. Are trades, portfolios, fingerprints, and rationales telling the same story?
10. Does convergence become herding or cascades in the shared exchange?
11. Can model/provider identity be detected from behavior alone?
12. What intervention best reduces harmful convergence without destroying performance?

---

## 20. Suggested document structure for future expansion

This file can be split later into:

1. `data-dictionary.md`
2. `methodology-guide.md`
3. `research-question-backlog.md`
4. `visualization-roadmap.md`
5. `threats-to-validity.md`
6. `experiment-playbook.md`
7. `model-interpretability-guide.md`

For now, keep it as one editable overview document until the project direction stabilizes.
