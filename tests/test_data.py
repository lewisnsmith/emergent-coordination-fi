import numpy as np

from flock.data import schemas, synthetic
from flock.data.registry import Registry


def test_synthetic_is_deterministic():
    b1, e1, m1 = synthetic.generate(n_symbols=2, n_steps=50, seed=9)
    b2, e2, m2 = synthetic.generate(n_symbols=2, n_steps=50, seed=9)
    assert b1.equals(b2)
    assert e1.equals(e2)
    b3, _, _ = synthetic.generate(n_symbols=2, n_steps=50, seed=10)
    assert not b1.equals(b3)


def test_synthetic_prices_positive(synthetic_data):
    bars, _, _ = synthetic_data
    assert (bars[["open", "high", "low", "close"]] > 0).all().all()
    assert (bars["high"] >= bars["close"]).all()
    assert (bars["low"] <= bars["close"]).all()


def test_dataset_roundtrip_and_registry(tmp_path, synthetic_data):
    bars, events, meta = synthetic_data
    ds_dir = tmp_path / "ds" / "syn-test"
    rows = schemas.write_dataset(ds_dir, bars, events, meta)
    assert rows == len(bars)
    assert schemas.read_bars(ds_dir).equals(
        bars[schemas.BAR_COLUMNS].sort_values(["ts", "symbol"]).reset_index(drop=True)
    )
    reg = Registry(root=tmp_path / "ds")
    entry = reg.register("syn-test", "synthetic", ds_dir, {"seed": 7})
    assert reg.get("syn-test").sha256 == entry.sha256
    entry2 = reg.register("syn-test", "synthetic", ds_dir, {"seed": 7})
    assert entry2.version == 2
    assert reg.get("syn-test").version == 2


def test_registry_missing_dataset_message(tmp_path):
    reg = Registry(root=tmp_path)
    try:
        reg.get("nope")
        raise AssertionError("expected KeyError")
    except KeyError as e:
        assert "flock data build" in str(e)


def test_baseline_hyperparams_vary_across_instances(rng):
    from flock.agents.baselines import make_baseline

    agents = [
        make_baseline("momentum", f"m{i}", "baseline", np.random.default_rng(i), None)
        for i in range(5)
    ]
    lookbacks = {a.params["lookback"] for a in agents}
    assert len(lookbacks) > 1  # heterogeneous cohort
