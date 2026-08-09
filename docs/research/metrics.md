# Metrics

All metrics are computed within-cohort and reported alongside the null-cohort value and a
marginal-preserving chance floor. Implementations live in `src/flock/analysis/`.

## Notation

Cohort *C* with agents *i = 1..n*; steps *t = 1..T*; symbols *s*. Agent *i*'s action at *(t, s)*
is *a_i(t,s) ∈ {buy, sell, hold}* with signed size *q_i(t,s)*. Position vector *w_i(t)* is the
agent's portfolio weights at *t*.

## Decision-level convergence (`convergence.py`)

- **Pairwise action agreement**: for each pair (i, j),
  `A_ij = mean_t,s [ 1{a_i(t,s) = a_j(t,s)} ]`. Cohort statistic: mean over pairs.
- **Chance-corrected agreement (Cohen's κ)** per pair, using each pair's empirical action
  marginals; cohort mean κ. This is the primary decision-level statistic (robust to hold-heavy
  behavior).
- **Trade-direction correlation**: Pearson correlation of sign(q_i) with sign(q_j) over (t, s)
  cells where at least one trades.

## Portfolio-level convergence (`convergence.py`)

- **Position cosine similarity**: `cos(w_i(t), w_j(t))` averaged over t and pairs.
- **Portfolio overlap** (fund-overlap style, comparable to 13F panels):
  `O_ij(t) = Σ_s min(|w_i(t,s)|, |w_j(t,s)|)` for long weights; cohort mean over pairs, t.
- **Return correlation**: correlation of per-step portfolio returns across agents.

## Strategy-level convergence (`strategy.py`)

- **Strategy fingerprint**: regress agent i's signed trade flow on canonical signals computed
  from market data only — momentum (12-1 style lookback), short-term reversal, distance from
  moving average, realized volatility. The coefficient vector β_i is the fingerprint.
  **Fingerprint dispersion** = mean pairwise Euclidean distance between standardized β_i.
- **Rationale clustering**: embed decision rationales (locally, hash-TF-IDF by default so the
  pipeline stays offline; sentence-embedding model optional) and report mean pairwise cosine
  similarity plus cluster count at fixed threshold.

## Headline dispersion statistic

For any similarity metric *m* above, define **dispersion** `D(C) = 1 − mean_pairs m`.
The headline result is the contrast `Δ = D(baseline cohort) − D(LLM cohort)` with a permutation
p-value and bootstrap CI (below). Reported for κ (primary), portfolio overlap, and fingerprint
distance (converted to a similarity via negative standardization).

The implementation scores actions on the full `(step, symbol)` grid. Portfolio-net actions are
retained only for display; they are not the confirmatory endpoint because offsetting buy/sell
orders could otherwise be mislabeled as a hold.

## Breadth and market-dynamics outcomes

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

## Quality, suitability, and safety outcomes

Prompt-pressure results use normalized regret against a constrained oracle, goal attainment,
shortfall probability, liquidity preservation, drawdown, turnover, hard-constraint violations,
unsupported evidence, fabricated facts, unsupported certainty, and abstention. “Better” requires
practical quality improvement plus safety/suitability noninferiority. “Equivalent” requires TOST;
a nonsignificant difference is inconclusive.

## H13 local fidelity and quantization propagation

H13 reports three references separately: executable-oracle correctness, same-checkpoint
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

## Herding / coordination (`coordination.py`, Phase 2 + real-world panels)

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

## Statistical inference (`stats.py`)

- **Randomization inference:** single-run agent relabeling is diagnostic only. Confirmatory
  inference uses paired sign flips over independent market-window/seed blocks; Phase 2 assigns
  whole market replicas because agents interfere.
- **Bootstrap CIs:** BCa/hierarchical resampling uses the highest independent unit first (windows,
  market replicas, people), preserving nested model/agent observations.
- **Equivalence/noninferiority:** paired TOST uses preregistered SESOI bounds; one-sided safety
  tests use adverse margins. Nonsignificance is never relabeled as sameness or safety.
- **Multiple comparisons:** Holm correction applies within the locked confirmatory family;
  exploratory high-dimensional MPHIQ screens use hierarchical false-discovery control before
  held-out confirmation.
- **Power analysis**: pilot variance from exp-000 sweeps determines seeds-per-cell to detect
  Δκ = 0.1 at power 0.8, α = 0.05 (procedure in `stats.py::power_seeds`).

## Reporting rules

- Every figure/table states: cohort sizes, seed count, chance floor, null-cohort value, CI.
- No metric is reported in isolation; the pre-registered hierarchy (κ → overlap → fingerprint)
  is always shown together.
- Every claim records its independent unit, effect, interval, raw and corrected p-value or
  equivalence verdict, sensitivity checks, config/data hashes, and linked output artifact.
