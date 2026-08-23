# Alpha out-of-sample signal evaluation

## Question

Does one frozen consensus signal produce positive net benchmark-relative next-session return in a
lawfully sourced untouched historical panel?

## Design

Pin the Qwen checkpoint and a hashed five-prompt clean set. For SPY, QQQ, IWM, and TLT from
2025-08-01 through 2026-07-31, signal after day-t close, go long next session only when at least
four of five prompts say `BUY`, otherwise hold cash, enter day-t+1 open, and exit day-t+1 close.
Charge five basis points per one-way turnover. The threshold cannot be retuned.

## Estimands, units, and controls

Estimate net benchmark-relative mean next-session return against equal-weight buy-and-hold; cash is
a second benchmark. Report return, turnover, costs, drawdown, Sharpe, failures, missing prices,
exposure, and uncertainty using frozen asset/session blocks. The attempted-variant ledger has one
row for this cohort. Support requires the 95% interval above zero; rejection requires its upper
bound at or below zero; otherwise the result is inconclusive.

## Failure rules and limits

Lookahead, timestamp mismatch, prompt/checkpoint drift, missing cost charges, unauthorized data, or
an altered ledger blocks the verdict. Future monitoring creates a new versioned cohort and never
revises this window. This is not mechanism evidence, a live strategy, investment advice, or a claim
that performance persists.

## Execution sequence

1. Test timing, lookahead prevention, costs, turnover, failures, benchmarks, and checksums on fixtures.
2. Freeze the model, prompts, universe, dates, signal, costs, missingness, uncertainty, and ledger.
3. Resolve data lineage, lawful use, acquisition, spending, and release rights before inspection.
4. Gate local signal generation and materialize timestamped decisions without changing the rule.
5. Run the evaluator once, preserve all failures, and assign the frozen three-way verdict.
6. Release every verdict under the same separate-track contract; no broker order is authorized.
