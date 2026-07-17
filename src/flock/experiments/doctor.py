"""Read-only environment and endpoint preflight for paid studies."""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Literal
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ConfigDict

from flock.data.registry import Registry
from flock.experiments.costs import load_pricing
from flock.experiments.study import compile_study, load_study_spec


class DoctorCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    status: Literal["pass", "warn", "fail"]
    detail: str


class DoctorReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ok: bool
    live: bool
    checks: tuple[DoctorCheck, ...]


_PROVIDER_ENV = {
    "anthropic": ("ANTHROPIC_API_KEY",),
    "openai": ("OPENAI_API_KEY",),
    "google": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
}
_PROVIDER_SDK = {"anthropic": "anthropic", "openai": "openai", "google": "google.genai"}


def _credential_name(provider: str) -> str | None:
    return next((name for name in _PROVIDER_ENV[provider] if os.getenv(name)), None)


def _sdk_present(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:
        return False


def _probe_model(provider: str, model_id: str, credential_name: str, timeout_s: float) -> str:
    """Make one bounded metadata GET; never submit a generation request."""
    key = os.environ[credential_name]
    encoded_model = quote(model_id, safe="")
    if provider == "openai":
        url = f"https://api.openai.com/v1/models/{encoded_model}"
        headers = {"Authorization": f"Bearer {key}"}
        params = None
    elif provider == "anthropic":
        url = f"https://api.anthropic.com/v1/models/{encoded_model}"
        headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
        params = None
    elif provider == "google":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{encoded_model}"
        headers = {}
        params = {"key": key}
    else:  # pragma: no cover - guarded by caller
        raise ValueError(f"unsupported live provider {provider}")
    response = httpx.get(url, headers=headers, params=params, timeout=timeout_s)
    response.raise_for_status()
    payload = response.json()
    return str(payload.get("id") or payload.get("name") or model_id)


def _dataless_path(root: Path) -> str | None:
    if sys.platform != "darwin":
        return None
    result = subprocess.run(
        [
            "find",
            str(root),
            "(",
            "-path",
            str(root / ".git"),
            "-o",
            "-path",
            str(root / ".pytest_cache"),
            "-o",
            "-path",
            str(root / ".ruff_cache"),
            ")",
            "-prune",
            "-o",
            "-flags",
            "+dataless",
            "-print",
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    for raw_path in result.stdout.splitlines():
        path = Path(raw_path)
        if "__pycache__" in path.parts:
            continue
        try:
            if path.stat().st_size > 0:
                return raw_path
        except FileNotFoundError:
            continue
    return None


def run_doctor(root: Path = Path("."), *, live: bool = False, timeout_s: float = 5) -> DoctorReport:
    """Check local readiness; live mode performs metadata-only endpoint probes."""
    root = root.resolve()
    checks: list[DoctorCheck] = []
    try:
        pricing = load_pricing(root / "configs/budgets/pricing.yaml")
        plan = compile_study(
            load_study_spec(root / "configs/studies/paper-core.yaml"), pricing=pricing
        )
        checks.append(DoctorCheck(name="study", status="pass", detail=plan.plan_hash))
    except (OSError, ValueError) as error:
        plan = None
        checks.append(DoctorCheck(name="study", status="fail", detail=str(error)))

    try:
        pricing = load_pricing(root / "configs/budgets/pricing.yaml")
        oldest = min(
            date.fromisoformat(price.verified_on)
            for price in (*pricing.api.values(), *pricing.vm.values())
        )
        age = (date.today() - oldest).days
        status = "pass" if age <= 30 else ("fail" if live else "warn")
        checks.append(
            DoctorCheck(
                name="pricing",
                status=status,
                detail=f"catalog {pricing.version}; oldest verification {age} days ago",
            )
        )
    except (OSError, ValueError) as error:
        checks.append(DoctorCheck(name="pricing", status="fail", detail=str(error)))

    registry = Registry(root / "datasets")
    for entry in registry.entries():
        errors = registry.verify(entry)
        status = "fail" if entry.files is not None and errors else ("warn" if errors else "pass")
        checks.append(
            DoctorCheck(
                name=f"dataset:{entry.name}",
                status=status,
                detail="; ".join(errors) if errors else f"bundle {entry.sha256}",
            )
        )

    free_gib = shutil.disk_usage(root).free / 1024**3
    checks.append(
        DoctorCheck(
            name="storage",
            status="pass" if free_gib >= 5 else "fail",
            detail=f"{free_gib:.1f} GiB free",
        )
    )
    dataless = _dataless_path(root)
    checks.append(
        DoctorCheck(
            name="icloud",
            status="fail" if dataless else "pass",
            detail=f"dataless path: {dataless}" if dataless else "no dataless path detected",
        )
    )

    for provider, module in _PROVIDER_SDK.items():
        sdk_present = _sdk_present(module)
        checks.append(
            DoctorCheck(
                name=f"sdk:{provider}",
                status="pass" if sdk_present else ("fail" if live else "warn"),
                detail="installed" if sdk_present else "install the providers extra",
            )
        )
        credential = _credential_name(provider)
        checks.append(
            DoctorCheck(
                name=f"credential:{provider}",
                status="pass" if credential else ("fail" if live else "warn"),
                detail=f"present via {credential}" if credential else "not present",
            )
        )

    if live and plan is not None:
        models = {
            (allocation.provider, allocation.model_id)
            for cohort in plan.source_spec.cohorts
            if cohort.technology == "llm"
            for allocation in cohort.allocations
        }
        for provider, model_id in sorted(models):
            credential = _credential_name(provider)
            if credential is None:
                continue
            try:
                resolved = _probe_model(provider, model_id, credential, timeout_s)
                checks.append(
                    DoctorCheck(
                        name=f"endpoint:{provider}:{model_id}",
                        status="pass",
                        detail=f"metadata resolved as {resolved}",
                    )
                )
            except (httpx.HTTPError, ValueError) as error:
                checks.append(
                    DoctorCheck(
                        name=f"endpoint:{provider}:{model_id}",
                        status="fail",
                        detail=f"metadata probe failed: {type(error).__name__}",
                    )
                )
        checks.append(
            DoctorCheck(
                name="quota",
                status="warn",
                detail="metadata probes do not prove throughput; run the capped provider canary",
            )
        )

    return DoctorReport(
        ok=not any(check.status == "fail" for check in checks),
        live=live,
        checks=tuple(checks),
    )
