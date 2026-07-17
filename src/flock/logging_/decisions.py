"""Run output writers: decisions.jsonl, fills.parquet, portfolio.parquet,
manifest.json — the publishable decision-log dataset (docs/research/04)."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict
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
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._decisions_f = open(self.run_dir / "decisions.jsonl", "w")
        self._fill_rows: list[dict] = []
        self._portfolio_rows: list[dict] = []

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

    def log_fill(self, fill: Fill) -> None:
        self._fill_rows.append(asdict(fill))

    def log_portfolio(
        self, step: int, ts: str, agent_id: str, cohort: str,
        cash: float, equity: float, weights: dict[str, float],
    ) -> None:
        self._portfolio_rows.append(
            {
                "step": step,
                "ts": ts,
                "agent_id": agent_id,
                "cohort": cohort,
                "cash": cash,
                "equity": equity,
                "weights": json.dumps(weights),
            }
        )

    def finalize(self, manifest: dict) -> None:
        self._decisions_f.close()
        pd.DataFrame(self._fill_rows).to_parquet(self.run_dir / "fills.parquet", index=False)
        pd.DataFrame(self._portfolio_rows).to_parquet(
            self.run_dir / "portfolio.parquet", index=False
        )
        with open(self.run_dir / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2, default=str)


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
