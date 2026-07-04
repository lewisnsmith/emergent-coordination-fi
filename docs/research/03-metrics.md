# 03 — Metrics

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

- **Permutation test** for Δ: pool the two cohorts, permute cohort labels (respecting cohort
  sizes), recompute Δ; two-sided p from ≥10,000 permutations (agent-level relabeling — agents,
  not steps, are the exchangeable units).
- **Bootstrap CIs**: BCa bootstrap over agents (and over seeds for cross-run aggregates),
  ≥10,000 resamples, on every headline metric.
- **Multiple comparisons**: Holm–Bonferroni across the pre-registered hypothesis family
  H1–H5; exploratory analyses labeled as such.
- **Power analysis**: pilot variance from exp-000 sweeps determines seeds-per-cell to detect
  Δκ = 0.1 at power 0.8, α = 0.05 (procedure in `stats.py::power_seeds`).

## Reporting rules

- Every figure/table states: cohort sizes, seed count, chance floor, null-cohort value, CI.
- No metric is reported in isolation; the pre-registered hierarchy (κ → overlap → fingerprint)
  is always shown together.
