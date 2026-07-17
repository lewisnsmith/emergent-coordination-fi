# 21 — Mistake Case Study: When Many Agents Are Still One Experiment

**Status: DESIGN CASE STUDY; no empirical effect sizes or p-values are reported here. Last
updated: 2026-07-17.** This case study records a consequential mistake found while hardening Flock
and the associated benchmark redesign. It is not a before/after results comparison, because no
verified paid result is yet available.

## The tempting analysis

Suppose many agents process the same market trajectory. Each agent makes many decisions, each
model may be called with multiple seeds or paraphrases, and pairwise convergence creates still more
rows. It is tempting to compute an agent- or pair-level effect and use the number of agents, pairs,
steps, or calls as the inferential sample size.

That analysis answers a conditional descriptive question—how much the nested observations differ
inside the realized path—but it does not create new independent market histories. Shared prices,
news, opportunity sets, and shocks can make every nested observation move together. More calls on
the same path can make a standard error look arbitrarily precise while adding no independent
evidence about how the effect varies across paths.

Symbolically, let `y[u,t,a]` be an outcome for agent `a` at step `t` in trajectory or window `u`.
The invalid paper path acts as though many `(t,a)` rows are independent. The corrected path first
forms a frozen block effect:

```text
d[u] = aggregate_within_block(treatment outcomes in block u)
     - aggregate_within_block(matched control outcomes in block u)
```

Inference is then based on independent `u` blocks or their declared dependence clusters. Agent,
pair, step, prompt, retry, and response-seed variation remains useful for estimating `d[u]`,
diagnosing mechanisms, and measuring reliability, but it cannot increase confirmatory `n`.

## A second mistake hidden in the baseline

Even correct block-level inference cannot rescue a confounded contrast. The original framing risked
comparing a closely related LLM cohort with a purposefully diverse collection of classical
strategies. In that comparison, “LLM versus classical” also means “homogeneous versus
heterogeneous.” A convergence difference cannot be attributed to technology alone.

The redesign crosses the factors:

| Technology | Homogeneous ecology | Heterogeneous ecology |
|---|---|---|
| LLM | Repeated agents within one exact frozen family, estimated family by family | Frozen balanced mixture across sampled families |
| Classical | One strategy family with parameter/seed variation, estimated family by family | Frozen balanced mixture across classical families |

The paper-level estimands are within-ecology technology contrasts and the
technology-by-ecology interaction. Family balancing prevents a provider with more endpoints from
silently receiving more weight. Matching activity, capital, information, constraints, turnover,
and action marginals reduces alternative explanations but does not establish a universal model
effect.

## What changed in the repository

- Single-run analysis is diagnostic and cannot become paper evidence merely by exporting a
  significance result (`049b663`).
- The research contract defines trajectories/nonoverlapping window clusters as the highest
  independent units and explicitly prohibits nested observations from inflating `n`.
- The compiled study design balances `technology × ecology` cells, family rotations, held-out
  sets, calls, and declared budgets before execution.
- Study-level analysis rejects duplicated block evidence and documents when a sign-flip sensitivity
  relies on symmetry rather than an actual randomized assignment.

These safeguards reduce known failure modes; they do not prove that every dependence structure or
confound has been eliminated. That judgment still needs simulation recovery, a frozen analysis
plan, and independent statistics review.

## The honest before/after artifact to publish later

After a real pilot exists, create a release-derived comparison with no hand-entered numbers:

1. show the invalid agent-level analysis only as a labeled diagnostic demonstration;
2. show the corrected block effects with every independent unit visible;
3. report how point estimates, intervals, and effective `n` change, including null or inconclusive
   outcomes;
4. identify any remaining cluster, overlap, missingness, or activity-balance sensitivity; and
5. link both displays to the same hashed inputs and analysis code.

Do not fill this section with illustrative effect sizes that could be mistaken for observed
results. If the corrected result is weaker, reverses, or becomes inconclusive, that is the central
lesson rather than a presentation problem.

## Why this is evidence of research maturity

The important contribution is not that the first design had no flaws. It is that a consequential
error was made legible, corrected before confirmatory calls, encoded as an automated release gate,
and retained in the public history. The defensible story is therefore one of error detection and
scientific revision, not retrospective perfection. The dated reconstruction is in
[20 — Research Log](20-research-log.md), and human reviewers should challenge the correction using
[22 — Independent Review and Response](22-independent-review-response.md).

