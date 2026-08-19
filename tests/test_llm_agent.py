import json
from concurrent.futures import ThreadPoolExecutor
from typing import Literal

import pytest
from pydantic import ValidationError

from flock.agents.cache import CacheContextV1, CacheIntegrityError, ResponseCache
from flock.agents.grounding import validate_grounding
from flock.agents.llm_agent import LLMAgent, parse_response, render_user_prompt
from flock.agents.providers.base import ChatResponse, make_chat_model
from flock.core.config import ModelSpec, PersonaConfig
from flock.core.types import Bar, Observation, PortfolioView


def _cache_context(**updates) -> CacheContextV1:
    values = {
        "execution_class": "mock",
        "analysis_role": "rehearsal",
        "split_role": "not_applicable",
        "execution_fingerprint_sha256": "1" * 64,
        "provider_contract_sha256": "0" * 64,
        "split_registry_sha256": "0" * 64,
        "dataset_sha256": "2" * 64,
    }
    values.update(updates)
    return CacheContextV1.model_validate(values)


def _obs() -> Observation:
    bars = {
        "X": tuple(Bar(f"t{i}", "X", 10, 11, 9, 10 + i * 0.5, 100) for i in range(6)),
        "Y": tuple(Bar(f"t{i}", "Y", 20, 21, 19, 20 - i * 0.5, 100) for i in range(6)),
    }
    return Observation(
        step=0, ts="t5", symbols=("X", "Y"), bars=bars,
        prices={"X": bars["X"][-1].close, "Y": bars["Y"][-1].close},
        news=(), portfolio=PortfolioView(cash=1000.0, positions=(), equity=1000.0),
    )


def test_parse_response_valid():
    text = '{"orders": [{"symbol": "X", "side": "buy", "quantity": 5}], "rationale": "r"}'
    parsed = parse_response(text, ("X", "Y"))
    assert parsed is not None
    orders, rationale = parsed
    assert orders[0].symbol == "X" and orders[0].quantity == 5
    assert rationale == "r"


def test_parse_response_rejects_bad_symbol_and_garbage():
    bad = '{"orders": [{"symbol": "Z", "side": "buy", "quantity": 5}]}'
    assert parse_response(bad, ("X",)) is None
    assert parse_response("not json at all", ("X",)) is None


def test_parse_response_rejects_non_finite_or_non_positive_numbers():
    assert parse_response(
        '{"orders": [{"symbol": "X", "side": "buy", "quantity": NaN}]}', ("X",)
    ) is None
    assert parse_response(
        '{"orders": [{"symbol": "X", "side": "buy", "quantity": 1, '
        '"limit_price": -1}]}',
        ("X",),
    ) is None


def test_parse_response_handles_code_fence():
    text = '```json\n{"orders": [], "rationale": "hold"}\n```'
    parsed = parse_response(text, ("X",))
    assert parsed is not None and parsed[0] == ()


def _mock_agent(
    behavior: Literal["momentum", "contrarian", "random", "hold"] = "momentum",
    cache=None,
) -> LLMAgent:
    spec = ModelSpec(provider="mock", model_id=f"mock-{behavior}", behavior=behavior)
    persona = PersonaConfig(name="neutral", system_prompt="You are a trader.")
    model = make_chat_model(f"mock-{behavior}", spec)
    return LLMAgent("a1", "llm", model, persona, seed=7, cache=cache)


def test_mock_momentum_agent_buys_winner():
    decision = _mock_agent("momentum").decide(_obs())
    assert decision.parse_ok
    buys = [o for o in decision.orders if o.side == "buy"]
    assert buys and buys[0].symbol == "X"  # X trending up, Y down


def test_mock_agent_is_deterministic():
    d1 = _mock_agent("random").decide(_obs())
    d2 = _mock_agent("random").decide(_obs())
    assert d1.orders == d2.orders


def test_cache_roundtrip(tmp_path):
    cache = ResponseCache(root=tmp_path, context=_cache_context())
    key = cache.key("m", "mid", 0.7, 1, 100, "sys", "user")
    assert cache.get(key) is None
    response = ChatResponse(
        text="hello",
        provider="mock",
        requested_model_id="mid",
        resolved_model_id="mid",
        provider_response_id="mock-response-1",
        terminal_state="completed",
        usage_reported=True,
        cost_usd=0.01,
    )
    cache.put(key, response)
    got = cache.get(key)
    assert got == response


def test_cache_concurrent_writes_are_atomic_and_idempotent(tmp_path):
    cache = ResponseCache(root=tmp_path, context=_cache_context())
    key = cache.key("m", "mid", 0.7, 1, 100, "sys", "user")
    response = ChatResponse(text="one authenticated response")
    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(lambda _index: cache.put(key, response), range(12)))
    assert cache.get(key) == response
    assert not list(tmp_path.rglob("*.tmp"))


def test_cache_rejects_tamper_and_nondeterministic_collision(tmp_path):
    cache = ResponseCache(root=tmp_path, context=_cache_context())
    key = cache.key("m", "mid", 0.7, 1, 100, "sys", "user")
    cache.put(key, ChatResponse(text="first"))
    with pytest.raises(CacheIntegrityError, match="different response"):
        cache.put(key, ChatResponse(text="second"))

    entry = next(tmp_path.rglob("*.json"))
    payload = json.loads(entry.read_text())
    payload["response"]["text"] = "mutated"
    entry.write_text(json.dumps(payload))
    with pytest.raises(CacheIntegrityError, match="response hash"):
        cache.get(key)


def test_cache_namespaces_cannot_cross_evidence_or_split_roles(tmp_path):
    contexts = (
        _cache_context(),
        _cache_context(
            execution_class="local",
            analysis_role="discovery",
            split_role="train",
            split_registry_sha256="3" * 64,
        ),
        _cache_context(
            execution_class="fake_provider",
            analysis_role="discovery",
            split_role="train",
            provider_contract_sha256="4" * 64,
            split_registry_sha256="3" * 64,
        ),
        _cache_context(
            execution_class="provider",
            analysis_role="confirmatory",
            split_role="test",
            provider_contract_sha256="5" * 64,
            split_registry_sha256="6" * 64,
        ),
    )
    caches = [ResponseCache(tmp_path, context) for context in contexts]
    keys = [cache.key("m", "mid", 0.7, 1, 100, "sys", "user") for cache in caches]
    assert len(set(keys)) == len(keys)
    caches[0].put(keys[0], ChatResponse(text="mock only"))
    assert all(
        cache.get(key) is None
        for cache, key in zip(caches[1:], keys[1:], strict=True)
    )

    with pytest.raises(ValidationError, match="held-out test"):
        _cache_context(analysis_role="confirmatory")
    with pytest.raises(ValidationError, match="provider contract"):
        _cache_context(execution_class="provider")


def test_prompt_contains_observation_block():
    prompt = render_user_prompt(_obs())
    assert "## OBSERVATION_JSON" in prompt
    assert "RESPONSE FORMAT" in prompt
    assert "never invent" in prompt


def test_prompt_includes_prediction_contract_semantics():
    observation = _obs()
    observation = Observation(
        step=observation.step,
        ts=observation.ts,
        symbols=observation.symbols,
        bars=observation.bars,
        prices=observation.prices,
        news=observation.news,
        portfolio=observation.portfolio,
        instrument_context={
            "X": {
                "question": "Will X occur?",
                "close_ts": "2030-12-31T00:00:00Z",
                "rules": "Resolves Yes only if X occurs.",
                "price_semantics": "YES probability in [0,1]",
            }
        },
    )
    prompt = render_user_prompt(observation)
    assert "Will X occur?" in prompt
    assert "2030-12-31" in prompt
    assert "Resolves Yes only" in prompt


def test_grounding_rejects_fabricated_evidence_and_numeric_claims():
    verdict = validate_grounding(
        _obs(),
        evidence_refs=("price:Z",),
        confidence=1.2,
        rationale="X is definitely priced at 9999.",
        require_refs=True,
    )
    assert not verdict.ok
    assert any("unknown evidence" in failure for failure in verdict.failures)
    assert any("unsupported numeric" in failure for failure in verdict.failures)
    assert any("confidence" in failure for failure in verdict.failures)


def test_strict_grounding_fails_closed_without_evidence_refs():
    agent = _mock_agent("momentum")
    agent.grounding_mode = "strict"
    decision = agent.decide(_obs())
    assert decision.parse_ok
    assert not decision.grounding_ok
    assert decision.orders == ()


def test_usage_preserves_provider_attempt_and_reasoning_metadata():
    class Metered:
        model_key = "metered"
        model_id = "metered-v1"

        def complete(self, *_args, **_kwargs):
            return ChatResponse(
                text='{"orders": [], "rationale": "hold"}',
                input_tokens=100,
                output_tokens=50,
                cost_usd=0.01,
                request_id="request-1",
                visible_output_tokens=20,
                reasoning_tokens=30,
                attempts=2,
                retry_errors=("TimeoutError: first attempt",),
            )

    persona = PersonaConfig(name="neutral", system_prompt="You are a trader.")
    decision = LLMAgent("a", "llm", Metered(), persona).decide(_obs())
    assert decision.usage.reasoning_tokens == 30
    assert decision.usage.visible_output_tokens == 20
    assert decision.usage.attempts == 2
    assert decision.usage.request_ids == ("request-1",)
    assert len(decision.usage.retry_errors) == 1
