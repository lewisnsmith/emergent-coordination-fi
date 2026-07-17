"""Load versioned task prompts and compose prompt-pressure treatments."""

from __future__ import annotations

from pathlib import Path

import yaml

PROMPT_DIR = Path("configs/prompts")


def _load(path: Path) -> dict:
    with path.open() as stream:
        return yaml.safe_load(stream)


def resolve_prompt(prompt_id: str, prompt_dir: Path = PROMPT_DIR) -> str:
    """Resolve a stable prompt ID; ``task-neutral-v1`` uses the legacy task frame."""
    if prompt_id == "task-neutral-v1":
        return ""
    catalog = _load(prompt_dir / "catalog.yaml")
    for item in catalog["semantic_paraphrases"]:
        if item["id"] == prompt_id:
            return item["text"].strip()
    for item in catalog["realistic_prompt_families"]["families"]:
        if item["id"] == prompt_id:
            return item["text"].strip()

    pressure = _load(prompt_dir / "pressure-treatments.yaml")
    cells = {cell["code"]: cell for cell in pressure["core_cells"]["cells"]}
    if prompt_id in cells:
        return _compose_pressure(pressure, cells[prompt_id])
    raise KeyError(f"unknown prompt id '{prompt_id}'")


def _compose_pressure(design: dict, cell: dict) -> str:
    factors = design["factors"]
    stakes = factors["stakes"]["levels"][cell["stakes"]]["text"]

    def boolean_text(factor: str, value: bool) -> str:
        levels = factors[factor]["levels"]
        return next(level["text"] for level in levels if level["value"] is value)

    return "\n\n".join(
        part.strip()
        for part in (
            design["invariant_safety_header"],
            design["composition"]["common_task"],
            stakes,
            boolean_text("urgency", cell["urgent"]),
            boolean_text("emotion", cell["distressed"]),
            boolean_text("forced_action", cell["forced_action"]),
        )
    )
