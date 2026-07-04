from flock.agents.cache import ResponseCache
from flock.agents.llm_agent import LLMAgent, parse_response, render_user_prompt
from flock.agents.providers.base import ChatResponse, make_chat_model
from flock.core.config import ModelSpec, PersonaConfig
from flock.core.types import Bar, Observation, PortfolioView


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


def test_parse_response_handles_code_fence():
    text = '```json\n{"orders": [], "rationale": "hold"}\n```'
    parsed = parse_response(text, ("X",))
    assert parsed is not None and parsed[0] == ()


def _mock_agent(behavior: str = "momentum", cache=None) -> LLMAgent:
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
    cache = ResponseCache(root=tmp_path)
    key = ResponseCache.key("m", "mid", 0.7, 1, 100, "sys", "user")
    assert cache.get(key) is None
    cache.put(key, ChatResponse(text="hello", cost_usd=0.01))
    got = cache.get(key)
    assert got is not None and got.text == "hello" and got.cost_usd == 0.01


def test_prompt_contains_observation_block():
    prompt = render_user_prompt(_obs())
    assert "## OBSERVATION_JSON" in prompt
    assert "RESPONSE FORMAT" in prompt
