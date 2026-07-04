"""Content-addressed LLM response cache.

Key = sha256 over (model_key, model_id, temperature, seed, max_tokens, system,
user). Stored as small JSON files under .flock-cache/llm/ so published results
re-derive offline and repeated sweeps are free.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from flock.agents.providers.base import ChatResponse

CACHE_ROOT = Path(".flock-cache") / "llm"


class ResponseCache:
    def __init__(self, root: Path = CACHE_ROOT):
        self.root = root

    @staticmethod
    def key(
        model_key: str, model_id: str, temperature: float, seed: int, max_tokens: int,
        system: str, user: str,
    ) -> str:
        payload = json.dumps(
            [model_key, model_id, temperature, seed, max_tokens, system, user]
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def _path(self, key: str) -> Path:
        return self.root / key[:2] / f"{key}.json"

    def get(self, key: str) -> ChatResponse | None:
        p = self._path(key)
        if not p.exists():
            return None
        with open(p) as f:
            return ChatResponse(**json.load(f))

    def put(self, key: str, response: ChatResponse) -> None:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w") as f:
            json.dump(asdict(response), f)
