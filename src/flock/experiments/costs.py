"""Pre-run API and VM credit estimator with explicit uncertainty ranges."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field


class TokenCase(BaseModel):
    input_tokens: int
    output_tokens: int
    retry_rate: float = 0.0


class EffectiveRate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    effective_from: date
    input_per_million_usd: float
    output_per_million_usd: float


class APIPrice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_per_million_usd: float
    output_per_million_usd: float
    batch_discount: float = 0.0
    cached_input_per_million_usd: float | None = None
    cache_write_multiplier: float = 1.0
    future_rates: list[EffectiveRate] = Field(default_factory=list)
    source: str
    verified_on: str

    def rates_on(self, on_date: date) -> tuple[float, float]:
        input_rate = self.input_per_million_usd
        output_rate = self.output_per_million_usd
        for rate in sorted(self.future_rates, key=lambda item: item.effective_from):
            if rate.effective_from <= on_date:
                input_rate = rate.input_per_million_usd
                output_rate = rate.output_per_million_usd
        return input_rate, output_rate


class VMPrice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hourly_usd: float
    gpu_count: int
    gpu_type: str
    source: str
    verified_on: str


class PricingCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    api: dict[str, APIPrice]
    vm: dict[str, VMPrice]


class Workload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    calls: int
    model_mix: dict[str, float]
    token_cases: dict[str, TokenCase]
    local_gpu_hours: dict[str, float] = Field(default_factory=dict)
    storage_usd: float = 0.0
    contingency: float = 0.2


class CreditEnvelope(BaseModel):
    api: float
    gpu_vm: float
    cpu_storage: float
    total: float


class BudgetScenario(BaseModel):
    description: str
    total_calls: int
    selected_token_case: str
    retry_rate: float
    estimated_standard_api_usd: dict[str, float]
    recommended_credit_envelope_usd: CreditEnvelope


class RunMatrix(BaseModel):
    scenarios: dict[str, BudgetScenario]


def load_run_matrix(path: Path = Path("configs/budgets/run-matrix.yaml")) -> RunMatrix:
    with path.open() as f:
        return RunMatrix.model_validate(yaml.safe_load(f))


@dataclass(frozen=True)
class CostRange:
    calls: int
    low_api_usd: float
    expected_api_usd: float
    high_api_usd: float
    vm_usd: float
    storage_usd: float
    contingency: float
    total_low_usd: float
    total_expected_usd: float
    total_high_usd: float
    pricing_version: str
    priced_on: str


def load_pricing(path: Path = Path("configs/budgets/pricing.yaml")) -> PricingCatalog:
    with path.open() as f:
        return PricingCatalog.model_validate(yaml.safe_load(f))


def load_workload(
    path: Path = Path("configs/budgets/run-matrix.yaml"), scenario: str = "pilot"
) -> Workload:
    """Load a calculable workload, refusing legacy hard-coded summaries.

    The committed run matrix predates the executable study compiler and does
    not declare a model mix. It must not be silently interpreted as a real
    estimate. A workload-shaped YAML remains supported for focused use.
    """
    with path.open() as f:
        payload = yaml.safe_load(f)
    if "scenarios" in payload:
        raise ValueError(
            f"scenario {scenario!r} is a legacy summary, not a calculable workload; "
            "compile a study plan first"
        )
    return Workload.model_validate(payload)


def estimate_costs(
    workload: Workload, pricing: PricingCatalog, as_of: date | None = None
) -> CostRange:
    as_of = as_of or date.today()
    if set(workload.token_cases) != {"low", "expected", "high"}:
        raise ValueError("token_cases must contain exactly low, expected, and high")
    weight_total = sum(workload.model_mix.values())
    if abs(weight_total - 1.0) > 1e-9:
        raise ValueError(f"model_mix weights must sum to 1 (got {weight_total})")
    missing = set(workload.model_mix) - set(pricing.api)
    if missing:
        raise ValueError(f"models have no verified API price: {sorted(missing)}")
    missing_vm = set(workload.local_gpu_hours) - set(pricing.vm)
    if missing_vm:
        raise ValueError(f"VM shapes have no verified price: {sorted(missing_vm)}")

    def api_total(case_name: str) -> float:
        case = workload.token_cases[case_name]
        calls = workload.calls * (1 + case.retry_rate)
        total = 0.0
        for model, weight in workload.model_mix.items():
            price = pricing.api[model]
            input_rate, output_rate = price.rates_on(as_of)
            discount_factor = 1 - price.batch_discount
            total += calls * weight * discount_factor * (
                case.input_tokens * input_rate
                + case.output_tokens * output_rate
            ) / 1_000_000
        return total

    api = {name: api_total(name) for name in ("low", "expected", "high")}
    vm = sum(
        hours * pricing.vm[shape].hourly_usd
        for shape, hours in workload.local_gpu_hours.items()
    )
    multiplier = 1 + workload.contingency

    def total(api_cost: float) -> float:
        return (api_cost + vm + workload.storage_usd) * multiplier

    return CostRange(
        calls=workload.calls,
        low_api_usd=api["low"],
        expected_api_usd=api["expected"],
        high_api_usd=api["high"],
        vm_usd=vm,
        storage_usd=workload.storage_usd,
        contingency=workload.contingency,
        total_low_usd=total(api["low"]),
        total_expected_usd=total(api["expected"]),
        total_high_usd=total(api["high"]),
        pricing_version=pricing.version,
        priced_on=as_of.isoformat(),
    )
