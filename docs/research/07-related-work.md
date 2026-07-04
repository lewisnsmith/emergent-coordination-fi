# 07 — Related Work

Working bibliography grounding the design. (Verify citations against originals before
submission; this file is a map, not a bibliography of record.)

## Herding measurement (our H2/H5 statistics come from here)

- **Lakonishok, Shleifer & Vishny (1992)**, "The impact of institutional trading on stock
  prices," *JFE*. The LSV herding statistic: excess one-sidedness of trades vs binomial null.
  We apply it symmetrically to LLM cohorts and 13F panels.
- **Sias (2004)**, "Institutional herding," *RFS*. Serial cross-sectional correlation of
  institutional demand; decomposition into own-following and crowd-following.
- **Wermers (1999)**, mutual-fund herding; grounds activity filters and interpretation.

## Algorithmic coordination & collusion

- **Calvano, Calzolari, Denicolò & Pastorello (2020)**, "Artificial intelligence, algorithmic
  pricing, and collusion," *AER*. Q-learning pricers converge to supra-competitive prices
  without communication — the canonical tacit-coordination result our exp-012 mirrors for
  market-making.
- **Klein (2021)** and follow-ups on reinforcement-learning collusion robustness.
- **SEC/CFTC and FSB reports on AI in finance (2023–2025)** — policy framing for herding via
  shared models ("model monoculture", third-party AI concentration risk).

## Crowding & systemic risk

- **Khandani & Lo (2011)**, "What happened to the quants in August 2007?" Evidence that crowded
  quant strategies unwound together — the historical template for convergence risk.
- **Stein (2009)**, "Presidential address: Sophisticated investors and market efficiency" —
  crowding and leverage externalities among sophisticated traders.
- **Brunnermeier & Pedersen (2009)**, funding/market liquidity spirals — mechanism for
  Phase-2 cascade interpretation.

## LLM agents in markets and simulations

- **LLM agent-based market simulation** (growing literature, 2023–2025): multi-agent LLM
  traders in simulated markets exhibiting bubbles, herding, and prompt-sensitive behavior.
  Our contribution differs in (a) the *dispersion contrast* against matched algorithmic and
  empirical baselines, (b) pre-registered inference, (c) cross-provider design.
- **Homogenization / algorithmic monoculture**: Kleinberg & Raghavan (2021) on monoculture in
  algorithmic decision-making; Bommasani et al. (2022) "Picking on the same person" — outcome
  homogenization from shared foundation models. Our work is the trading instantiation.
- **LLM behavioral finance**: studies of LLM risk preferences, probability calibration, and
  economic rationality (e.g., Horton 2023, "LLMs as simulated economic agents") — motivates
  persona axis and demographic instructions.

## Experimental market microstructure

- **Smith (1962)** and the experimental-economics tradition of induced-value double auctions —
  our Phase-2 exchange follows the continuous double auction convention.
- **Gode & Sunder (1993)**, zero-intelligence traders: market institutions can produce
  efficiency without agent rationality — the reason our null cohort exists.

## Positioning

The novel claim is comparative and quantitative: *given identical information and matched
constraints, LLM cohorts exhibit measurably lower strategy dispersion than the algorithmic and
human infrastructure they may replace, and this convergence has price-level consequences in
shared markets.* No prior work (to our knowledge) makes the dispersion contrast with matched
baselines, pre-registered statistics, and cross-provider cohorts.
