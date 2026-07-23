from flock.core.config import ExperimentConfig, SweepConfig
from flock.experiments.grid import derive_cell, sweep_cells
from flock.experiments.runner import build_agents

BASE = ExperimentConfig(
    name="t",
    dataset="d",
    model_policy="mock_only",
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


def test_sweep_override_keeps_agent_ids_unique_across_llm_groups():
    cfg = ExperimentConfig(
        name="duplicate-groups",
        dataset="synthetic-equities-v1",
        model_policy="mock_only",
        cohorts=[
            {
                "name": "llm",
                "agents": [
                    {
                        "kind": "llm",
                        "model": "mock-momentum",
                        "persona": "neutral",
                        "count": 2,
                    },
                    {
                        "kind": "llm",
                        "model": "mock-momentum",
                        "persona": "neutral",
                        "count": 2,
                    },
                ],
            }
        ],
    )

    ids = [agent.agent_id for agent in build_agents(cfg, cache=None)]

    assert ids == [
        "llm-mock-momentum-neutral-0",
        "llm-mock-momentum-neutral-1",
        "llm-mock-momentum-neutral-2",
        "llm-mock-momentum-neutral-3",
    ]
