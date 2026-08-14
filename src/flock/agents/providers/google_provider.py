"""Google Gemini adapter. Requires `uv sync --extra providers` and GEMINI_API_KEY."""

from __future__ import annotations

import importlib
from collections.abc import Mapping
from importlib.metadata import version
from urllib.parse import urlsplit, urlunsplit

from flock.agents.providers.base import (
    ChatResponse,
    quarantine_provider_response,
    sanitized_provider_error,
)
from flock.agents.providers.pricing import cost_usd
from flock.core.config import ModelSpec

_DEFAULT_API_VERSION = "v1beta"
_TERMINAL_FINISH_REASONS = frozenset({"STOP", "MAX_TOKENS"})


def _enum_value(value: object) -> str:
    raw = getattr(value, "value", value)
    return raw if isinstance(raw, str) else ""


def _http_details(client: object, model_id: str) -> tuple[str, str]:
    api_client = getattr(client, "_api_client", None)
    options = getattr(api_client, "_http_options", None)
    raw_base = getattr(options, "base_url", None)
    api_version = getattr(options, "api_version", None)
    if not isinstance(api_version, str) or not api_version:
        api_version = _DEFAULT_API_VERSION
    default_base = "https://generativelanguage.googleapis.com"
    parsed = urlsplit(str(raw_base or default_base))
    if not parsed.scheme or not parsed.hostname:
        parsed = urlsplit(default_base)
    netloc = parsed.hostname or "generativelanguage.googleapis.com"
    if parsed.port is not None:
        netloc = f"{netloc}:{parsed.port}"
    base_path = parsed.path.rstrip("/")
    path = f"{base_path}/{api_version}/models/{model_id}:generateContent"
    return api_version, urlunsplit((parsed.scheme, netloc, path, "", ""))


def _provider_request_id(response: object) -> str:
    http_response = getattr(response, "sdk_http_response", None)
    headers = getattr(http_response, "headers", None)
    if not isinstance(headers, Mapping):
        return ""
    for key, value in headers.items():
        if str(key).lower() in {"x-request-id", "x-goog-request-id"}:
            return str(value)
    return ""


class GoogleChatModel:
    def __init__(self, model_key: str, spec: ModelSpec, client=None):
        self.model_key = model_key
        self.model_id = spec.model_id
        self._client = client

    def _get_client(self):
        if self._client is None:
            genai = importlib.import_module("google.genai")
            types = importlib.import_module("google.genai.types")
            http_options = types.HttpOptions(
                retry_options=types.HttpRetryOptions(attempts=1)
            )
            self._client = genai.Client(http_options=http_options)
        return self._client

    def complete(
        self, system: str, user: str, *, temperature: float, seed: int, max_tokens: int
    ) -> ChatResponse:
        from google.genai import types

        client = self._get_client()
        try:
            resp = client.models.generate_content(
                model=self.model_id,
                contents=user,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    seed=seed,
                ),
            )
        except Exception as error:
            raise sanitized_provider_error("google", error) from None

        response_id = getattr(resp, "response_id", None)
        resolved_model = getattr(resp, "model_version", None)
        usage = getattr(resp, "usage_metadata", None)
        candidates = getattr(resp, "candidates", None)
        if not isinstance(response_id, str) or not response_id:
            raise quarantine_provider_response("google", "missing response id")
        if not isinstance(resolved_model, str) or not resolved_model:
            raise quarantine_provider_response("google", "missing resolved model")
        if resolved_model != self.model_id:
            raise quarantine_provider_response("google", "model resolution drift")
        if usage is None:
            raise quarantine_provider_response("google", "missing usage")
        if not isinstance(candidates, (list, tuple)) or not candidates:
            raise quarantine_provider_response("google", "missing candidates")

        prompt_feedback = getattr(resp, "prompt_feedback", None)
        block_reason = _enum_value(getattr(prompt_feedback, "block_reason", None))
        if block_reason not in {"", "BLOCKED_REASON_UNSPECIFIED"}:
            raise quarantine_provider_response("google", "blocked prompt")
        finish_reasons = tuple(
            _enum_value(getattr(candidate, "finish_reason", None))
            for candidate in candidates
        )
        if any(reason not in _TERMINAL_FINISH_REASONS for reason in finish_reasons):
            raise quarantine_provider_response("google", "unsafe or nonterminal result")
        safety_ratings = (
            rating
            for candidate in candidates
            for rating in (getattr(candidate, "safety_ratings", None) or ())
        )
        if any(bool(getattr(rating, "blocked", False)) for rating in safety_ratings):
            raise quarantine_provider_response("google", "unsafe result")

        input_tokens = getattr(usage, "prompt_token_count", None)
        visible_output_tokens = getattr(usage, "candidates_token_count", None)
        reasoning_tokens = getattr(usage, "thoughts_token_count", 0) or 0
        cached_input_tokens = getattr(usage, "cached_content_token_count", 0) or 0
        total_tokens = getattr(usage, "total_token_count", None)
        if not isinstance(input_tokens, int) or input_tokens < 0:
            raise quarantine_provider_response("google", "invalid input usage")
        if not isinstance(visible_output_tokens, int) or visible_output_tokens < 0:
            raise quarantine_provider_response("google", "invalid visible usage")
        if not isinstance(total_tokens, int) or total_tokens < 0:
            raise quarantine_provider_response("google", "invalid total usage")
        if any(
            not isinstance(value, int) or value < 0
            for value in (reasoning_tokens, cached_input_tokens)
        ):
            raise quarantine_provider_response("google", "invalid detailed usage")
        output_tokens = visible_output_tokens + reasoning_tokens
        try:
            text = resp.text
        except Exception:
            raise quarantine_provider_response("google", "unreadable text output") from None
        if not isinstance(text, str) or not text:
            raise quarantine_provider_response("google", "missing text output")
        api_version, api_endpoint = _http_details(client, self.model_id)
        return ChatResponse(
            text=text,
            provider="google",
            requested_model_id=self.model_id,
            resolved_model_id=resolved_model,
            provider_request_id=_provider_request_id(resp),
            provider_response_id=response_id,
            sdk_name="google-genai",
            sdk_version=version("google-genai"),
            api_version=api_version,
            api_endpoint=api_endpoint,
            terminal_state="completed",
            finish_reason=",".join(finish_reasons),
            stop_reason=",".join(finish_reasons),
            safety_status="safe",
            usage_reported=True,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd(
                self.model_id,
                input_tokens,
                output_tokens,
                cached_input_tokens=cached_input_tokens,
            ),
            request_id=response_id,
            cached_input_tokens=cached_input_tokens,
            visible_output_tokens=visible_output_tokens,
            reasoning_tokens=reasoning_tokens,
        )
