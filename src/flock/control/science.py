"""Machine-readable scientific contracts for controlled experiment promotion."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, StringConstraints, model_validator

from flock.control.models import Identifier, Sha256, StrictFrozenModel

GitObjectId = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")]

_REGISTERED_H1 = {
    "H1.delta_tech": {
        "llm_homogeneous": 0.5,
        "classical_homogeneous": -0.5,
        "llm_heterogeneous": 0.5,
        "classical_heterogeneous": -0.5,
    },
    "H1.delta_int": {
        "llm_homogeneous": 1.0,
        "llm_heterogeneous": -1.0,
        "classical_homogeneous": -1.0,
        "classical_heterogeneous": 1.0,
    },
}

_SOURCE_PATHS = {
    "scope_sha256": Path("docs/research/research-scope-outcomes-and-evidence.md"),
    "methods_sha256": Path("docs/research/experimental-methods-and-statistical-analysis.md"),
    "preregistration_sha256": Path("docs/research/preregistration.md"),
}


class ContrastCoefficientV1(StrictFrozenModel):
    cell: Identifier
    coefficient: Annotated[float, Field(allow_inf_nan=False)]


class EstimandLockV1(StrictFrozenModel):
    estimand_id: Identifier
    hypothesis_id: Annotated[str, Field(pattern=r"^H(?:[1-9]|1[0-3]|2b)$")]
    outcome: str
    orientation: Literal[
        "linear_contrast",
        "same_minus_different",
        "same_model_minus_cross_provider",
    ]
    coefficients: tuple[ContrastCoefficientV1, ...] = ()
    independent_unit: str
    inference_role: Literal["confirmatory", "sensitivity_only", "descriptive"]
    primary_model: str | None = None
    direction: Literal["positive", "negative", "two_sided"] | None = None
    null_value: Annotated[float, Field(allow_inf_nan=False)] | None = None
    sesoi: Annotated[float, Field(gt=0, allow_inf_nan=False)] | None = None
    interval_rule: str | None = None
    missingness_rule: str | None = None
    multiplicity_order: Annotated[int, Field(ge=1)] | None = None
    required_cube_edges: Annotated[int, Field(ge=0)] = 0
    claim_template: str

    @model_validator(mode="after")
    def validate_estimand(self) -> Self:
        cells = [item.cell for item in self.coefficients]
        if len(cells) != len(set(cells)):
            raise ValueError("contrast coefficient cells must be unique")
        if self.orientation == "linear_contrast":
            if not self.coefficients:
                raise ValueError("linear contrasts require coefficients")
            if abs(sum(item.coefficient for item in self.coefficients)) > 1e-12:
                raise ValueError("linear contrast coefficients must sum to zero")
        elif self.coefficients:
            raise ValueError("only linear contrasts may include explicit coefficients")
        if self.orientation == "same_minus_different" and self.required_cube_edges != 80:
            raise ValueError("MPHIQ same-minus-different estimands require exactly 80 edges")
        if self.inference_role != "confirmatory" and self.multiplicity_order is not None:
            raise ValueError("only confirmatory estimands may enter the ordered family")
        return self


class PreregistrationReceiptV1(StrictFrozenModel):
    frozen_commit: GitObjectId | None = None
    git_tag: str | None = None
    registration_id: str | None = None
    receipt_sha256: Sha256 | None = None

    @property
    def complete(self) -> bool:
        return all(
            value is not None
            for value in (
                self.frozen_commit,
                self.git_tag,
                self.registration_id,
                self.receipt_sha256,
            )
        )


class ScienceLockV1(StrictFrozenModel):
    schema_version: Literal[1] = 1
    study_id: Identifier
    status: Literal["draft", "frozen"]
    scope_sha256: Sha256
    methods_sha256: Sha256
    preregistration_sha256: Sha256
    estimands: tuple[EstimandLockV1, ...] = Field(min_length=1)
    multiplicity_method: Literal["Holm-Bonferroni"]
    exclusion_rule: str
    split_rule: str
    blockers: tuple[str, ...] = ()
    preregistration_receipt: PreregistrationReceiptV1

    @model_validator(mode="after")
    def validate_lock(self) -> Self:
        identifiers = [item.estimand_id for item in self.estimands]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("science-lock estimand IDs must be unique")
        by_id = {item.estimand_id: item for item in self.estimands}
        for estimand_id, expected in _REGISTERED_H1.items():
            estimand = by_id.get(estimand_id)
            actual = (
                {item.cell: item.coefficient for item in estimand.coefficients}
                if estimand is not None
                else None
            )
            if actual != expected:
                raise ValueError(f"{estimand_id} differs from the registered contrast")
        sign_flip = by_id.get("H1.sign_flip_sensitivity")
        if sign_flip is None or sign_flip.inference_role != "sensitivity_only":
            raise ValueError("H1 sign flips must remain sensitivity-only")
        h4 = by_id.get("H4.mphiq_component")
        if (
            h4 is None
            or h4.orientation != "same_minus_different"
            or h4.required_cube_edges != 80
        ):
            raise ValueError("H4 must remain same-minus-different over all 80 cube edges")
        ordered = sorted(
            item.multiplicity_order
            for item in self.estimands
            if item.multiplicity_order is not None
        )
        if ordered and ordered != list(range(1, len(ordered) + 1)):
            raise ValueError("multiplicity order must be unique and contiguous")
        if self.status == "frozen":
            incomplete = [
                item.estimand_id
                for item in self.estimands
                if item.inference_role == "confirmatory"
                and any(
                    value is None
                    for value in (
                        item.primary_model,
                        item.direction,
                        item.null_value,
                        item.sesoi,
                        item.interval_rule,
                        item.missingness_rule,
                        item.multiplicity_order,
                    )
                )
            ]
            if incomplete:
                raise ValueError(f"frozen confirmatory estimands are incomplete: {incomplete}")
            if self.blockers:
                raise ValueError("a frozen science lock cannot retain blockers")
            if not self.preregistration_receipt.complete:
                raise ValueError(
                    "a frozen science lock requires immutable preregistration receipts"
                )
        return self

    @property
    def confirmatory_ready(self) -> bool:
        return (
            self.status == "frozen"
            and not self.blockers
            and self.preregistration_receipt.complete
        )

    def contrast(self, estimand_id: str, values: dict[str, float]) -> float:
        estimand = next(
            (item for item in self.estimands if item.estimand_id == estimand_id), None
        )
        if estimand is None:
            raise KeyError(f"unknown estimand {estimand_id!r}")
        if estimand.orientation != "linear_contrast":
            raise ValueError("only explicit linear contrasts can be evaluated directly")
        expected = {item.cell for item in estimand.coefficients}
        if set(values) != expected:
            raise ValueError("contrast values must exactly match the locked cells")
        return sum(item.coefficient * values[item.cell] for item in estimand.coefficients)


def load_science_lock(
    path: Path = Path("configs/control/science-lock.json"),
    *,
    repo_root: Path = Path("."),
    verify_sources: bool = True,
) -> ScienceLockV1:
    lock = ScienceLockV1.model_validate_json(path.read_text(encoding="utf-8"))
    if verify_sources:
        for field, relative_path in _SOURCE_PATHS.items():
            source = repo_root / relative_path
            try:
                actual = hashlib.sha256(source.read_bytes()).hexdigest()
            except OSError as error:
                raise ValueError(f"science-lock source is unavailable: {relative_path}") from error
            if actual != getattr(lock, field):
                raise ValueError(f"science-lock source hash drift: {relative_path}")
    return lock
