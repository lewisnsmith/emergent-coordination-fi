# 07 — Related Work

Working claim map for the design. The dated, reproducible search protocol and screening decisions
are in [`literature-search-log.yaml`](literature-search-log.yaml); `paper/references.bib` is the
bibliographic source of record. Refresh both before preregistration and submission.

## Novelty boundary

The generic novelty territory is occupied. Prior work already reports concentrated cross-model
investment recommendations, reduced LLM-trader dispersion relative to humans, common errors in
mixed model markets, prompt-sensitive market effects, and LLM trading in price-forming order-book
simulations. This project must not claim to be the first demonstration that LLM financial agents
converge, herd, or affect simulated markets.

The defensible proposed contribution is narrower: a matched
`technology (LLM/classical) × ecology (homogeneous/heterogeneous)` benchmark, family-weighted
estimands, a design intended to decompose model/profile/harness/information/wording components,
and inference over independent trajectories or nonoverlapping windows. H5 is a separate,
simulator-bounded consequence experiment; H2 is a conditional descriptive anchor.

## Herding measurement (our H2/H5 statistics come from here)

- **Lakonishok, Shleifer & Vishny (1992)**, "The impact of institutional trading on stock
  prices," *JFE*. The LSV herding statistic: excess one-sidedness of trades vs binomial null.
  We apply it symmetrically to LLM cohorts and 13F panels.
- **Sias (2004)**, "Institutional herding," *RFS*. Serial cross-sectional correlation of
  institutional demand; decomposition into own-following and crowd-following.
- **Wermers (1999)**, mutual-fund herding; grounds activity filters and interpretation.
- **Wylie (2005)** and **Frey, Herbst & Walter (2014)** show that traditional LSV estimates can
  be biased by the data structure and activity process. H2 therefore requires period-specific
  expected-buy fractions, quarter-to-quarter holdings changes, activity reporting, and structural
  sensitivity analysis rather than treating 13F overlap as a universal human benchmark.

## Algorithmic coordination and collusion

- **Calvano, Calzolari, Denicolò & Pastorello (2020)**, “Artificial intelligence, algorithmic
  pricing, and collusion,” *AER*. Q-learning pricers converge to supra-competitive prices
  without communication. This is a strategic pricing result, not authority to call correlated
  Phase-1 decisions collusion.
- **Klein (2021)** studies sequential Q-learning pricing. DOI
  `10.1111/1756-2171.12383` is the article identifier, not a correction notice.
- **Colliard, Foucault & Lovo (2026)** show that Q-learning market makers can fail to learn
  competitive pricing because experimentation is limited and profit feedback is noisy. This is a
  direct benchmark for H5 competitive/null/deviation tests.

## Crowding & systemic risk

- **Khandani & Lo (2011)**, "What happened to the quants in August 2007?" Evidence that crowded
  quant strategies unwound together — the historical template for convergence risk.
- **Stein (2009)**, "Presidential address: Sophisticated investors and market efficiency" —
  crowding and leverage externalities among sophisticated traders.
- **Brunnermeier & Pedersen (2009)**, funding/market liquidity spirals — mechanism for
  Phase-2 cascade interpretation.

## Direct LLM-finance precedents

- **Henning et al. (2025),
  [“LLM Agents Do Not Replicate Human Market Traders”](https://arxiv.org/abs/2502.15800).** Six
  API-accessed LLMs trade in homogeneous and mixed experimental markets alongside a human-market
  comparison. The paper directly reports lower strategy and portfolio-value dispersion among LLM
  traders, occupying any broad “LLMs are more homogeneous than humans” claim.
- **Joglar (2026),
  [“Converging Echoes”](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6852518).** Five LLMs
  generate investment recommendations in a crossed client-profile design. Inter-model portfolio
  overlap exceeds a size-matched random benchmark and capital concentrates in a small issuer set.
  The distinction here must be sequential replay and matched classical ecologies, not discovery of
  recommendation convergence.
- **Saxena et al. (2026),
  [“Machine Spirits”](https://arxiv.org/abs/2604.18602).** Fifteen LLMs/providers trade in
  homogeneous and heterogeneous experimental markets. Common errors and mixed model ecologies can
  produce instability, directly motivating rather than replacing the proposed ecology factor.
- **Ouyang and Sui (2026),
  [“Dissecting AI Trading”](https://arxiv.org/abs/2604.18373).** Autonomous LLM traders operate in
  an auction, and targeted prompt interventions alter behavioral mechanisms and bubble magnitude.
  This occupies generic prompt-to-market-effect novelty; MPHIQ's balanced component decomposition
  remains the differentiator.
- **Lopez-Lira (2025),
  [“Can Large Language Models Trade?”](https://arxiv.org/abs/2504.10789).** LLM agents trade with
  a persistent order book, market and limit orders, partial fills, heterogeneous strategies and
  information, and endogenous liquidity and price behavior. Exchange infrastructure and simulated
  price effects are therefore enabling methods, not firsts.
- **Ma et al. (2025),
  [“Agent Trading Arena”](https://aclanthology.org/2025.findings-emnlp.294/).** A competitive
  zero-sum stock arena studies numerical and visual reasoning under endogenous agent interaction.
  It further occupies generic multi-agent trading-arena novelty.
- **“Agentic Trading: When LLM Agents Meet Financial Markets” (2026),
  [systematic review](https://arxiv.org/abs/2605.19337).** The review maps 77 studies and identifies
  recurring weaknesses in temporal splits, transaction costs, survivorship controls, and
  reproducibility. Its evidence map should be updated at preregistration and submission, and its
  identified weaknesses should be treated as minimum design gates.

## Adjacent foundations

- **Homogenization / algorithmic monoculture**: Kleinberg & Raghavan (2021) on monoculture in
  algorithmic decision-making; Bommasani et al. (2022), “Picking on the Same Person,” on outcome
  homogenization from shared algorithmic components; and Gorecki & Hardt (2025) on empirical
  monoculture versus model multiplicity across 50 language models. The proposed study applies
  these mechanisms to a matched trading benchmark; it does not originate them.
- **LLM behavioral finance**: Horton, Filippas & Manning (2023, revised 2026), “LLMs as simulated
  economic agents,” motivates the persona axis while also reinforcing that simulated-agent
  behavior is not evidence about humans without external validation.

## Experimental market microstructure

- **Smith (1962)** and the experimental-economics tradition of induced-value double auctions
  motivate the market-design benchmark. The current H5 simulator is not yet a validated continuous
  double auction and remains disabled until its explicit gates pass.
- **Gode & Sunder (1993)**, zero-intelligence traders: market institutions can produce
  efficiency without agent rationality — the reason our null cohort exists.

## Terminology and positioning contract

Phase-1 agents cannot coordinate because they neither interact nor observe one another. Agreement
there is **common-response convergence**, **correlated decisions**, or **outcome homogenization**.
LSV, Sias, one-sided cascades, or pairwise agreement can establish statistical herding or
synchronization under their assumptions, but not strategic collusion. “Tacit collusion” is
reserved for evidence of strategic response, profitable joint deviation, punishment, or a
comparable supra-competitive mechanism.

The proposed study should be positioned as a replication and extension: reproduce static/advisory
convergence and reduced dispersion in bridge cells, then ask *which shared components cause the
effect, whether it survives a fair classical comparison, and how ecology changes it*. It must not
promise that LLM cohorts are more convergent than human or institutional infrastructure unless the
H2 harmonization gate passes, and it must not carry simulator-bounded H5 causality into real
markets.
