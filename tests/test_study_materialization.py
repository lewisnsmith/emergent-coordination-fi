import hashlib
import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from flock.cli import app
from flock.core.config import ExperimentConfig
from flock.core.study import StudySpec
from flock.data.registry import dataset_bundle_files, dataset_bundle_hash
from flock.experiments.materialize import ExecutionResolution, materialize_study
from flock.experiments.runner import build_agents
from flock.experiments.study import compile_study, compile_study_file, write_study_plan

PAPER_CORE = Path("configs/studies/paper-core.yaml")


def test_materializes_every_frozen_cell_with_exact_lineage_and_counts():
    plan = compile_study_file(PAPER_CORE)
    first = materialize_study(plan)
    second = materialize_study(plan)

    assert first.materialization_hash == second.materialization_hash
    assert len(first.assignments) == first.exact_runs == plan.exact_runs == 197
    assert first.exact_steps == plan.exact_steps
    assert first.exact_agent_steps == plan.exact_agent_steps
    assert first.exact_calls == plan.exact_calls
    assert first.executable_runs == 0
    assert len({item.assignment_id for item in first.assignments}) == 197

    mphiq = [item for item in first.assignments if item.stage_id == "mphiq-factorial"]
    assert len(mphiq) == 128
    assert {item.cell.mphiq_code for item in mphiq} == {f"{value:05b}" for value in range(32)}
    assert {item.trajectory_id for item in mphiq} == {
        item.trajectory_id
        for item in first.assignments
        if item.stage_id == "confirmatory-replay"
    }
    assert {item.seed for item in mphiq} == {3101}
    assert all(item.cell.mphiq_pairs for item in mphiq)

    h5 = [item for item in first.assignments if item.stage_id == "h5-capital-share"]
    assert len(h5) == 48
    assert len({item.market_replica_id for item in h5}) == 8
    shares = [item.cell.capital_share for item in h5]
    assert all(share is not None for share in shares)
    assert {share.ai_share_bps for share in shares if share is not None} == {
        0,
        1000,
        2500,
        5000,
        7500,
        10000,
    }
    with pytest.raises(ValueError, match="197 of 197 assignments are not executable"):
        materialize_study(plan, require_executable=True)


def _mock_study() -> StudySpec:
    return StudySpec.model_validate(
        {
            "schema_version": 1,
            "study_id": "mock-materialization-v1",
            "title": "Offline mock materialization contract",
            "max_stages": 1,
            "dependence_clusters": [
                {
                    "cluster_id": "mock-trajectory-cluster",
                    "independent_unit": "trajectory",
                    "description": "One independently seeded offline mock trajectory.",
                }
            ],
            "trajectories": [
                {
                    "trajectory_id": "mock-trajectory-v1",
                    "window_id": "mock-window-v1",
                    "source": "synthetic",
                    "market_id": "mock-market-v1",
                    "start_date": "2026-01-01",
                    "end_date": "2026-01-02",
                    "dependence_cluster_id": "mock-trajectory-cluster",
                }
            ],
            "cohorts": [
                {
                    "cohort_id": "mock-llm-homogeneous",
                    "technology": "llm",
                    "ecology": "homogeneous",
                    "allocations": [
                        {
                            "model_id": "mock-momentum-exact",
                            "revision": "mock-v1",
                            "provider": "mock",
                            "family": "mock-family",
                            "pricing_key": "gpt-5.6-sol",
                            "count": 2,
                        }
                    ],
                }
            ],
            "held_out_families": ["mock-family"],
            "estimands": [
                {
                    "estimand_id": "h4-mock-materialization",
                    "hypothesis_id": "H4",
                    "outcome": "Mock action agreement.",
                    "contrast": "Deterministic offline mock contrast.",
                    "independent_unit": "One synthetic trajectory.",
                    "estimator": "Descriptive mock-only estimator.",
                }
            ],
            "required_outputs": [
                {
                    "output_id": "mock-assignment-output",
                    "path": "results/mock/assignments.json",
                    "format": "json",
                    "estimand_ids": ["h4-mock-materialization"],
                }
            ],
            "stages": [
                {
                    "stage_id": "mock-replay-stage",
                    "order": 1,
                    "authorization_stage": "canary",
                    "design": "replay",
                    "trajectory_ids": ["mock-trajectory-v1"],
                    "cohort_ids": ["mock-llm-homogeneous"],
                    "seeds": [77],
                    "steps_per_run": 2,
                    "calls_per_llm_agent_step": 1,
                    "estimand_ids": ["h4-mock-materialization"],
                    "output_ids": ["mock-assignment-output"],
                    "expected_counts": {
                        "runs": 1,
                        "steps": 2,
                        "agents_per_run": 2,
                        "agent_steps": 4,
                        "calls": 4,
                    },
                    "planned_cost_usd": 0.0,
                    "budget_cap": {"max_calls": 4, "max_cost_usd": 1.0},
                }
            ],
            "budget_cap": {"max_calls": 4, "max_cost_usd": 1.0},
        }
    )


def _write_mock_runtime(root: Path) -> Path:
    (root / "configs/models.yaml").parent.mkdir(parents=True)
    (root / "configs/models.yaml").write_text(
        yaml.safe_dump(
            {
                "mock-momentum-key": {
                    "provider": "mock",
                    "model_id": "mock-momentum-exact",
                    "deployment": "mock",
                    "family": "mock-family",
                    "pricing_key": "gpt-5.6-sol",
                    "behavior": "momentum",
                    "verified_on": "mock-v1",
                },
                "mock-contrarian-key": {
                    "provider": "mock",
                    "model_id": "mock-contrarian-exact",
                    "deployment": "mock",
                    "family": "mock-family-b",
                    "pricing_key": "gpt-5.6-sol",
                    "behavior": "contrarian",
                    "verified_on": "mock-v1",
                },
            }
        )
    )
    personas = root / "configs/personas"
    personas.mkdir(parents=True)
    (personas / "neutral.yaml").write_text(
        "name: neutral\nsystem_prompt: Trade only from the supplied observation.\n"
    )
    (personas / "neutral-alt.yaml").write_text(
        "name: neutral-alt\nsystem_prompt: Follow the supplied fictional mandate.\n"
    )
    prompts = root / "configs/prompts"
    prompts.mkdir(parents=True)
    (prompts / "catalog.yaml").write_text(
        yaml.safe_dump(
            {
                "semantic_paraphrases": [
                    {
                        "id": f"mock-paraphrase-{index}",
                        "semantic_group": "mock-neutral-group",
                        "text": f"Use only supplied evidence; variant {index}.",
                    }
                    for index in range(4)
                ]
            }
        )
    )
    dataset = root / "datasets/mock-dataset-v1"
    dataset.mkdir(parents=True)
    (dataset / "payload.txt").write_text("deterministic mock payload\n")
    manifest = [
        {
            "name": "mock-dataset-v1",
            "version": 1,
            "path": "datasets/mock-dataset-v1",
            "sha256": dataset_bundle_hash(dataset),
            "rows": 1,
            "source": "synthetic",
            "created_at": "2026-07-17T00:00:00+00:00",
            "params": {"seed": 77},
            "files": dataset_bundle_files(dataset),
        }
    ]
    (root / "datasets/manifests.json").write_text(json.dumps(manifest))
    return root / "configs/models.yaml"


def _mock_mphiq_study() -> StudySpec:
    raw = _mock_study().model_dump(mode="json")
    raw["study_id"] = "mock-mphiq-materialization-v1"
    raw["title"] = "Offline mock MPHIQ materialization contract"
    raw["cohorts"] = [
        {
            "cohort_id": "mock-llm-heterogeneous",
            "technology": "llm",
            "ecology": "heterogeneous",
            "allocations": [
                {
                    "model_id": "mock-momentum-exact",
                    "revision": "mock-v1",
                    "provider": "mock",
                    "family": "mock-family",
                    "pricing_key": "gpt-5.6-sol",
                    "count": 4,
                },
                {
                    "model_id": "mock-contrarian-exact",
                    "revision": "mock-v1",
                    "provider": "mock",
                    "family": "mock-family-b",
                    "pricing_key": "gpt-5.6-sol",
                    "count": 4,
                },
            ],
        }
    ]
    raw["mphiq_pairs"] = [
        {
            "pair_id": f"mock-edge-{factor.lower()}",
            "factor": factor,
            "different_code": "00000",
            "same_code": "00000"[:index] + "1" + "00000"[index + 1 :],
            "assignment_seed": 9000 + index,
        }
        for index, factor in enumerate("MPHIQ")
    ]
    raw["stages"] = [
        {
            "stage_id": "mock-mphiq-stage",
            "order": 1,
            "authorization_stage": "canary",
            "design": "mphiq",
            "trajectory_ids": ["mock-trajectory-v1"],
            "cohort_ids": ["mock-llm-heterogeneous"],
            "seeds": [77, 78],
            "steps_per_run": 1,
            "calls_per_llm_agent_step": 1,
            "mphiq_pair_ids": [f"mock-edge-{factor.lower()}" for factor in "MPHIQ"],
            "estimand_ids": ["h4-mock-materialization"],
            "output_ids": ["mock-assignment-output"],
            "expected_counts": {
                "runs": 12,
                "steps": 12,
                "agents_per_run": 8,
                "agent_steps": 96,
                "calls": 96,
            },
            "planned_cost_usd": 0.0,
            "budget_cap": {"max_calls": 96, "max_cost_usd": 1.0},
        }
    ]
    raw["budget_cap"] = {"max_calls": 96, "max_cost_usd": 1.0}
    return StudySpec.model_validate(raw)


def _mock_mphiq_resolution() -> ExecutionResolution:
    return ExecutionResolution.model_validate(
        {
            "schema_version": 1,
            "trajectory_datasets": {"mock-trajectory-v1": "mock-dataset-v1"},
            "model_registry_keys": {
                "mock-momentum-exact": "mock-momentum-key",
                "mock-contrarian-exact": "mock-contrarian-key",
            },
            "stage_defaults": {
                "mock-mphiq-stage": {
                    "market": {"kind": "replay", "fee_bps": 5.0, "slippage_bps": 2.0},
                    "observation_window": 20,
                    "initial_cash": 100000.0,
                    "initial_position_per_symbol": 0.0,
                    "max_position_per_symbol": 1000.0,
                    "grounding_mode": "audit",
                }
            },
            "mphiq_levels": {
                "mock-mphiq-stage": {
                    "persona_ids": ["neutral", "neutral-alt"],
                    "harness_presets": [
                        {
                            "level_id": f"mock-harness-{index}",
                            "temperature": index / 10,
                            "memory": bool(index % 2),
                            "harness_id": f"runtime-harness-{index}",
                        }
                        for index in range(4)
                    ],
                    "information_policies": [
                        "shared-all",
                        "no-news",
                        "news-partition-a",
                        "news-partition-b",
                    ],
                    "prompt_ids": [f"mock-paraphrase-{index}" for index in range(4)],
                    "prompt_semantic_group": "mock-neutral-group",
                }
            },
        }
    )


def _refresh_treatment_digest(treatment: dict) -> None:
    payload = {key: value for key, value in treatment.items() if key != "assignment_digest"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    treatment["assignment_digest"] = hashlib.sha256(canonical.encode()).hexdigest()


def test_explicit_resolution_emits_an_executable_offline_mock_config(tmp_path):
    plan = compile_study(_mock_study())
    models_path = _write_mock_runtime(tmp_path)
    resolution = ExecutionResolution.model_validate(
        {
            "schema_version": 1,
            "trajectory_datasets": {"mock-trajectory-v1": "mock-dataset-v1"},
            "model_registry_keys": {"mock-momentum-exact": "mock-momentum-key"},
            "stage_defaults": {
                "mock-replay-stage": {
                    "market": {"kind": "replay", "fee_bps": 5.0, "slippage_bps": 2.0},
                    "observation_window": 20,
                    "initial_cash": 100000.0,
                    "initial_position_per_symbol": 0.0,
                    "max_position_per_symbol": 1000.0,
                    "persona_id": "neutral",
                    "prompt_id": "task-neutral-v1",
                    "grounding_mode": "audit",
                }
            },
        }
    )

    result = materialize_study(
        plan,
        resolution,
        root=tmp_path,
        models_path=models_path,
        require_executable=True,
    )

    assert result.executable_runs == 1
    assignment = result.assignments[0]
    assert assignment.execution_blockers == ()
    config = ExperimentConfig.model_validate(assignment.execution_config)
    assert config.model_policy == "mock_only"
    assert config.trajectory_id == "mock-trajectory-v1"
    assert config.dependence_cluster == "mock-trajectory-cluster"
    assert config.seed == 77
    assert config.steps == 2
    assert config.cohorts[0].agents[0].model == "mock-momentum-key"


def test_mphiq_resolution_emits_balanced_per_agent_executable_treatments(tmp_path, monkeypatch):
    plan = compile_study(_mock_mphiq_study())
    models_path = _write_mock_runtime(tmp_path)
    result = materialize_study(
        plan,
        _mock_mphiq_resolution(),
        root=tmp_path,
        models_path=models_path,
        require_executable=True,
    )

    assert result.executable_runs == result.exact_runs == 12
    assert sum(result.assignments[0].calls_by_pricing_key.values()) == 8
    configs = {
        (item.trajectory_id, item.seed, item.cell.mphiq_code): ExperimentConfig.model_validate(
            item.execution_config
        )
        for item in result.assignments
    }
    factor_fields = (
        "model_id",
        "profile_id",
        "harness_id",
        "information_policy",
        "prompt_id",
    )
    for (_, _, code), config in configs.items():
        assert code is not None
        groups = config.cohorts[0].agents
        assert len(groups) == 8
        treatments = []
        for group in groups:
            assert group.count == 1
            assert group.mphiq_treatment is not None
            treatments.append(group.mphiq_treatment)
        for bit, field_name in zip(code, factor_fields, strict=True):
            levels = {getattr(treatment, field_name) for treatment in treatments}
            if bit == "1":
                assert len(levels) == 1
            else:
                assert len(levels) >= 2

    for seed in (77, 78):
        different = configs[("mock-trajectory-v1", seed, "00000")]
        flipped = configs[("mock-trajectory-v1", seed, "01000")]
        different_rows = []
        flipped_rows = []
        for group in different.cohorts[0].agents:
            assert group.mphiq_treatment is not None
            different_rows.append(group.mphiq_treatment)
        for group in flipped.cohorts[0].agents:
            assert group.mphiq_treatment is not None
            flipped_rows.append(group.mphiq_treatment)
        for left, right in zip(different_rows, flipped_rows, strict=True):
            assert left.model_id == right.model_id
            assert left.harness_id == right.harness_id
            assert left.harness_temperature == right.harness_temperature
            assert left.harness_memory == right.harness_memory
            assert left.information_policy == right.information_policy
            assert left.prompt_id == right.prompt_id

    invalid = configs[("mock-trajectory-v1", 77, "00000")].model_dump(mode="json")
    forced_model = invalid["cohorts"][0]["agents"][0]["mphiq_treatment"]["model_id"]
    for group in invalid["cohorts"][0]["agents"]:
        group["mphiq_treatment"]["model_id"] = forced_model
    with pytest.raises(ValueError, match="assignment_digest does not match"):
        ExperimentConfig.model_validate(invalid)

    invalid_harness = configs[("mock-trajectory-v1", 77, "00100")].model_dump(mode="json")
    harness_group = invalid_harness["cohorts"][0]["agents"][0]
    harness_group["temperature"] += 0.01
    harness_group["mphiq_treatment"]["harness_temperature"] = harness_group["temperature"]
    _refresh_treatment_digest(harness_group["mphiq_treatment"])
    with pytest.raises(ValueError, match="same-factor harness resolved to multiple levels"):
        ExperimentConfig.model_validate(invalid_harness)

    monkeypatch.chdir(tmp_path)
    agents = build_agents(configs[("mock-trajectory-v1", 77, "00000")], None)
    assert all("mphiq_treatment" in agent.describe() for agent in agents)
    assert {agent.describe()["mphiq_treatment"]["agent_index"] for agent in agents} == set(range(8))

    invalid_revision = configs[("mock-trajectory-v1", 77, "10000")].model_dump(mode="json")
    for group in invalid_revision["cohorts"][0]["agents"]:
        group["mphiq_treatment"]["model_revision"] = "mock-v2"
        _refresh_treatment_digest(group["mphiq_treatment"])
    resolved_invalid_revision = ExperimentConfig.model_validate(invalid_revision)
    with pytest.raises(ValueError, match="model_revision does not match resolved ModelSpec"):
        build_agents(resolved_invalid_revision, None)


def test_materialize_cli_exports_unresolved_assignments_but_fails_closed(tmp_path):
    plan_path = tmp_path / "plan.json"
    output = tmp_path / "assignments.json"
    write_study_plan(compile_study_file(PAPER_CORE), plan_path)

    blocked = CliRunner().invoke(
        app,
        [
            "materialize-study",
            str(plan_path),
            "--output",
            str(output),
            "--root",
            str(Path.cwd()),
        ],
    )
    assert blocked.exit_code == 1
    assert output.exists()
    assert "197 assignment(s) lack explicit execution mappings" in blocked.output

    allowed = CliRunner().invoke(
        app,
        [
            "materialize-study",
            str(plan_path),
            "--output",
            str(output),
            "--root",
            str(Path.cwd()),
            "--allow-unresolved",
        ],
    )
    assert allowed.exit_code == 0, allowed.output
    assert json.loads(output.read_text())["exact_calls"] == 232360
