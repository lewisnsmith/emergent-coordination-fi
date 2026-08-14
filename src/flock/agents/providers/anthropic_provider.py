"""Anthropic adapter. Requires `uv sync --extra providers` and ANTHROPIC_API_KEY."""

from __future__ import annotations

import re
from importlib.metadata import version
from urllib.parse import urlsplit, urlunsplit

from flock.agents.providers.base import (
    ChatResponse,
    quarantine_provider_response,
    sanitized_provider_error,
)
from flock.agents.providers.pricing import cost_usd
from flock.core.config import ModelSpec

_API_VERSION = "2023-06-01"
_DEFAULT_ENDPOINT = "https://api.anthropic.com/v1/messages"
_TERMINAL_STOP_REASONS = frozenset({"end_turn", "max_tokens", "stop_sequence"})


def _text_content(block: object) -> str:
    """Extract only Anthropic text blocks across evolving SDK union types."""
    if getattr(block, "type", None) != "text":
        return ""
    value = getattr(block, "text", None)
    return value if isinstance(value, str) else ""


def _sampling_is_unsupported(model_id: str) -> bool:
    if model_id.startswith("claude-sonnet-5"):
        return True
    match = re.match(r"^claude-opus-4[-.](\d+)", model_id)
    return match is not None and int(match.group(1)) >= 7


def _endpoint(client: object) -> str:
    raw_base = getattr(client, "base_url", None)
    if raw_base is None:
        return _DEFAULT_ENDPOINT
    parsed = urlsplit(str(raw_base))
    if not parsed.scheme or not parsed.hostname:
        return _DEFAULT_ENDPOINT
    netloc = parsed.hostname
    if parsed.port is not None:
        netloc = f"{netloc}:{parsed.port}"
    path = f"{parsed.path.rstrip('/')}/messages"
    return urlunsplit((parsed.scheme, netloc, path, "", ""))


class AnthropicChatModel:
    def __init__(self, model_key: str, spec: ModelSpec, client=None):
        self.model_key = model_key
        self.model_id = spec.model_id
        self._client = client

    def _get_client(self):
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic(max_retries=0)
        return self._client

    def complete(
        self, system: str, user: str, *, temperature: float, seed: int, max_tokens: int
    ) -> ChatResponse:
        # Anthropic has no seed parameter; determinism comes from the response cache.
        client = self._get_client()
        request = {
            "model": self.model_id,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        omitted_parameters: tuple[str, ...] = ()
        if _sampling_is_unsupported(self.model_id):
            omitted_parameters = ("temperature", "top_p", "top_k")
        else:
            request["temperature"] = temperature
        try:
            msg = client.messages.create(**request)
        except Exception as error:
            raise sanitized_provider_error("anthropic", error) from None

        response_id = getattr(msg, "id", None)
        resolved_model = getattr(msg, "model", None)
        usage = getattr(msg, "usage", None)
        stop_reason = getattr(msg, "stop_reason", None)
        if not isinstance(response_id, str) or not response_id:
            raise quarantine_provider_response("anthropic", "missing response id")
        if not isinstance(resolved_model, str) or not resolved_model:
            raise quarantine_provider_response("anthropic", "missing resolved model")
        if resolved_model != self.model_id:
            raise quarantine_provider_response("anthropic", "model resolution drift")
        if usage is None:
            raise quarantine_provider_response("anthropic", "missing usage")
        if stop_reason == "refusal" or any(
            getattr(block, "type", None) == "refusal" for block in msg.content
        ):
            raise quarantine_provider_response("anthropic", "refusal")
        if stop_reason not in _TERMINAL_STOP_REASONS:
            raise quarantine_provider_response("anthropic", "nonterminal stop state")

        input_tokens = getattr(usage, "input_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None)
        if not isinstance(input_tokens, int) or input_tokens < 0:
            raise quarantine_provider_response("anthropic", "invalid input usage")
        if not isinstance(output_tokens, int) or output_tokens < 0:
            raise quarantine_provider_response("anthropic", "invalid output usage")
        cached_input_tokens = getattr(usage, "cache_read_input_tokens", 0) or 0
        cache_write_tokens = getattr(usage, "cache_creation_input_tokens", 0) or 0
        output_details = getattr(usage, "output_tokens_details", None)
        reasoning_tokens = getattr(output_details, "thinking_tokens", 0) or 0
        if any(
            not isinstance(value, int) or value < 0
            for value in (cached_input_tokens, cache_write_tokens, reasoning_tokens)
        ):
            raise quarantine_provider_response("anthropic", "invalid detailed usage")

        text = "".join(_text_content(block) for block in msg.content)
        if not text:
            raise quarantine_provider_response("anthropic", "missing text output")
        provider_request_id = getattr(msg, "_request_id", "")
        if not isinstance(provider_request_id, str):
            provider_request_id = ""
        return ChatResponse(
            text=text,
            provider="anthropic",
            requested_model_id=self.model_id,
            resolved_model_id=resolved_model,
            provider_request_id=provider_request_id,
            provider_response_id=response_id,
            sdk_name="anthropic",
            sdk_version=version("anthropic"),
            api_version=_API_VERSION,
            api_endpoint=_endpoint(client),
            terminal_state="completed",
            finish_reason=stop_reason,
            stop_reason=stop_reason,
            safety_status="safe",
            usage_reported=True,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=cost_usd(
                self.model_id,
                input_tokens,
                output_tokens,
                cached_input_tokens=cached_input_tokens,
                cache_write_tokens=cache_write_tokens,
            ),
            request_id=response_id,
            cached_input_tokens=cached_input_tokens,
            cache_write_tokens=cache_write_tokens,
            visible_output_tokens=max(output_tokens - reasoning_tokens, 0),
            reasoning_tokens=reasoning_tokens,
            omitted_parameters=omitted_parameters,
        )
