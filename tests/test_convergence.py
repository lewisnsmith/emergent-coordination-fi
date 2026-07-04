import numpy as np
import pandas as pd

from flock.analysis import convergence


def _decisions(actions_by_agent: dict[str, list[str]], cohort: str = "c") -> pd.DataFrame:
    rows = []
    for agent, actions in actions_by_agent.items():
        for step, action in enumerate(actions):
            rows.append(
                {
                    "agent_id": agent, "cohort": cohort, "step": step, "ts": f"t{step}",
                    "action": action, "parse_ok": True, "orders_clipped": [],
                }
            )
    return pd.DataFrame(rows)


def test_identical_agents_have_kappa_near_one():
    seq = ["buy", "sell", "hold", "buy", "sell", "buy", "hold", "sell"]
    d = _decisions({"a": seq, "b": seq})
    mat = convergence.action_matrix(d, ["a", "b"])
    assert convergence.pairwise_agreement(mat) == 1.0
    assert convergence.mean_pairwise_kappa(mat) == 1.0


def test_independent_agents_have_kappa_near_zero():
    rng = np.random.default_rng(0)
    acts = ["buy", "sell", "hold"]
    d = _decisions({f"a{i}": list(rng.choice(acts, 300)) for i in range(4)})
    mat = convergence.action_matrix(d, sorted(d["agent_id"].unique()))
    kappa = convergence.mean_pairwise_kappa(mat)
    assert abs(kappa) < 0.1


def test_degenerate_hold_only_agents_score_zero_not_one():
    d = _decisions({"a": ["hold"] * 10, "b": ["hold"] * 10})
    mat = convergence.action_matrix(d, ["a", "b"])
    assert convergence.mean_pairwise_kappa(mat) == 0.0


def test_portfolio_overlap_bounds():
    weights = {
        "a": pd.DataFrame({"X": [0.5, 0.5], "Y": [0.5, 0.5]}),
        "b": pd.DataFrame({"X": [0.5, 0.5], "Y": [0.5, 0.5]}),
        "c": pd.DataFrame({"X": [0.0, 0.0], "Y": [0.0, 0.0]}),
    }
    full = convergence.mean_portfolio_overlap({"a": weights["a"], "b": weights["b"]})
    none = convergence.mean_portfolio_overlap({"a": weights["a"], "c": weights["c"]})
    assert full == 1.0
    assert none == 0.0


def test_position_cosine_identical_is_one():
    w = pd.DataFrame({"X": [0.3, 0.4], "Y": [0.2, 0.1]})
    sim = convergence.mean_position_cosine({"a": w, "b": w.copy()})
    assert abs(sim - 1.0) < 1e-9
