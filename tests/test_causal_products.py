import numpy as np
import pandas as pd

from flock.analysis.adoption import threshold_forecast
from flock.analysis.causal import evaluate_ai_causal_gate
from flock.analysis.data_products import export_product
from flock.analysis.signatures import evaluate_detector


def test_causal_gate_never_promotes_signature_without_exposure_and_counterfactual():
    failed = evaluate_ai_causal_gate(False, False, True, True, True)
    assert not failed.passed
    assert failed.allowed_label == "ai_like_signature"
    passed = evaluate_ai_causal_gate(True, True, True, True, True)
    assert passed.passed
    assert passed.allowed_label == "causally_verified_ai_event"


def test_data_product_export_preserves_evidence_tiers(tmp_path):
    frame = pd.DataFrame(
        {
            "record_id": ["a", "b"],
            "evidence_tier": ["simulation_truth", "ai_like_signature"],
            "confidence": [1.0, 0.7],
            "source_hash": ["x", "y"],
        }
    )
    output = export_product(frame, tmp_path / "product", "p1")
    assert (output / "records.parquet").exists()
    assert (output / "manifest.json").exists()


def test_adoption_forecast_is_conditional_on_supplied_draws():
    draws = np.array([[0.1, 0.3], [0.2, 0.4], [0.3, 0.5]])
    result = threshold_forecast(draws, [2027, 2028], impact_threshold=0.35)
    assert result.crossing_probability == (0.0, 2 / 3)


def test_detector_reports_discrimination_and_calibration():
    result = evaluate_detector([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9])
    assert result.roc_auc == 1.0
    assert result.brier_score < 0.1
