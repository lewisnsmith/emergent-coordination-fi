"""Generic OpenAI-compatible endpoint adapter (Ollama, vLLM, OpenRouter, ...).

Configure via OPENAI_COMPATIBLE_BASE_URL / OPENAI_COMPATIBLE_API_KEY.
"""

from __future__ import annotations

import ipaddress
import os
import re
from importlib.metadata import version
from urllib.parse import urlsplit, urlunsplit

from flock.agents.providers.base import (
    ChatResponse,
    quarantine_provider_response,
    require_execution_lease,
    sanitized_provider_error,
)
from flock.core.config import ModelSpec

_DNS_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$", re.ASCII)


def _valid_host(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
    except ValueError:
        labels = host.lower().split(".")
        return (
            len(host) <= 253
            and bool(labels)
            and all(_DNS_LABEL.fullmatch(label) for label in labels)
        )
    return True


def _loopback_host(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _parse_base_url(raw: object, *, require_loopback: bool) -> str:
    if not isinstance(raw, str) or not raw:
        raise RuntimeError("OPENAI_COMPATIBLE_BASE_URL is required")
    if raw != raw.strip() or any(ord(char) <= 32 or char == "\\" for char in raw):
        raise RuntimeError("OPENAI_COMPATIBLE_BASE_URL is malformed")
    try:
        parsed = urlsplit(raw)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        raise RuntimeError("OPENAI_COMPATIBLE_BASE_URL is malformed") from None
    if parsed.scheme not in {"http", "https"}:
        raise RuntimeError("OPENAI_COMPATIBLE_BASE_URL uses an unsupported scheme")
    if (
        not parsed.netloc
        or hostname is None
        or "%" in parsed.netloc
        or not _valid_host(hostname)
    ):
        raise RuntimeError("OPENAI_COMPATIBLE_BASE_URL must contain a valid host")
    if (
        parsed.username is not None
        or parsed.password is not None
        or "@" in parsed.netloc
    ):
        raise RuntimeError("OPENAI_COMPATIBLE_BASE_URL cannot contain userinfo")
    if parsed.query or parsed.fragment or "?" in raw or "#" in raw:
        raise RuntimeError("OPENAI_COMPATIBLE_BASE_URL cannot contain query or fragment")
    if require_loopback and not _loopback_host(hostname):
        raise RuntimeError(
            "OPENAI_COMPATIBLE_BASE_URL must use a loopback host for local deployment"
        )

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        normalized_host = hostname.lower()
    else:
        normalized_host = address.compressed
    if ":" in normalized_host:
        normalized_host = f"[{normalized_host}]"
    netloc = normalized_host if port is None else f"{normalized_host}:{port}"
    return urlunsplit(
        (parsed.scheme, netloc, parsed.path.rstrip("/"), "", "")
    )


def _environment_base_url(*, require_loopback: bool) -> str:
    return _parse_base_url(
        os.environ.get("OPENAI_COMPATIBLE_BASE_URL"),
        require_loopback=require_loopback,
    )


def validate_local_compatible_endpoint() -> str:
    """Validate the environment boundary before runner-side data or provider work."""
    return _environment_base_url(require_loopback=True)


def _chat_endpoint(base_url: str) -> str:
    return f"{base_url}/chat/completions"


class OpenAICompatibleChatModel:
    def __init__(
        self,
        model_key: str,
        spec: ModelSpec,
        client=None,
        *,
        execution_lease: object | None = None,
    ):
        if spec.provider != "openai_compatible":
            raise ValueError(
                "OpenAICompatibleChatModel requires provider='openai_compatible'"
            )
        if spec.deployment not in {"api", "local"}:
            raise ValueError("OpenAICompatibleChatModel requires api or local deployment")
        if spec.deployment == "api":
            require_execution_lease(model_key, spec, execution_lease)
        self._require_loopback = spec.deployment == "local"
        self._base_url = (
            validate_local_compatible_endpoint()
            if self._require_loopback
            else _environment_base_url(require_loopback=False)
        )
        self.model_key = model_key
        self.model_id = spec.model_id
        self._client = client
        if client is not None:
            self._validate_client_endpoint(client)

    def _validate_client_endpoint(self, client: object) -> None:
        raw_base_url = getattr(client, "base_url", None)
        if raw_base_url is None:
            raise RuntimeError("injected OpenAI-compatible client must expose base_url")
        client_base_url = _parse_base_url(
            str(raw_base_url),
            require_loopback=self._require_loopback,
        )
        if client_base_url != self._base_url:
            raise RuntimeError(
                "OpenAI-compatible client endpoint differs from the validated endpoint"
            )

    def _get_client(self):
        current_base_url = (
            validate_local_compatible_endpoint()
            if self._require_loopback
            else _environment_base_url(require_loopback=False)
        )
        if current_base_url != self._base_url:
            raise RuntimeError(
                "OPENAI_COMPATIBLE_BASE_URL changed after adapter construction"
            )
        if self._client is None:
            try:
                from openai import OpenAI

                self._client = OpenAI(
                    base_url=current_base_url,
                    api_key=os.environ.get("OPENAI_COMPATIBLE_API_KEY", "none"),
                    max_retries=0,
                )
            except Exception as error:
                raise sanitized_provider_error("openai_compatible", error) from None
        self._validate_client_endpoint(self._client)
        return self._client

    def complete(
        self, system: str, user: str, *, temperature: float, seed: int, max_tokens: int
    ) -> ChatResponse:
        client = self._get_client()
        try:
            resp = client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                seed=seed,
            )
        except Exception as error:
            raise sanitized_provider_error("openai_compatible", error) from None

        choices = getattr(resp, "choices", None)
        if not isinstance(choices, (list, tuple)) or not choices:
            raise quarantine_provider_response("openai_compatible", "missing choices")
        choice = choices[0]
        text = getattr(getattr(choice, "message", None), "content", None)
        if not isinstance(text, str) or not text:
            raise quarantine_provider_response("openai_compatible", "missing text output")
        resolved_model = getattr(resp, "model", "")
        if not isinstance(resolved_model, str):
            resolved_model = ""
        if resolved_model and resolved_model != self.model_id:
            raise quarantine_provider_response(
                "openai_compatible", "model resolution drift"
            )
        response_id = getattr(resp, "id", "")
        if not isinstance(response_id, str):
            response_id = ""
        provider_request_id = getattr(resp, "_request_id", "")
        if not isinstance(provider_request_id, str):
            provider_request_id = ""
        finish_reason = getattr(choice, "finish_reason", "")
        if not isinstance(finish_reason, str):
            finish_reason = ""

        usage = getattr(resp, "usage", None)
        usage_reported = usage is not None
        if usage_reported:
            input_tokens = getattr(usage, "prompt_tokens", None)
            output_tokens = getattr(usage, "completion_tokens", None)
            total_tokens = getattr(usage, "total_tokens", 0)
            if not isinstance(input_tokens, int) or input_tokens < 0:
                raise quarantine_provider_response(
                    "openai_compatible", "invalid input usage"
                )
            if not isinstance(output_tokens, int) or output_tokens < 0:
                raise quarantine_provider_response(
                    "openai_compatible", "invalid output usage"
                )
            if not isinstance(total_tokens, int) or total_tokens < 0:
                raise quarantine_provider_response(
                    "openai_compatible", "invalid total usage"
                )
        else:
            input_tokens = output_tokens = total_tokens = 0
        return ChatResponse(
            text=text,
            provider="openai_compatible",
            requested_model_id=self.model_id,
            resolved_model_id=resolved_model,
            provider_request_id=provider_request_id,
            provider_response_id=response_id,
            sdk_name="openai",
            sdk_version=version("openai"),
            api_endpoint=_chat_endpoint(self._base_url),
            finish_reason=finish_reason,
            usage_reported=usage_reported,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            request_id=response_id,
            visible_output_tokens=output_tokens,
        )
