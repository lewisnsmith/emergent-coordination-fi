# Scientific decisions

## Branch unit

A branch represents one report or release that can be completed, verified, and merged without an
unfinished sibling claim. Every experiment has one owning branch. Hypotheses may recur, but the
packet declares whether each role is primary, secondary, supporting, contextual, exploratory, or
removed by amendment.

Downstream branches consume checksummed releases, not unfinished feature branches. Study-specific
tooling remains namespaced until a verified publication demonstrates genuine shared use. Before a
study ships, current `main` is merged into it and the full release is reverified so `main` can move
forward without importing unfinished siblings.

## Evidence corrections

- Exp-008 is exploratory H1/H3/H4 work, not H12 pressure evidence.
- Exp-009 covers H1/H3 replay robustness; H4 robustness belongs to exp-006/007.
- Exp-014 simulates execution and does not answer H6 human trust.
- Exp-016 supplies black-box H8 attribution and only supports later H12 methods.
- Exp-020 detects resemblance and does not answer H10 causal attribution.
- Exp-024 reports measured pathways, not formal mechanistic mediation.
- Exp-022 omits unavailable tiers and never merges different causal statuses.
- Exp-017 retains its narrowed checkpoint-, prompt-, trajectory-, intervention-, and
  synthetic-exchange-bounded design.

## Evidence separation

- Simulated exchange causality does not imply real-market causality.
- Signature resemblance does not identify AI exposure; exposure does not identify causation
  without a credible counterfactual.
- Closed-model input interventions are black-box attribution, not activation-level mechanism
  evidence.
- Human trust requires approved, consented participant data.
- Alpha evaluation is not mechanism evidence and does not authorize live trading.

## Development and publication

The shared publication base contains only reusable integrity utilities and publication conventions.
Study branches receive code only with its complete import and test closure. A missing runner,
verifier, input, rights record, cost estimate, or approval is a blocker, not a placeholder output.

Positive, null, and negative results use the same verification and release requirements. Local or
remote publication refs are not evidence that an experiment ran. Remote writes, data or model
acquisition, provider calls, participant contact, spending, registration, and publication each
retain separate authorization gates.

## Recovery

The former broad family tips remain under `backup/pre-publication-units/*`. Their exact mapping,
tips, shared tree, and supplemental bundle hash are recorded in `branch-corrections.yaml`. Historical
source material remains recoverable at `4016845`; it is not merged wholesale into a study.
