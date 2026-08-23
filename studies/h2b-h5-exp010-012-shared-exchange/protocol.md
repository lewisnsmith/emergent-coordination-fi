# H2b and H5 shared exchange

## Question

Inside a controlled synthetic exchange, how do AI delegation share and correlated behavior change
market impact and microstructure?

## Design

Exp-010 calibrates known mock and random cohorts and must reconcile every order, fill, inventory,
cash movement, and arrival. Exp-011 runs all capital-share conditions within independently
initialized replica blocks using common shocks, fixed total capital, and matched background
liquidity. Exp-012 adds paired AI/no-AI and AI-market-maker microstructure treatments.

## Estimands, units, and controls

Estimate the capital-share dose response in impact, volatility, liquidity, convergence breadth,
spreads, herding, and cascades, plus a threshold distribution carrying simultaneous uncertainty and
no-threshold mass. Independent units are market-replica blocks. Controls include zero-AI markets,
random and placebo cohorts, matched volume, fixed exogenous liquidity, fixed capital, common random
numbers, and arrival-order perturbations.

## Failure rules and limits

Calibration failure stops exp-011/012. Book-reconstruction errors, capital drift, dependent
replicas, or operating outside the frozen domain blocks a verdict. Results are synthetic total
effects, not evidence about current adoption, exposed capital, coordination, or real markets.

## Execution sequence

1. Declare the operating domain, invariants, stress envelope, and failure conditions.
2. Implement and pass exp-010 calibration and full reconstruction.
3. Freeze books, liquidity, share grid, shocks, units, outcomes, and threshold rules.
4. Gate model outputs, compute, spending, and release rights.
5. Run exp-011 and exp-012 with common replica blocks and reconstruct every book.
6. Release null, adverse, and no-threshold outcomes under the same synthetic-only contract.
