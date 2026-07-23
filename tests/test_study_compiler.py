import copy
import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from flock.core.study import StudySpec
from flock.experiments.study import (
    compile_study,
    compile_study_file,
    load_study_plan,
    write_study_plan,
)

PAPER_CORE = Path("configs/studies/paper-core.yaml")


def _raw_spec() -> dict:
    return yaml.safe_load(PAPER_CORE.read_text())


def _compile_raw(raw: dict):
    return compile_study(StudySpec.model_validate(raw))


def test_paper_core_compiles_deterministically_to_json_serializable_frozen_plan():
    first = compile_study_file(PAPER_CORE)
    second = compile_study_file(PAPER_CORE)

    assert first.plan_hash == second.plan_hash
    assert len(first.plan_hash) == 64
    assert first.exact_runs == 197
    assert first.exact_steps == 21_681
    assert first.exact_agent_steps == 397_528
    assert first.exact_calls == 232_360
    assert first.planned_cost_usd == 18_810.0
    assert sum(first.stages[0].calls_by_pricing_key.values()) == 40
    assert len(first.stages[3].design_cells) == 32
    assert json.loads(json.dumps(first.to_jsonable()))["plan_hash"] == first.plan_hash
    with pytest.raises(ValidationError, match="frozen"):
        first.exact_calls = 0


def test_schema_forbids_unknown_fields_and_invalid_values():
    extra = _raw_spec()
    extra["surprise"] = True
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        StudySpec.model_validate(extra)

    invalid = _raw_spec()
    invalid["stages"][0]["steps_per_run"] = 0
    with pytest.raises(ValidationError, match="greater than 0"):
        StudySpec.model_validate(invalid)


def test_frozen_plan_roundtrip_rejects_tampering(tmp_path):
    path = tmp_path / "plan.json"
    write_study_plan(compile_study_file(PAPER_CORE), path)
    loaded = load_study_plan(path)
    assert loaded.plan_hash

    payload = json.loads(path.read_text())
    payload["exact_calls"] += 1
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="deterministic recompilation"):
        load_study_plan(path)


def test_rejects_placeholder_block_and_mutable_model_alias():
    placeholder = _raw_spec()
    placeholder["dependence_clusters"][0]["cluster_id"] = "unspecified"
    with pytest.raises(ValidationError, match="cannot be a placeholder"):
        StudySpec.model_validate(placeholder)

    alias = _raw_spec()
    alias["cohorts"][0]["allocations"][0]["model_id"] = "gpt-latest"
    with pytest.raises(ValidationError, match="mutable alias"):
        StudySpec.model_validate(alias)


def test_rejects_duplicate_trajectory_ids_and_independent_overlapping_real_windows():
    duplicate = _raw_spec()
    duplicate["trajectories"][1]["trajectory_id"] = duplicate["trajectories"][0][
        "trajectory_id"
    ]
    with pytest.raises(ValueError, match="duplicate trajectory ID"):
        _compile_raw(duplicate)

    overlapping = _raw_spec()
    overlapping["trajectories"][3]["start_date"] = "2018-06-01"
    overlapping["trajectories"][3]["end_date"] = "2018-08-31"
    with pytest.raises(ValueError, match="overlapping real windows"):
        _compile_raw(overlapping)


def test_rejects_unbalanced_heterogeneous_allocation():
    raw = _raw_spec()
    heterogeneous = next(
        cohort for cohort in raw["cohorts"] if cohort["cohort_id"] == "llm-heterogeneous-v1"
    )
    heterogeneous["allocations"][0]["count"] = 5
    with pytest.raises(ValidationError, match="differ by at most one"):
        StudySpec.model_validate(raw)


def test_rejects_unmatched_h1_family_rotation_and_unknown_holdout():
    unmatched = _raw_spec()
    unmatched["stages"][0]["cohort_ids"].remove("llm-homogeneous-gemini-v1")
    with pytest.raises(ValueError, match="family rotation"):
        _compile_raw(unmatched)

    unknown_holdout = _raw_spec()
    unknown_holdout["held_out_families"] = ["unseen-family"]
    with pytest.raises(ValueError, match="held-out model families"):
        _compile_raw(unknown_holdout)


def test_rejects_stage_cap_count_drift_and_budget_overrun():
    too_many_stages = _raw_spec()
    too_many_stages["max_stages"] = 4
    with pytest.raises(ValueError, match="exceeding stage cap"):
        _compile_raw(too_many_stages)

    count_drift = _raw_spec()
    count_drift["stages"][0]["expected_counts"]["calls"] += 1
    with pytest.raises(ValueError, match="declared exact counts"):
        _compile_raw(count_drift)

    over_budget = copy.deepcopy(_raw_spec())
    over_budget["stages"][0]["budget_cap"]["max_calls"] = 1
    with pytest.raises(ValueError, match="stage call cap"):
        _compile_raw(over_budget)


def test_rejects_missing_pricing_and_preconfirmatory_spend_overruns():
    missing_price = _raw_spec()
    missing_price["cohorts"][0]["allocations"][0]["pricing_key"] = "unpriced-model"
    with pytest.raises(ValueError, match="no dated pricing"):
        _compile_raw(missing_price)

    excessive_canary = _raw_spec()
    excessive_canary["stages"][0]["planned_cost_usd"] = 51.0
    excessive_canary["stages"][0]["budget_cap"]["max_cost_usd"] = 51.0
    with pytest.raises(ValueError, match=r"\$50 hard ceiling"):
        _compile_raw(excessive_canary)
