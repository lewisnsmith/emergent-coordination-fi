"""Fail-closed tests for the direct experiment execution boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from typer.testing import CliRunner

import flock.agents.providers.anthropic_provider as anthropic_provider
import flock.agents.providers.openai_compatible as openai_compatible_provider
import flock.experiments.grid as grid_module
import flock.experiments.runner as runner_module
from flock.agents.providers.base import (
    _ExecutionLease,
    _issue_execution_lease,
    make_chat_model,
)
from flock.cli import app
from flock.core.config import ExperimentConfig, ModelSpec, load_models


def _api_config(model: str = "claude-opus-frontier") -> ExperimentConfig:
    return ExperimentConfig.model_validate(
        {
            "name": "blocked-api-run",
            "dataset": "must-not-be-read",
            "model_policy": "frontier_only",
            "runtime_budget": {
                "max_requests": 1,
                "max_input_tokens": 100,
                "max_output_tokens": 100,
                "max_cost_usd": 1.0,
                "request_cost_reserve_usd": 1.0,
            },
            "cohorts": [
                {
                    "name": "llm",
                    "agents": [
                        {
                            "kind": "llm",
                            "model": model,
                            "persona": "neutral",
                            "count": 1,
                        }
                    ],
                }
            ],
        },
    )


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=True))


def test_run_config_rejects_api_before_resume_data_or_provider_construction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        runner_module,
        "make_run_id",
        lambda _cfg: calls.append("resume") or "should-not-be-used",
    )
    monkeypatch.setattr(
        runner_module,
        "build_market",
        lambda *_args, **_kwargs: calls.append("market"),
    )
    monkeypatch.setattr(
        runner_module,
        "make_chat_model",
        lambda *_args, **_kwargs: calls.append("provider"),
    )

    with pytest.raises(PermissionError, match="internally issued exact-model execution lease"):
        runner_module.run_config(_api_config(), results_root=tmp_path)

    assert calls == []


def test_run_cli_rejects_api_before_provider_construction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "api-run.yaml"
    _write_yaml(config_path, _api_config().model_dump(mode="json"))
    calls: list[str] = []
    monkeypatch.setattr(
        runner_module,
        "make_chat_model",
        lambda *_args, **_kwargs: calls.append("provider"),
    )

    result = CliRunner().invoke(app, ["run", str(config_path)])

    assert result.exit_code == 1
    assert isinstance(result.exception, PermissionError)
    assert calls == []


def test_grid_and_sweep_cli_preflight_all_cells_before_resume_or_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base_path = tmp_path / "api-base.yaml"
    sweep_path = tmp_path / "api-sweep.yaml"
    _write_yaml(base_path, _api_config().model_dump(mode="json"))
    _write_yaml(
        sweep_path,
        {
            "name": "blocked-api-sweep",
            "base": str(base_path),
            "models": [],
            "personas": [],
            "temperatures": [],
            "seeds": [1, 2],
        },
    )
    calls: list[str] = []
    monkeypatch.setattr(
        grid_module,
        "make_run_id",
        lambda _cfg: calls.append("resume") or "should-not-be-used",
    )
    monkeypatch.setattr(
        grid_module,
        "run_config",
        lambda *_args, **_kwargs: calls.append("run"),
    )

    with pytest.raises(PermissionError, match="internally issued exact-model execution lease"):
        grid_module.run_sweep(sweep_path, results_root=tmp_path / "direct-results")
    direct_calls = list(calls)

    result = CliRunner().invoke(app, ["sweep", str(sweep_path)])

    assert direct_calls == []
    assert result.exit_code == 1
    assert isinstance(result.exception, PermissionError)
    assert calls == []


def test_provider_factory_rejects_missing_forged_and_wrong_model_leases_before_constructor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, ModelSpec]] = []

    class ConstructorSpy:
        def __init__(self, model_key: str, spec: ModelSpec):
            calls.append((model_key, spec))
            self.model_key = model_key
            self.model_id = spec.model_id

        def complete(self, *_args: Any, **_kwargs: Any):
            raise AssertionError("the test must not make a provider call")

    monkeypatch.setattr(anthropic_provider, "AnthropicChatModel", ConstructorSpy)
    spec = load_models()["claude-opus-frontier"]

    with pytest.raises(PermissionError, match="internally issued exact-model execution lease"):
        make_chat_model("claude-opus-frontier", spec)

    counterfeit = object.__new__(_ExecutionLease)
    with pytest.raises(PermissionError, match="internally issued exact-model execution lease"):
        make_chat_model("claude-opus-frontier", spec, execution_lease=counterfeit)

    lease = _issue_execution_lease(
        allowed_models={"claude-opus-frontier": spec},
        authorization_digest="a" * 64,
    )
    with pytest.raises(PermissionError, match="internally issued exact-model execution lease"):
        make_chat_model("different-registry-key", spec, execution_lease=lease)

    changed_spec = spec.model_copy(update={"max_tokens": spec.max_tokens + 1})
    with pytest.raises(PermissionError, match="internally issued exact-model execution lease"):
        make_chat_model("claude-opus-frontier", changed_spec, execution_lease=lease)

    assert calls == []

    model = make_chat_model("claude-opus-frontier", spec, execution_lease=lease)
    assert model.model_id == spec.model_id
    assert calls == [("claude-opus-frontier", spec)]


def test_mock_and_local_models_do_not_require_execution_lease(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    local_calls: list[tuple[str, ModelSpec]] = []

    class LocalConstructorSpy:
        def __init__(self, model_key: str, spec: ModelSpec):
            local_calls.append((model_key, spec))
            self.model_key = model_key
            self.model_id = spec.model_id

        def complete(self, *_args: Any, **_kwargs: Any):
            raise AssertionError("the test must not call the local endpoint")

    monkeypatch.setattr(
        openai_compatible_provider,
        "OpenAICompatibleChatModel",
        LocalConstructorSpy,
    )
    models = load_models()
    mock_spec = models["mock-hold"]
    local_spec = models["gpt-oss-120b-local"]

    mock_model = make_chat_model("mock-hold", mock_spec)
    local_model = make_chat_model("gpt-oss-120b-local", local_spec)

    assert mock_model.model_id == mock_spec.model_id
    assert local_model.model_id == local_spec.model_id
    assert local_calls == [("gpt-oss-120b-local", local_spec)]
