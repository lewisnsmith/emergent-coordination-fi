from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]
EXPECTED_BRANCHES = {
    "feat/alpha-oos-evaluation",
    "feat/h1-h3-h4-h12-replay-convergence",
    "feat/h2-h2b-h6-investor-delegation",
    "feat/h2b-h5-shared-exchange",
    "feat/h7-adoption-forecast",
    "feat/h8-exp017-causal-convergence",
    "feat/h8-h12-pressure-attribution",
    "feat/h8-h13-local-fidelity-quantization",
    "feat/h9-h10-h11-market-signatures",
}
EXPECTED_PROGRAM_EXPERIMENTS = {f"exp-{index:03d}" for index in range(27)}


def test_program_manifest_names_every_family() -> None:
    manifest = yaml.safe_load((ROOT / "research-program.yaml").read_text())

    assert manifest["publication_base"] == "3002008b291dcd736b90237cccd1e5fd9f4ba0e4"
    assert {study["branch"] for study in manifest["study_families"]} == EXPECTED_BRANCHES
    assert all(
        study["status"] in {"planned", "blocked_external"}
        for study in manifest["study_families"]
    )
    assigned = [
        experiment
        for study in manifest["study_families"]
        for experiment in study["experiments"]
        if experiment.startswith("exp-")
    ]
    assert len(assigned) == len(set(assigned))
    assert set(assigned) == EXPECTED_PROGRAM_EXPERIMENTS
