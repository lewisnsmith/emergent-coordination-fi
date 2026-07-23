from flock.agents.prompts import resolve_prompt
from flock.core.types import Bar, NewsEvent, Observation, PortfolioView
from flock.experiments.treatments import apply_information_policy


def _observation() -> Observation:
    bar = Bar("t0", "X", 10, 11, 9, 10, 100)
    return Observation(
        step=0,
        ts="t0",
        symbols=("X",),
        bars={"X": (bar,)},
        prices={"X": 10},
        news=tuple(
            NewsEvent("t0", "X", f"evidence item {index}", 0) for index in range(20)
        ),
        portfolio=PortfolioView(100, (), 100),
    )


def test_information_partitions_are_disjoint_and_complete():
    obs = _observation()
    a = apply_information_policy(obs, "news-partition-a")
    b = apply_information_policy(obs, "news-partition-b")
    assert set(a.news).isdisjoint(b.news)
    assert set(a.news) | set(b.news) == set(obs.news)


def test_pressure_prompt_preserves_simulation_safety_header():
    prompt = resolve_prompt("fictional_life_or_death__u1e1f1")
    assert "FICTIONAL RESEARCH SIMULATION" in prompt
    assert "critical medical care" in prompt
    assert "must be made immediately" in prompt
    assert "never violate evidence" in prompt


def test_unknown_prompt_and_information_policy_fail_closed():
    try:
        resolve_prompt("does-not-exist")
    except KeyError:
        pass
    else:
        raise AssertionError("unknown prompt should fail")
    try:
        apply_information_policy(_observation(), "invented")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown information policy should fail")
