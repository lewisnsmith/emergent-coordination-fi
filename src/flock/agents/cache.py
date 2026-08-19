"""Integrity-checked, execution-namespaced LLM response cache."""

from __future__ import annotations

import fcntl
import json
import os
import threading
from dataclasses import asdict, fields
from pathlib import Path
from typing import Literal, Self

from pydantic import model_validator

from flock.agents.providers.base import ChatResponse
from flock.control.models import Sha256, StrictFrozenModel, canonical_sha256

CACHE_ROOT = Path(".flock-cache") / "llm"
_ZERO_SHA256 = "0" * 64
_RESPONSE_FIELDS = {field.name for field in fields(ChatResponse)}


class CacheIntegrityError(RuntimeError):
    """A cache entry or namespace does not match its authenticated content."""


class CacheContextV1(StrictFrozenModel):
    """Execution identity that prevents evidence and split namespaces crossing."""

    schema_version: Literal[1] = 1
    execution_class: Literal["mock", "local", "fake_provider", "provider"]
    analysis_role: Literal["rehearsal", "discovery", "confirmatory"]
    split_role: Literal["not_applicable", "train", "test"]
    execution_fingerprint_sha256: Sha256
    provider_contract_sha256: Sha256
    split_registry_sha256: Sha256
    dataset_sha256: Sha256

    @model_validator(mode="after")
    def validate_namespace(self) -> Self:
        provider_backed = self.execution_class in {"fake_provider", "provider"}
        if provider_backed and self.provider_contract_sha256 == _ZERO_SHA256:
            raise ValueError("provider-backed caches require a provider contract hash")
        if self.analysis_role == "confirmatory" and self.split_role != "test":
            raise ValueError("confirmatory caches must use the held-out test split")
        if self.split_role in {"train", "test"}:
            if self.split_registry_sha256 == _ZERO_SHA256:
                raise ValueError("train/test caches require a split registry hash")
        elif self.split_registry_sha256 != _ZERO_SHA256:
            raise ValueError("a split registry hash requires an explicit train/test role")
        return self

    @property
    def namespace(self) -> Path:
        return Path(
            self.execution_class,
            self.analysis_role,
            self.split_role,
            self.sha256(),
        )


class ResponseCache:
    """Store full response envelopes under a hash-bound execution namespace."""

    def __init__(self, root: Path, context: CacheContextV1):
        self.root = root
        self.context = context

    def key(
        self,
        model_key: str,
        model_id: str,
        temperature: float,
        seed: int,
        max_tokens: int,
        system: str,
        user: str,
    ) -> str:
        return canonical_sha256(
            {
                "schema_version": 2,
                "cache_context_sha256": self.context.sha256(),
                "model_key": model_key,
                "model_id": model_id,
                "temperature": temperature,
                "seed": seed,
                "max_tokens": max_tokens,
                "system": system,
                "user": user,
            }
        )

    def _path(self, key: str) -> Path:
        if len(key) != 64 or any(character not in "0123456789abcdef" for character in key):
            raise CacheIntegrityError("cache key must be a lowercase SHA-256 digest")
        return self.root / self.context.namespace / key[:2] / f"{key}.json"

    def _decode(self, key: str, payload: object) -> tuple[ChatResponse, str]:
        if not isinstance(payload, dict) or set(payload) != {
            "schema_version",
            "key",
            "cache_context_sha256",
            "response",
            "response_sha256",
            "entry_sha256",
        }:
            raise CacheIntegrityError("cache entry has an invalid schema")
        if payload.get("schema_version") != 2 or payload.get("key") != key:
            raise CacheIntegrityError("cache entry key or schema does not match")
        if payload.get("cache_context_sha256") != self.context.sha256():
            raise CacheIntegrityError("cache entry belongs to another execution namespace")
        response_payload = payload.get("response")
        if not isinstance(response_payload, dict) or set(response_payload) != _RESPONSE_FIELDS:
            raise CacheIntegrityError("cache response envelope is incomplete")
        try:
            response_sha256 = canonical_sha256(response_payload)
            unsigned = {name: value for name, value in payload.items() if name != "entry_sha256"}
            entry_sha256 = canonical_sha256(unsigned)
        except (TypeError, ValueError) as error:
            raise CacheIntegrityError("cache entry is not canonical JSON") from error
        if payload.get("response_sha256") != response_sha256:
            raise CacheIntegrityError("cache response hash does not match")
        if payload.get("entry_sha256") != entry_sha256:
            raise CacheIntegrityError("cache entry hash does not match")
        normalized = dict(response_payload)
        normalized["omitted_parameters"] = tuple(normalized["omitted_parameters"])
        normalized["retry_errors"] = tuple(normalized["retry_errors"])
        try:
            response = ChatResponse(**normalized)
        except (TypeError, ValueError) as error:
            raise CacheIntegrityError("cache response envelope is invalid") from error
        return response, response_sha256

    def get(self, key: str) -> ChatResponse | None:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise CacheIntegrityError("cache entry cannot be read") from error
        response, _ = self._decode(key, payload)
        return response

    def put(self, key: str, response: ChatResponse) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        response_payload = asdict(response)
        response_sha256 = canonical_sha256(response_payload)
        unsigned = {
            "schema_version": 2,
            "key": key,
            "cache_context_sha256": self.context.sha256(),
            "response": response_payload,
            "response_sha256": response_sha256,
        }
        payload = {**unsigned, "entry_sha256": canonical_sha256(unsigned)}
        lock_path = path.with_suffix(".lock")
        with lock_path.open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            if path.exists():
                existing = self.get(key)
                if existing is None:  # pragma: no cover - protected by the exclusive lock
                    raise CacheIntegrityError("cache entry disappeared while locked")
                existing_sha256 = canonical_sha256(asdict(existing))
                if existing_sha256 != response_sha256 or existing != response:
                    raise CacheIntegrityError(
                        "the same request key produced a different response envelope"
                    )
                return
            temporary = path.with_suffix(
                f".{os.getpid()}.{threading.get_ident()}.tmp"
            )
            try:
                with temporary.open("x", encoding="utf-8") as stream:
                    stream.write(
                        json.dumps(
                            payload,
                            sort_keys=True,
                            separators=(",", ":"),
                            ensure_ascii=False,
                            allow_nan=False,
                        )
                    )
                    stream.flush()
                    os.fsync(stream.fileno())
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
