from pathlib import Path

import pytest
from pydantic import ValidationError

from flock.agents.cache import ResponseCache
from flock.agents.llm_agent import LLMAgent
from flock.agents.providers.base import ChatResponse
from flock.core.config import ExperimentConfig, PersonaConfig, RuntimeBudget
from flock.experiments.budget import BudgetExceeded, RuntimeBudgetGuard
from tests.test_llm_agent import _cache_context, _obs


def _cap(**updates) -> RuntimeBudget:
    values = {
        "max_requests": 10,
        "max_input_tokens": 100_000,
        "max_output_tokens": 10_000,
        "max_cost_usd": 1.0,
        "request_cost_reserve_usd": 0.25,
    }
    values.update(updates)
    return RuntimeBudget.model_validate(values)


def test_frontier_experiment_requires_runtime_budget():
    with pytest.raises(ValidationError, match="runtime_budget"):
        ExperimentConfig.model_validate(
            {
                "name": "unsafe",
                "dataset": "example",
                "model_policy": "frontier_only",
                "cohorts": [],
            }
        )


def test_budget_reservation_fails_before_crossing_dollar_cap():
    guard = RuntimeBudgetGuard(_cap(max_cost_usd=0.2))
    with pytest.raises(BudgetExceeded, match="cost USD"):
        guard.before_request("system", "user", max_tokens=10, max_attempts=1)
    assert guard.snapshot().requests == 0


def test_success_replaces_conservative_reservation_with_billed_usage():
    guard = RuntimeBudgetGuard(_cap())
    reservation = guard.before_request("system", "user", 100, 3)
    assert guard.snapshot().pending_reservations == 1
    guard.record_response(
        reservation,
        ChatResponse(
            text="{}", input_tokens=20, output_tokens=5, cost_usd=0.01, attempts=2
        ),
    )
    snapshot = guard.snapshot()
    assert snapshot.pending_reservations == 0
    assert (snapshot.requests, snapshot.input_tokens, snapshot.output_tokens) == (2, 20, 5)
    assert snapshot.cost_usd == pytest.approx(0.01)


def test_cached_response_is_not_rebilled_or_remetered(tmp_path: Path):
    class MeteredModel:
        model_key = "metered"
        model_id = "metered-v1"

        def __init__(self):
            self.calls = 0

        def complete(self, *_args, **_kwargs):
            self.calls += 1
            return ChatResponse(
                text='{"orders": [], "rationale": "hold"}',
                input_tokens=100,
                output_tokens=20,
                cost_usd=0.10,
                request_id="request-1",
            )

    model = MeteredModel()
    cache = ResponseCache(tmp_path, _cache_context())
    guard = RuntimeBudgetGuard(_cap())
    persona = PersonaConfig(name="neutral", system_prompt="You are a trader.")
    first = LLMAgent(
        "a", "llm", model, persona, cache=cache,
        before_request=guard.before_request,
        record_response=guard.record_response,
        record_failure=guard.record_failure,
    ).decide(_obs())
    second = LLMAgent(
        "a", "llm", model, persona, cache=cache,
        before_request=guard.before_request,
        record_response=guard.record_response,
        record_failure=guard.record_failure,
    ).decide(_obs())
    assert model.calls == 1
    assert first.usage.cost_usd == pytest.approx(0.10)
    assert second.usage.cost_usd == 0.0
    assert second.usage.attempts == 0
    assert guard.snapshot().requests == 1
