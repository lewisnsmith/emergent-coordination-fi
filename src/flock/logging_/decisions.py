"""Atomic run outputs, including decisions, fills, portfolios, and market events."""

from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from flock.core.types import Decision, Fill, Observation

RESULTS_DIR = Path("results")


def git_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5
        )
        return out.stdout.strip() or "unknown"
    except OSError:
        return "unknown"


class RunWriter:
    def __init__(self, run_id: str, results_root: Path = RESULTS_DIR):
        self.run_id = run_id
        self.run_dir = results_root / run_id
        if (self.run_dir / "manifest.json").exists():
            raise FileExistsError(f"completed run already exists: {self.run_dir}")
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        self.attempt_id = f"{timestamp}-{uuid.uuid4().hex[:8]}"
        self.work_dir = results_root / ".incomplete" / run_id / self.attempt_id
        self.work_dir.mkdir(parents=True, exist_ok=False)
        self._decisions_f = open(self.work_dir / "decisions.jsonl", "x")
        self._fills_f = open(self.work_dir / "fills.jsonl", "x")
        self._portfolio_f = open(self.work_dir / "portfolio.jsonl", "x")
        self._market_events_f = open(self.work_dir / "market_events.jsonl", "x")
        self._fill_rows: list[dict] = []
        self._portfolio_rows: list[dict] = []
        self._decision_rows = 0
        self._market_event_rows = 0
        self._closed = False

    def log_decision(
        self,
        decision: Decision,
        obs: Observation,
        agent_meta: dict,
        cohort: str,
        clipped_orders: tuple,
    ) -> None:
        record = {
            "run_id": self.run_id,
            "step": decision.step,
            "ts": obs.ts,
            "agent_id": decision.agent_id,
            "cohort": cohort,
            **agent_meta,
            "observation_digest": hashlib.sha256(obs.digest_payload().encode()).hexdigest(),
            "prompt_hash": decision.prompt_hash,
            "raw_response_hash": decision.raw_response_hash,
            "symbols": list(obs.symbols),
            "action": decision.action,
            "orders": [asdict(o) for o in decision.orders],
            "orders_clipped": [asdict(o) for o in clipped_orders],
            "rationale": decision.rationale,
            "parse_ok": decision.parse_ok,
            "evidence_refs": list(decision.evidence_refs),
            "confidence": decision.confidence,
            "uncertainties": list(decision.uncertainties),
            "grounding_ok": decision.grounding_ok,
            "grounding_failures": list(decision.grounding_failures),
            "usage": asdict(decision.usage),
            "latency_s": round(decision.latency_s, 4),
        }
        self._decisions_f.write(json.dumps(record) + "\n")
        self._decisions_f.flush()
        self._decision_rows += 1

    def log_fill(self, fill: Fill) -> None:
        record = asdict(fill)
        self._fill_rows.append(record)
        self._fills_f.write(json.dumps(record) + "\n")
        self._fills_f.flush()

    def log_market_event(self, event: dict) -> None:
        record = {"run_id": self.run_id, **event}
        self._market_events_f.write(json.dumps(record, default=str) + "\n")
        self._market_events_f.flush()
        self._market_event_rows += 1

    def log_portfolio(
        self, step: int, ts: str, agent_id: str, cohort: str,
        cash: float, equity: float, weights: dict[str, float],
    ) -> None:
        record = {
            "step": step,
            "ts": ts,
            "agent_id": agent_id,
            "cohort": cohort,
            "cash": cash,
            "equity": equity,
            "weights": json.dumps(weights),
        }
        self._portfolio_rows.append(record)
        self._portfolio_f.write(json.dumps(record) + "\n")
        self._portfolio_f.flush()

    @staticmethod
    def _atomic_json(path: Path, payload: dict) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, default=str) + "\n")
        temporary.replace(path)

    def checkpoint(self, completed_steps: int, total_cost_usd: float) -> None:
        self._atomic_json(
            self.work_dir / "checkpoint.json",
            {
                "run_id": self.run_id,
                "attempt_id": self.attempt_id,
                "completed_steps": completed_steps,
                "decision_rows": self._decision_rows,
                "fill_rows": len(self._fill_rows),
                "portfolio_rows": len(self._portfolio_rows),
                "market_event_rows": self._market_event_rows,
                "total_cost_usd": total_cost_usd,
            },
        )

    def _close(self) -> None:
        if self._closed:
            return
        self._decisions_f.close()
        self._fills_f.close()
        self._portfolio_f.close()
        self._market_events_f.close()
        self._closed = True

    def fail(self, error: BaseException) -> None:
        self._close()
        self._atomic_json(
            self.work_dir / "failure.json",
            {
                "run_id": self.run_id,
                "attempt_id": self.attempt_id,
                "status": "failed",
                "error_type": type(error).__name__,
                "error": str(error)[:500],
                "failed_at": datetime.now(UTC).isoformat(),
            },
        )

    def finalize(self, manifest: dict) -> None:
        self._close()
        pd.DataFrame(self._fill_rows).to_parquet(self.work_dir / "fills.parquet", index=False)
        pd.DataFrame(self._portfolio_rows).to_parquet(
            self.work_dir / "portfolio.parquet", index=False
        )
        manifest = {**manifest, "attempt_id": self.attempt_id, "status": "complete"}
        self._atomic_json(self.work_dir / "manifest.json", manifest)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        for name in (
            "decisions.jsonl",
            "fills.parquet",
            "portfolio.parquet",
            "market_events.jsonl",
        ):
            (self.work_dir / name).replace(self.run_dir / name)
        (self.work_dir / "manifest.json").replace(self.run_dir / "manifest.json")


def resolve_run_dir(run_id: str, results_root: Path = RESULTS_DIR) -> Path:
    """Resolve a run id (or 'latest') to its results directory."""
    if run_id != "latest":
        d = results_root / run_id
        if not d.exists():
            raise FileNotFoundError(f"no run directory {d}")
        return d
    candidates = [d for d in results_root.iterdir() if (d / "manifest.json").exists()]
    if not candidates:
        raise FileNotFoundError("no completed runs under results/")
    return max(candidates, key=lambda d: (d / "manifest.json").stat().st_mtime)
