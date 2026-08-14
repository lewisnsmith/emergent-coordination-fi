from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from flock.control import ScienceLockV1, load_science_lock


def test_checked_in_science_lock_has_registered_h1_and_h4_orientation() -> None:
    lock = load_science_lock()
    values = {
        "llm_homogeneous": 2.0,
        "llm_heterogeneous": 5.0,
        "classical_homogeneous": 1.0,
        "classical_heterogeneous": 3.0,
    }
    assert lock.contrast("H1.delta_tech", values) == pytest.approx(1.5)
    assert lock.contrast("H1.delta_int", values) == pytest.approx(-1.0)
    sign_flip = next(
        item for item in lock.estimands if item.estimand_id == "H1.sign_flip_sensitivity"
    )
    assert sign_flip.inference_role == "sensitivity_only"
    assert sign_flip.multiplicity_order is None
    h4 = next(item for item in lock.estimands if item.estimand_id == "H4.mphiq_component")
    assert h4.orientation == "same_minus_different"
    assert h4.required_cube_edges == 80
    assert not lock.confirmatory_ready


def test_science_lock_rejects_coefficient_and_cube_drift() -> None:
    lock = load_science_lock()
    payload = lock.model_dump(mode="json")
    payload["estimands"][0]["coefficients"][0]["coefficient"] = 0.4
    payload["estimands"][0]["coefficients"][1]["coefficient"] = -0.4
    with pytest.raises(ValidationError, match="registered contrast"):
        ScienceLockV1.model_validate_json(json.dumps(payload))

    payload = lock.model_dump(mode="json")
    h4 = next(item for item in payload["estimands"] if item["hypothesis_id"] == "H4")
    h4["required_cube_edges"] = 79
    with pytest.raises(ValidationError, match="exactly 80"):
        ScienceLockV1.model_validate_json(json.dumps(payload))


def test_draft_cannot_be_relabelled_frozen_without_decisions_and_receipts() -> None:
    payload = json.loads(load_science_lock().model_dump_json())
    payload["status"] = "frozen"
    payload["blockers"] = []
    with pytest.raises(ValidationError, match="confirmatory estimands are incomplete"):
        ScienceLockV1.model_validate_json(json.dumps(payload))


def test_source_drift_is_detected(tmp_path) -> None:
    lock = load_science_lock()
    config = tmp_path / "science-lock.json"
    config.write_text(lock.model_dump_json())
    with pytest.raises(ValueError, match="science-lock source"):
        load_science_lock(config, repo_root=tmp_path)
