import numpy as np

from flock.interpretability.artifacts import write_mechanism_artifact
from flock.interpretability.black_box import paired_attribution
from flock.interpretability.local_hooks import activation_patch


class FakeHookableModel:
    checkpoint_hash = "abc"

    def capture(self, prompt, layers):
        return {layer: np.array([float(layer)]) for layer in layers}

    def score_with_patch(self, prompt, patches, target):
        base = 1.0 if prompt == "clean" else 0.0
        return base + sum(float(value[0]) / 10 for value in patches.values())


def test_paired_black_box_attribution_preserves_block_effects():
    effect = paired_attribution("news", [0.1, 0.2, 0.3], [0.4, 0.4, 0.5])
    assert effect.estimate == np.mean(effect.paired_effects)
    assert len(effect.paired_effects) == 3


def test_activation_patching_reports_causal_recovery():
    results = activation_patch(FakeHookableModel(), "clean", "treated", "buy", (1, 2))
    assert [result.layer for result in results] == [1, 2]
    assert results[1].patched_score > results[0].patched_score


def test_mechanism_artifact_is_hashed_and_reproducible(tmp_path):
    tensor = np.arange(6).reshape(2, 3)
    first = write_mechanism_artifact(tmp_path / "a", tensor, "checkpoint", ["p"], "patch", (1,))
    second = write_mechanism_artifact(tmp_path / "b", tensor, "checkpoint", ["p"], "patch", (1,))
    assert first.tensor_sha256 == second.tensor_sha256
    assert first.prompt_hashes == second.prompt_hashes
