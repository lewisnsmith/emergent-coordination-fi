# 01 — Research Question

## Primary question

**Do LLM-powered trading agents converge on similar trading strategies to a greater extent than
current market infrastructure — retail traders, institutional managers, and classical trading
algorithms?**

We study this as a question about **emergent coordination**: if many market participants are
instances of (or advised by) a small number of foundation models, do their decisions correlate
more strongly than the decisions of today's heterogeneous participants — and does that
correlation constitute a new systemic channel for herding, crowding, and coordinated price
pressure?

## Why it matters

- **Systemic risk.** Crowded trades and correlated liquidation are classic amplifiers of market
  stress (quant quake 2007, March 2020 dash-for-cash). If LLM agents share a common prior — the
  same pre-training distribution, the same RLHF objectives — correlation may arise *without any
  communication*, which existing surveillance (focused on communication and common ownership)
  would not detect.
- **Market efficiency.** Convergent agents may arbitrage away the same signals faster, or may
  collectively neglect signals outside the models' shared blind spots.
- **Algorithmic coordination policy.** Regulators already worry about algorithmic tacit collusion
  (Calvano et al. 2020). LLM agents extend that concern from pricing algorithms to general
  trading mandates.

## Hypotheses

Let *D(C)* denote the within-cohort decision dispersion of cohort *C* (formally defined in
[03 — Metrics](03-metrics.md); lower dispersion = more convergence).

- **H1 (primary).** Given identical information sets, *D(LLM cohort) < D(baseline algo cohort)*,
  where the baseline cohort spans classical strategy families (momentum, mean-reversion,
  market-making, buy-and-hold, random).
- **H2.** *D(LLM cohort)* is lower than the empirical dispersion of real-world participant
  panels (13F institutional holdings overlap; prediction-market trader positioning) measured
  with the same overlap/herding statistics.
- **H3 (within- vs cross-family).** Same-provider agent pairs (e.g., Claude–Claude) agree more
  than cross-provider pairs (Claude–GPT), which in turn agree more than chance.
- **H4 (persona sensitivity).** Persona/demographic instructions reduce convergence, but by less
  than information-set differentiation does: prompts change *style* more than *strategy*.
- **H5 (shared-market amplification).** In a shared exchange where agents' trades move prices,
  LLM cohorts produce stronger herding statistics (LSV, Sias) and more frequent one-sided
  cascades than baseline cohorts of equal size and capital.

## Operationalization

- An **agent** is a decision function `observe → decide` producing orders each step; LLM agents
  are parameterized by (provider, model, temperature, reasoning effort, persona prompt, memory).
- A **strategy** is operationalized two ways: (a) the realized decision stream itself, and
  (b) a *strategy fingerprint* — loadings from regressing the agent's trades on canonical factor
  signals (momentum, reversal, value proxy, volatility).
- **Convergence** is low within-cohort dispersion across the metric hierarchy: decision-level
  (per-step action agreement), portfolio-level (position similarity over time), and
  strategy-level (fingerprint distance, rationale-embedding distance).
- **Current infrastructure** is proxied by (a) classical algo baselines run under identical
  conditions (internal control) and (b) empirical dispersion panels from real markets (external
  anchor). Both comparisons are reported; neither alone is dispositive.

## Scope

Markets: US equities (daily bars) and binary prediction markets (Polymarket/Kalshi-style
contracts). Phase 1 uses historical **replay** (no price impact — isolates convergence);
Phase 2 uses a **shared simulated exchange** (price impact and feedback — tests coordination).
Real-money trading, RL/fine-tuned agents, and live deployment are out of scope.
