"""Baseline strategy implementations.

All baselines size orders as a fraction of equity and respect the same
position limits the runner enforces for LLM agents.
"""

from __future__ import annotations

import numpy as np

from flock.core.types import Decision, Observation, Order


def _closes(obs: Observation, symbol: str) -> np.ndarray:
    return np.array([b.close for b in obs.bars[symbol]])


class _Baseline:
    kind = "baseline"

    def __init__(self, agent_id: str, cohort: str, rng: np.random.Generator, params: dict):
        self.agent_id = agent_id
        self.cohort = cohort
        self.rng = rng
        self.params = params

    def describe(self) -> dict:
        return {"kind": self.kind, "params": {k: round(v, 6) for k, v in self.params.items()}}

    def _order_qty(self, obs: Observation, symbol: str, frac: float) -> float:
        price = obs.prices[symbol]
        if price <= 0:
            return 0.0
        return round(obs.portfolio.equity * frac / price, 4)

    def _held(self, obs: Observation, symbol: str) -> float:
        for p in obs.portfolio.positions:
            if p.symbol == symbol:
                return p.quantity
        return 0.0


class MomentumAgent(_Baseline):
    """Buy recent winners, sell recent losers (time-series momentum)."""

    kind = "momentum"

    def __init__(self, agent_id, cohort, rng, params=None):
        params = params or {}
        params.setdefault("lookback", float(rng.integers(5, 15)))
        params.setdefault("threshold", float(rng.uniform(0.005, 0.03)))
        params.setdefault("size_frac", float(rng.uniform(0.02, 0.08)))
        super().__init__(agent_id, cohort, rng, params)

    def decide(self, obs: Observation) -> Decision:
        orders = []
        lb = int(self.params["lookback"])
        for s in obs.symbols:
            closes = _closes(obs, s)
            if len(closes) <= lb:
                continue
            ret = closes[-1] / closes[-1 - lb] - 1.0
            qty = self._order_qty(obs, s, self.params["size_frac"])
            if ret > self.params["threshold"] and qty > 0:
                orders.append(Order(s, "buy", qty))
            elif ret < -self.params["threshold"] and self._held(obs, s) > 0:
                orders.append(Order(s, "sell", min(qty, self._held(obs, s))))
        return Decision(self.agent_id, obs.step, tuple(orders), rationale="momentum rule")


class MeanReversionAgent(_Baseline):
    """Fade deviations from a moving average."""

    kind = "mean_reversion"

    def __init__(self, agent_id, cohort, rng, params=None):
        params = params or {}
        params.setdefault("window", float(rng.integers(8, 20)))
        params.setdefault("z_entry", float(rng.uniform(1.0, 2.0)))
        params.setdefault("size_frac", float(rng.uniform(0.02, 0.08)))
        super().__init__(agent_id, cohort, rng, params)

    def decide(self, obs: Observation) -> Decision:
        orders = []
        w = int(self.params["window"])
        for s in obs.symbols:
            closes = _closes(obs, s)
            if len(closes) < w:
                continue
            window = closes[-w:]
            mu, sd = window.mean(), window.std()
            if sd == 0:
                continue
            z = (closes[-1] - mu) / sd
            qty = self._order_qty(obs, s, self.params["size_frac"])
            if z < -self.params["z_entry"] and qty > 0:
                orders.append(Order(s, "buy", qty))
            elif z > self.params["z_entry"] and self._held(obs, s) > 0:
                orders.append(Order(s, "sell", min(qty, self._held(obs, s))))
        return Decision(self.agent_id, obs.step, tuple(orders), rationale="mean-reversion rule")


class MarketMakerAgent(_Baseline):
    """Quote both sides around the reference price with an inventory tilt."""

    kind = "market_maker"

    def __init__(self, agent_id, cohort, rng, params=None):
        params = params or {}
        params.setdefault("half_spread_bps", float(rng.uniform(10, 50)))
        params.setdefault("size_frac", float(rng.uniform(0.01, 0.04)))
        params.setdefault("max_inventory_frac", 0.15)
        super().__init__(agent_id, cohort, rng, params)

    def decide(self, obs: Observation) -> Decision:
        orders = []
        for s in obs.symbols:
            price = obs.prices[s]
            half = price * self.params["half_spread_bps"] / 1e4
            qty = self._order_qty(obs, s, self.params["size_frac"])
            if qty <= 0:
                continue
            inv_value = self._held(obs, s) * price
            max_inv = obs.portfolio.equity * self.params["max_inventory_frac"]
            if inv_value < max_inv:
                orders.append(Order(s, "buy", qty, limit_price=round(price - half, 4)))
            if self._held(obs, s) > 0:
                sell_qty = min(qty, self._held(obs, s))
                orders.append(Order(s, "sell", sell_qty, limit_price=round(price + half, 4)))
        return Decision(self.agent_id, obs.step, tuple(orders), rationale="market-making quotes")


class BuyHoldAgent(_Baseline):
    """Deploy capital equally across symbols early, then hold."""

    kind = "buy_hold"

    def __init__(self, agent_id, cohort, rng, params=None):
        params = params or {}
        params.setdefault("deploy_frac", float(rng.uniform(0.7, 0.95)))
        super().__init__(agent_id, cohort, rng, params)
        self._deployed = False

    def decide(self, obs: Observation) -> Decision:
        if self._deployed:
            return Decision(self.agent_id, obs.step, (), rationale="holding")
        self._deployed = True
        per_symbol = self.params["deploy_frac"] / len(obs.symbols)
        orders = []
        for s in obs.symbols:
            qty = self._order_qty(obs, s, per_symbol)
            if qty > 0:
                orders.append(Order(s, "buy", qty))
        return Decision(self.agent_id, obs.step, tuple(orders), rationale="initial deployment")


class RandomAgent(_Baseline):
    """Zero-intelligence trader (Gode & Sunder): chance floor for every metric."""

    kind = "random"

    def __init__(self, agent_id, cohort, rng, params=None):
        params = params or {}
        params.setdefault("trade_prob", float(rng.uniform(0.2, 0.6)))
        params.setdefault("size_frac", float(rng.uniform(0.01, 0.06)))
        super().__init__(agent_id, cohort, rng, params)

    def decide(self, obs: Observation) -> Decision:
        orders = []
        for s in obs.symbols:
            if self.rng.random() > self.params["trade_prob"]:
                continue
            qty = self._order_qty(obs, s, self.params["size_frac"])
            if self.rng.random() < 0.5 and qty > 0:
                orders.append(Order(s, "buy", qty))
            elif self._held(obs, s) > 0:
                orders.append(Order(s, "sell", min(qty, self._held(obs, s))))
        return Decision(self.agent_id, obs.step, tuple(orders), rationale="random")


_KINDS = {
    "momentum": MomentumAgent,
    "mean_reversion": MeanReversionAgent,
    "market_maker": MarketMakerAgent,
    "buy_hold": BuyHoldAgent,
    "random": RandomAgent,
}


def make_baseline(
    kind: str, agent_id: str, cohort: str, rng: np.random.Generator, params: dict | None = None
):
    cls = _KINDS[kind]
    return cls(agent_id, cohort, rng, dict(params) if params else None)
