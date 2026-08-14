"""OpenAI adapter. Requires `uv sync --extra providers` and OPENAI_API_KEY."""

from __future__ import annotations

from importlib.metadata import version
from urllib.parse import urlsplit, urlunsplit

from flock.agents.providers.base import (
    ChatResponse,
    quarantine_provider_response,
    require_execution_lease,
    sanitized_provider_error,
)
from flock.agents.providers.pricing import cost_usd
from flock.core.config import ModelSpec

_DEFAULT_ENDPOINT = "https://api.openai.com/v1/responses"


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
    path = f"{parsed.path.rstrip('/')}/responses"
    return urlunsplit((parsed.scheme, netloc, path, "", ""))


def _contains_refusal(output: object) -> bool:
    if not isinstance(output, (list, tuple)):
        return False
    for item in output:
        content = getattr(item, "content", ())
        if not isinstance(content, (list, tuple)):
            continue
        if any(getattr(part, "type", None) == "refusal" for part in content):
            return True
    return False


class OpenAIChatModel:
    def __init__(
        self,
        model_key: str,
        spec: ModelSpec,
        client=None,
        *,
        execution_lease: object | None = None,
    ):
        if spec.provider != "openai":
            raise ValueError("OpenAIChatModel requires provider='openai'")
        require_execution_lease(model_key, spec, execution_lease)
        self.model_key = model_key
        self.model_id = spec.model_id
        self._client = client

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(max_retries=0)
        return self._client

    def complete(
        self, system: str, user: str, *, temperature: float, seed: int, max_tokens: int
    ) -> ChatResponse:
        # Frontier GPT releases use the Responses API. It has no seed field;
        # reproducibility is preserved by full request hashing and response cache.
        client = self._get_client()
        try:
            resp = client.responses.create(
                model=self.model_id,
                instructions=system,
                input=user,
                temperature=temperature,
                max_output_tokens=max_tokens,
                store=False,
            )
        except Exception as error:
            raise sanitized_provider_error("openai", error) from None

        response_id = getattr(resp, "id", None)
        resolved_model = getattr(resp, "model", None)
        status = getattr(resp, "status", None)
        usage = getattr(resp, "usage", None)
        output = getattr(resp, "output", ())
        if not isinstance(response_id, str) or not response_id:
            raise quarantine_provider_response("openai", "missing response id")
        if not isinstance(resolved_model, str) or not resolved_model:
            raise quarantine_provider_response("openai", "missing resolved model")
        if resolved_model != self.model_id:
            raise quarantine_provider_response("openai", "model resolution drift")
        if usage is None:
            raise quarantine_provider_response("openai", "missing usage")
        if _contains_refusal(output):
            raise quarantine_provider_response("openai", "refusal")
        moderation = getattr(resp, "moderation", None)
        if bool(getattr(moderation, "flagged", False)):
            raise quarantine_provider_response("openai", "unsafe response")
        if status != "completed" or any(
            getattr(item, "status", "completed") != "completed" for item in output
        ):
            raise quarantine_provider_response("openai", "nonterminal response state")

        input_tokens = getattr(usage, "input_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None)
        total_tokens = getattr(usage, "total_tokens", None)
        if not isinstance(input_tokens, int) or input_tokens < 0:
            raise quarantine_provider_response("openai", "invalid input usage")
        if not isinstance(output_tokens, int) or output_tokens < 0:
            raise quarantine_provider_response("openai", "invalid output usage")
        if not isinstance(total_tokens, int) or total_tokens < 0:
            raise quarantine_provider_response("openai", "invalid total usage")
        input_details = getattr(usage, "input_tokens_details", None)
        output_details = getattr(usage, "output_tokens_details", None)
        cached_input_tokens = getattr(input_details, "cached_tokens", 0) or 0
        reasoning_tokens = getattr(output_details, "reasoning_tokens", 0) or 0
        if any(
            not isinstance(value, int) or value < 0
            for value in (cached_input_tokens, reasoning_tokens)
        ):
            raise quarantine_provider_response("openai", "invalid detailed usage")
        text = getattr(resp, "output_text", None)
        if not isinstance(text, str) or not text:
            raise quarantine_provider_response("openai", "missing text output")
        provider_request_id = getattr(resp, "_request_id", "")
        if not isinstance(provider_request_id, str):
            provider_request_id = ""
        return ChatResponse(
            text=text,
            provider="openai",
            requested_model_id=self.model_id,
            resolved_model_id=resolved_model,
            provider_request_id=provider_request_id,
            provider_response_id=response_id,
            sdk_name="openai",
            sdk_version=version("openai"),
            api_version="v1",
            api_endpoint=_endpoint(client),
            terminal_state="completed",
            finish_reason=status,
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
            visible_output_tokens=max(output_tokens - reasoning_tokens, 0),
            reasoning_tokens=reasoning_tokens,
        )
