# 01 — Research Question

## Primary question

**Which shared components make LLM trading agents converge, and how does that convergence compare
with classical strategies under matched homogeneous and heterogeneous cohort ecologies?**

The first paper studies **common-response convergence** and **outcome homogenization**. Phase-1
agents do not interact, observe each other, or move prices, so agreement there is not emergent
coordination or collusion. The motivating risk is that many participants may independently respond
similarly because they share model lineage, training priors, prompts, harnesses, or information.
Whether that common response causes market harm is a separate simulator-bounded question under H5.

## Why it matters

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

## First-paper hypotheses

Let *D(C)* denote the within-cohort decision dispersion of cohort *C* (formally defined in
[03 — Metrics](03-metrics.md); lower dispersion = more convergence).

- **H1 (technology × ecology).** In the matched 2×2 benchmark—LLM versus classical technology,
  crossed with homogeneous versus heterogeneous family ecology—the family-weighted technology
  contrast and technology-by-ecology interaction differ from zero. The directional expectation
  that LLM cohorts are more convergent is frozen only after the SESOI and power design are fixed.
- **H3 (lineage).** Within LLM technology, same-model and same-provider pairs differ in
  convergence from provider-balanced cross-family pairs under held-constant information, profile,
  harness, and prompt conditions.
- **H4 (component decomposition).** In the balanced MPHIQ design, genuine information-set
  differentiation changes convergence more than profile or wording differentiation; model,
  profile, harness, information, and question effects are reported separately.

The benchmark includes homogeneous LLM, heterogeneous LLM, homogeneous classical, and
heterogeneous classical cells. Homogeneous cells sample one family with within-family variation;
heterogeneous cells use the same frozen number and weights of families. Activity, capital,
information, feasible actions, fees, and constraints are matched. Primary contrasts first average
within each provider or strategy family and then apply frozen equal or population-justified family
weights, so adding endpoints to one family cannot silently change the estimand.

## Conditional anchor and future program

- **H2 (conditional external anchor).** Real-investor convergence is descriptive and enters the
  first paper only if universe, cadence, activity, sampling, position direction, and capital
  weighting can be harmonized. Unmatched 13F or trader panels are reported separately and cannot
  rank AI against “current infrastructure.”
- **H5 (separate simulator experiment).** Randomized AI-managed capital share may change
  preregistered market outcomes inside a validated shared-exchange simulator. Any causal language
  is internal to that simulator and does not establish a real-market effect.
- **H2b and H6–H12 (future program).** Delegation breadth, human trust, adoption forecasting,
  interpretability, signature transport, real-market attribution, data products, and prompt
  pressure remain separate protocols. They are neither first-paper endpoints nor claims.

The machine-readable catalog is
[`configs/research-program.yaml`](../../configs/research-program.yaml), which maps the broader
H1–H12 program (including H2b) to `exp-000` through `exp-024`. The narrower first-paper claim and
analysis contract is frozen through [06 — Preregistration](06-preregistration.md).

## Operationalization

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

## Scope

The first paper covers synthetic trajectories and nonoverlapping historical replay windows in US
equities, with binary prediction-market replay as a held-out market-type replication if its data
gate passes. It tests H1/H3/H4 only. H5 uses a separate shared simulated exchange, and H2 is
included only under its harmonization gate. H6–H12 remain future papers. Real-money trading,
automated live deployment, claims of individual financial advice, and real-market causal claims
from simulated resemblance remain out of scope.
