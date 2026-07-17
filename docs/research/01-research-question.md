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

## Canonical hypotheses

Let *D(C)* denote the within-cohort decision dispersion of cohort *C* (formally defined in
[03 — Metrics](03-metrics.md); lower dispersion = more convergence).

- **H1 (primary).** Given identical information sets, *D(LLM cohort) < D(baseline algo cohort)*,
  where the baseline cohort spans classical strategy families (momentum, mean-reversion,
  market-making, buy-and-hold, random).
- **H2.** LLM convergence differs from matched real-investor convergence after harmonizing
  universe, cadence, activity, and sampling. This is a descriptive external anchor.
- **H2b.** Even if pairwise LLM convergence is ordinary, shared-AI delegation increases its
  breadth, capital coverage, persistence, or affected-asset coverage.
- **H3 (within- vs cross-family).** Same-provider agent pairs (e.g., Claude–Claude) agree more
  than cross-provider pairs (Claude–GPT), which in turn agree more than chance.
- **H4 (persona sensitivity).** Persona/demographic instructions reduce convergence, but by less
  than information-set differentiation does: prompts change *style* more than *strategy*.
- **H5 (shared-market amplification).** In a shared exchange where agents' trades move prices,
  LLM cohorts produce stronger herding statistics (LSV, Sias) and more frequent one-sided
  cascades than baseline cohorts of equal size and capital.
- **H6 (trust/delegation).** Oversight, performance evidence, explanation, autonomy, and risk
  causally change how much capital people delegate to AI. This requires a human-subjects study;
  agent behavior cannot answer it.
- **H7 (near-term adoption).** Verified adoption evidence combined with the H5 dose-response
  threshold supports a calibrated, explicitly conditional threshold-crossing forecast.
- **H8 (causal drivers).** Controlled input interventions identify which client/market evidence
  drives API decisions; activation interventions identify mechanisms only in local models whose
  weights and activations are available. Generated rationales are not mechanistic proof.
- **H9 (transport).** Simulation-derived signatures retain locked discrimination and calibration
  on held-out simulations and real-market domains.
- **H10 (real-market causation).** AI exposure changes real-market outcomes only when exposure is
  verified and a randomized, staggered, or credible quasi-experimental counterfactual exists.
  Signature resemblance by itself never identifies AI as the cause.
- **H11 (data products).** Results can produce useful datasets when simulation truth, AI-like
  patterns, verified exposure, and causally verified events remain separate uncertainty-labeled
  tiers.
- **H12 (prompt pressure).** Stakes, urgency, emotional distress, and forced-action wording have
  separable effects on quality, suitability, safety, risk, abstention, and convergence.

The machine-readable source of truth is [`configs/research-program.yaml`](../../configs/research-program.yaml),
which maps H1–H12 (including H2b) to `exp-000` through `exp-024`, exact estimands, claim
boundaries, dependencies, outputs, and verification gates.

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
Separate protocols cover human trust, adoption projections, interpretability, and observational
real-market work. Real-money trading, automated live deployment, and claims of individual
financial advice remain out of scope.
