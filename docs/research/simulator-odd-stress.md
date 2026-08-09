# H5 Simulator ODD/STRESS Report and Release Gate

**Status: INCOMPLETE; H5 confirmatory execution and “continuous double auction” claims are
blocked.** This document describes the simulator that exists in the tagged code, distinguishes
implemented mechanisms from proposed ones, and defines the validation evidence required before
the H5 AI-capital-share experiment can enter a paper.

## Purpose and claim boundary

H5 asks how assigning different fractions of simulated capital to LLM-controlled agents changes
outcomes inside a specified artificial market. It does not estimate a real-market treatment
effect. The intended treatment is assigned to independently initialized whole-market replicas at
AI capital shares of `0%, 10%, 25%, 50%, 75%, 100%`; traders, orders, fills, and ticks are nested
observations. Every result must say “within this simulator.”

The implementation is presently a **step-synchronous price-time-priority call process with an
intra-step limit-order book**, not a validated continuous double auction. Orders receive a seeded
random arrival order within each step, cross against resting orders at the resting price, and all
remaining limit orders expire at the end of the step. Calling this mechanism a continuous double
auction would overstate the implemented time and persistence model.

## ODD: overview

### Purpose

The model is designed to separate common-response convergence in noninteractive replay from
endogenous price feedback in an interacting exchange. Its scientific output is a dose-response
curve over randomized AI capital shares, accompanied by market-quality and failure endpoints.

### Entities, state variables, and scales

| Entity | Implemented state | Current scale |
|---|---|---|
| Market replica | seed, step, timestamp, symbols, endogenous history | one isolated run |
| Agent | policy/model, cohort, cash, inventory, average cost | one decision per step |
| Order | agent, symbol, side, quantity, optional limit, arrival index | lifetime fixed to one step |
| Book | symbol-specific bids and asks with price-time priority | rebuilt each step |
| Trade | buyer, seller, price, quantity, per-side fee, tape sequence | one counterparty-linked record |
| Bar | endogenous OHLCV or zero-volume carried close | one per symbol and step |
| News | timestamped exogenous event | read from input bundle |

The time unit inherits the dataset timestamp cadence. This is a modeling convention and is not
yet calibrated to any real venue's message or auction clock.

### Process overview and scheduling

At a step, all agents observe the same public bar/news state plus their private portfolio. They
submit orders without observing other agents' current-step submissions. The exchange applies a
deterministic shuffle from `(replica seed, step)`, processes orders serially, skips self-matches,
fills crossing quantity at the resting price, records the counterparty-linked tape, snapshots
remaining depth, expires all remaining limits, and synthesizes an endogenous bar. A no-trade
symbol carries its prior close with zero volume.

The runner clips simultaneous orders against cash, inventory, position limits, and fee reserves
before submission. Unfilled buys cannot finance sells, and unfilled sells cannot finance buys.
The ledger rejects fills that would create negative cash, negative inventory, or a position above
the cap.

### Design concepts

- Common random numbers are used only where specified by a paired design.
- Arrival is randomized within a step but reproducible from the replica seed.
- Public feedback occurs through completed bars; agents do not observe the intra-step book.
- A trade creates equal buyer and seller quantities and charges each side separately.
- Background liquidity, fundamental demand, noise demand, and persistent orders are **not yet
  implemented**.
- Cancel/replace messages, latency, queue position across steps, dividends, borrowing, shorting,
  and exchange halts are **not modeled**.

### Initialization and input data

Input bars seed each symbol's observation history and reference price; events seed public news.
The data-bundle hash covers every input file and metadata artifact. Agent endowments, position
caps, fees, tick size, observation window, order lifetime, seed, and assigned AI share must be
present in the release manifest. The current exchange requires a positive initial inventory if
long-only agents are expected to supply the sell side.

## STRESS: experiment report contract

### Objectives and scenarios

The confirmatory objective is the prespecified simultaneous dose-response family across all six
AI-share levels. No threshold may be selected after seeing outcomes. Required stress dimensions
are arrival rule, initial endowment, tick size, fee, agent capital distribution, order-type mix,
book persistence, background-liquidity intensity, information regime, and replica seed.

### Data collection

A release must preserve reconstructable submissions, clipped orders, book states, cancellations
or expirations, fills, counterparty-linked trades, endogenous bars, portfolios, failures, model
usage, and costs. The current run writer preserves decisions, fills, and portfolios but does **not**
yet export submissions, book snapshots, expirations, or the exchange trade tape. That is a release
blocker, even though these objects exist in memory.

### Verification tests

The following invariants must pass property and interruption tests:

1. cash, inventory, and fees reconcile from the event stream;
2. each trade has one buyer and one different seller with equal quantity and price;
3. self-trades, negative inventory, negative cash, and over-cap positions are impossible;
4. simultaneous reservations remain valid under partial fills and gaps;
5. price-time priority and tick rounding are deterministic;
6. restart reproduces assignments and outcomes without duplicate model billing;
7. changing any input or exchange parameter changes the resolved hash; and
8. exchange analyses use endogenous bars and tape rather than the seeding dataset's future bars.

Implemented unit tests currently cover several conservation, self-trade, reservation, partial-fill,
and timestamp-alignment cases. They do not yet establish all eight release invariants for the
compiled H5 matrix.

### Validation targets

Before confirmatory execution, an outcome-blind calibration split must freeze plausible target
ranges or empirical reference distributions for:

- quoted and effective spread;
- depth by distance from the best quote;
- volume, turnover, and fill rate;
- return volatility, autocorrelation, and tail behavior;
- temporary and persistent price impact by order size;
- no-trade frequency and duration; and
- wealth, inventory, and liquidity concentration.

Validation is multivariate. Matching one stylized fact cannot compensate for degenerate depth,
near-zero volume, mechanically carried prices, or implausible fill rates. Target choice, tolerance,
calibration data, and failed targets must be reported rather than tuned away.

### Sensitivity, uncertainty, and stopping

Treat whole replicas as the independent units. Plot every replica and simultaneous uncertainty
bands over the complete dose-response. The blinded pilot may update replica counts from pooled
variance, completeness, throughput, and failure rates, but may not choose favorable endpoints,
AI-share thresholds, models, or simulator parameters from treatment effects. Provider failure,
parse failure, strict-grounding rejection, no-liquidity failure, and incomplete tape each receive
distinct terminal states.

## H5 release checklist

H5 remains disabled until all items are checked in a frozen commit:

- [ ] Persistent order lifetime and explicit cancel/expiry policy are implemented and tested.
- [ ] Seeded fundamental, noise, and background-liquidity agents are implemented and documented.
- [ ] Submissions, order events, book snapshots, expirations, fills, and tape are exported and
  reconstruct the same bars exactly.
- [ ] The compiled plan assigns all six AI shares to independent replicas with frozen blocking.
- [ ] Conservation, matching, leakage, restart, and hash-invalidating tests pass for every H5 cell.
- [ ] Calibration targets and tolerances are frozen on data disjoint from confirmatory replicas.
- [ ] Every mandatory market-quality target passes or the simulator is reported as invalid.
- [ ] Arrival, endowment, tick, fee, persistence, liquidity, order-type, and capital-share stress
  results are included without specification selection.
- [ ] `claims.json` labels all H5 claims `simulator_bounded` and links them to this report.

Until then, exchange runs are engineering diagnostics and cannot populate the manuscript.
