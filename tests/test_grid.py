from flock.core.config import ExperimentConfig, SweepConfig
from flock.experiments.grid import derive_cell, sweep_cells

BASE = ExperimentConfig(
    name="t",
    dataset="d",
    cohorts=[
        {
            "name": "llm",
            "agents": [{"kind": "llm", "model": "m0", "persona": "neutral", "count": 2}],
        },
        {"name": "baseline", "agents": [{"kind": "momentum", "count": 2}]},
    ],
)


def test_derive_cell_overrides_only_llm_groups():
    cfg = derive_cell(BASE, model="m1", persona="retail-saver", temperature=0.1, seed=9)
    llm_group = cfg.cohorts[0].agents[0]
    assert llm_group.model == "m1"
    assert llm_group.persona == "retail-saver"
    assert llm_group.temperature == 0.1
    assert cfg.seed == 9
    assert cfg.cohorts[1].agents[0].kind == "momentum"
    # base untouched
    assert BASE.cohorts[0].agents[0].model == "m0"


def test_sweep_cells_cardinality_and_unique_hashes():
    sweep = SweepConfig(
        name="s", base="x.yaml", models=["a", "b"], seeds=[1, 2, 3]
    )
    cells = sweep_cells(sweep, BASE)
    assert len(cells) == 6
    hashes = {c.config_hash() for c in cells}
    assert len(hashes) == 6
