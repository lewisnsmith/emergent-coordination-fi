import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from flock.analysis.crossed import analyze_first_paper_estimands
from flock.cli import app
from flock.core.config import ExperimentConfig
from flock.experiments.aggregate import (
    AGGREGATION_ARTIFACTS,
    _first_paper_assignments,
    _load_verified_runs,
    aggregate_study,
)
from flock.experiments.materialize import MaterializedStudy, materialize_study
from flock.experiments.study import compile_study_file
from flock.experiments.verify import RunVerification

MODELS = (
    ("model-a", "provider-one", "family-a"),
    ("model-b", "provider-one", "family-b"),
    ("model-c", "provider-two", "family-c"),
    ("model-d", "provider-three", "family-d"),
)
MODEL_BY_KEY = {f"key-{model}": model for model, _, _ in MODELS}
BASELINES = (
    ("momentum-v1", "momentum", "momentum"),
    ("buy-hold-v1", "buy_hold", "buy-hold"),
)
STEPS = 3


def _allocation(
    model_id: str,
    provider: str,
    family: str,
    count: int = 2,
) -> dict:
    return {
        "model_id": model_id,
        "revision": "mock-v1",
        "provider": provider,
        "family": family,
        "pricing_key": "mock-price" if provider == "mock" else None,
        "count": count,
    }


def _source_cohorts() -> list[dict]:
    llm_allocations = [
        _allocation(model, provider, family)
        for model, provider, family in MODELS
    ]
    classical_allocations = [
        _allocation(model, "classical", family)
        for model, _kind, family in BASELINES
    ]
    return [
        *[
            {
                "cohort_id": f"llm-homogeneous-{family}",
                "technology": "llm",
                "ecology": "homogeneous",
                "allocations": [allocation],
            }
            for allocation, (_model, _provider, family) in zip(
                llm_allocations, MODELS, strict=True
            )
        ],
        {
            "cohort_id": "llm-heterogeneous",
            "technology": "llm",
            "ecology": "heterogeneous",
            "allocations": llm_allocations,
        },
        *[
            {
                "cohort_id": f"classical-homogeneous-{family}",
                "technology": "classical",
                "ecology": "homogeneous",
                "allocations": [allocation],
            }
            for allocation, (_model, _kind, family) in zip(
                classical_allocations, BASELINES, strict=True
            )
        ],
        {
            "cohort_id": "classical-heterogeneous",
            "technology": "classical",
            "ecology": "heterogeneous",
            "allocations": classical_allocations,
        },
    ]


def _replay_config(name: str, block: str, cluster: str, seed: int) -> dict:
    cohorts = []
    for source in _source_cohorts():
        groups = []
        for allocation in source["allocations"]:
            if source["technology"] == "llm":
                groups.append(
                    {
                        "kind": "llm",
                        "count": allocation["count"],
                        "model": f"key-{allocation['model_id']}",
                        "persona": "neutral",
                        "grounding_mode": "strict",
                    }
                )
            else:
                kind = next(
                    kind
                    for model_id, kind, _family in BASELINES
                    if model_id == allocation["model_id"]
                )
                groups.append({"kind": kind, "count": allocation["count"]})
        cohorts.append({"name": source["cohort_id"], "agents": groups})
    return ExperimentConfig.model_validate(
        {
            "name": name,
            "seed": seed,
            "dataset": "mock-dataset",
            "market": {"kind": "replay", "fee_bps": 5, "slippage_bps": 2},
            "steps": STEPS,
            "observation_window": 1,
            "initial_cash": 1000,
            "initial_position_per_symbol": 0,
            "max_position_per_symbol": 100,
            "model_policy": "mock_only",
            "hypothesis_ids": ["H1", "H3"],
            "independent_block": block,
            "dependence_cluster": cluster,
            "trajectory_id": block,
            "window_start": "2026-01-01",
            "window_end": "2026-01-03",
            "cohorts": cohorts,
        }
    ).model_dump(mode="json")


def _mphiq_pairs() -> list[dict]:
    codes = [f"{value ^ (value >> 1):05b}" for value in range(32)]
    pairs = []
    for index, (left, right) in enumerate(
        zip(codes[:-1], codes[1:], strict=True), start=1
    ):
        changed = next(
            i
            for i, bits in enumerate(zip(left, right, strict=True))
            if len(set(bits)) == 2
        )
        different, same = (left, right) if left[changed] == "0" else (right, left)
        pairs.append(
            {
                "pair_id": f"mock-edge-{index:02d}",
                "factor": "MPHIQ"[changed],
                "different_code": different,
                "same_code": same,
                "assignment_seed": 8000 + index,
            }
        )
    return pairs


def _treatment_groups(code: str) -> list[dict]:
    vectors = {
        "M": [
            "model-a", "model-a", "model-b", "model-b",
            "model-c", "model-c", "model-d", "model-d",
        ],
        "P": ["p0", "p1", "p2", "p0", "p1", "p2", "p0", "p1"],
        "H": ["h0", "h0", "h1", "h1", "h0", "h1", "h1", "h0"],
        "I": ["i0", "i1", "i0", "i1", "i1", "i0", "i1", "i0"],
        "Q": ["q0", "q1", "q2", "q3", "q1", "q2", "q3", "q0"],
    }
    selected = {
        factor: ([values[0]] * 8 if bit == "1" else values)
        for factor, bit, values in zip("MPHIQ", code, vectors.values(), strict=True)
    }
    groups = []
    for index in range(8):
        model_id = selected["M"][index]
        profile = selected["P"][index]
        harness = selected["H"][index]
        information = selected["I"][index]
        prompt = selected["Q"][index]
        treatment = {
            "scheme_code": code,
            "agent_index": index,
            "model_id": model_id,
            "model_revision": "mock-v1",
            "model_registry_key": f"key-{model_id}",
            "profile_id": profile,
            "harness_id": harness,
            "harness_temperature": 0.1 if harness == "h0" else 0.9,
            "harness_memory": harness == "h1",
            "information_policy": information,
            "prompt_id": prompt,
            "prompt_semantic_group": "mock-semantic-group",
        }
        treatment["assignment_digest"] = hashlib.sha256(
            json.dumps(treatment, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        groups.append(
            {
                "kind": "llm",
                "count": 1,
                "model": f"key-{model_id}",
                "persona": profile,
                "temperature": treatment["harness_temperature"],
                "memory": treatment["harness_memory"],
                "harness_id": harness,
                "prompt_id": prompt,
                "information_policy": information,
                "grounding_mode": "strict",
                "mphiq_treatment": treatment,
            }
        )
    return groups


def _mphiq_config(name: str, block: str, cluster: str, seed: int, code: str) -> dict:
    return ExperimentConfig.model_validate(
        {
            "name": name,
            "seed": seed,
            "dataset": "mock-dataset",
            "market": {"kind": "replay", "fee_bps": 5, "slippage_bps": 2},
            "steps": STEPS,
            "observation_window": 1,
            "initial_cash": 1000,
            "initial_position_per_symbol": 0,
            "max_position_per_symbol": 100,
            "model_policy": "mock_only",
            "hypothesis_ids": ["H3", "H4"],
            "independent_block": block,
            "dependence_cluster": cluster,
            "trajectory_id": block,
            "window_start": "2026-01-01",
            "window_end": "2026-01-03",
            "cohorts": [{"name": "llm-heterogeneous", "agents": _treatment_groups(code)}],
        }
    ).model_dump(mode="json")


def _assignment(
    ordinal: int,
    *,
    block: str,
    cluster: str,
    seed: int,
    design: str,
    cell: dict,
    cohorts: list[dict],
    config: dict,
) -> dict:
    agents = sum(sum(item["count"] for item in cohort["allocations"]) for cohort in cohorts)
    calls = agents * STEPS
    return {
        "assignment_id": config["name"],
        "ordinal": ordinal,
        "study_id": "mock-aggregation-v1",
        "plan_hash": "a" * 64,
        "stage_id": "confirmatory-replay" if design == "replay" else "mphiq-factorial",
        "authorization_stage": "confirmatory",
        "design": design,
        "trajectory_id": block,
        "window_id": f"window-{block}",
        "dependence_cluster_id": cluster,
        "independent_unit": "market_window",
        "market_replica_id": None,
        "seed": seed,
        "cell": cell,
        "steps": STEPS,
        "calls_per_llm_agent_step": 1,
        "cohorts": cohorts,
        "exact_counts": {
            "runs": 1,
            "steps": STEPS,
            "agents_per_run": agents,
            "agent_steps": agents * STEPS,
            "calls": calls,
        },
        "calls_by_pricing_key": {"mock-price": calls},
        "stage_budget_cap": {"max_calls": 100000, "max_cost_usd": 1000.0},
        "model_revisions": {
            allocation["model_id"]: allocation["revision"]
            for cohort in cohorts
            for allocation in cohort["allocations"]
        },
        "execution_config": config,
        "execution_blockers": [],
    }


def _agents(config: dict) -> dict[str, dict]:
    agents = {}
    for cohort in config["cohorts"]:
        for group_index, group in enumerate(cohort["agents"]):
            for instance in range(group["count"]):
                label = group.get("model") or group["kind"]
                agent_id = f"{cohort['name']}--{label}--{group_index}-{instance}"
                meta = {"cohort": cohort["name"], "kind": group["kind"]}
                if group["kind"] == "llm":
                    meta["model"] = group["model"]
                    meta["model_id"] = MODEL_BY_KEY[group["model"]]
                    if group.get("mphiq_treatment") is not None:
                        meta["mphiq_treatment"] = group["mphiq_treatment"]
                agents[agent_id] = meta
    return agents


def _write_run(results_root: Path, assignment: dict) -> Path:
    run_id = f"run-{assignment['ordinal']:03d}"
    run_dir = results_root / run_id
    run_dir.mkdir(parents=True)
    config = assignment["execution_config"]
    agents = _agents(config)
    manifest = {
        "run_id": run_id,
        "status": "complete",
        "config": config,
        "config_hash": "config-hash",
        "resolved_config_hash": "resolved-hash",
        "git_sha": "abcdef1234567890",
        "dataset": {"name": "mock-dataset", "version": 1, "sha256": "d" * 64},
        "n_steps": STEPS,
        "n_agents": len(agents),
        "agents": agents,
        "total_cost_usd": 0.0,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, sort_keys=True))
    rows = []
    portfolios = []
    code = assignment["cell"].get("mphiq_code")
    code_shift = int(code, 2) if code is not None else 0
    for agent_index, (agent_id, meta) in enumerate(sorted(agents.items())):
        for step in range(STEPS):
            action = ("buy", "hold", "sell")[(agent_index + step + code_shift) % 3]
            row = {
                "agent_id": agent_id,
                "step": step,
                "cohort": meta["cohort"],
                "action": action,
                "parse_ok": True,
            }
            if "mphiq_treatment" in meta:
                row["mphiq_treatment"] = meta["mphiq_treatment"]
            rows.append(row)
            portfolios.append(
                {
                    "agent_id": agent_id,
                    "step": step,
                    "cohort": meta["cohort"],
                    "cash": 1000.0,
                    "equity": 1000.0,
                    "weights": json.dumps({"S": (agent_index + 1) / 100}),
                }
            )
    pd.DataFrame(rows).to_json(run_dir / "decisions.jsonl", orient="records", lines=True)
    pd.DataFrame(columns=["agent_id", "step"]).to_parquet(
        run_dir / "fills.parquet", index=False
    )
    pd.DataFrame(portfolios).to_parquet(run_dir / "portfolio.parquet", index=False)
    (run_dir / "market_events.jsonl").write_text("")
    return run_dir


def _write_bundle(root: Path) -> tuple[Path, Path, MaterializedStudy]:
    results_root = root / "results"
    results_root.mkdir()
    source_cohorts = _source_cohorts()
    mphiq_cohort = [
        cohort for cohort in source_cohorts if cohort["cohort_id"] == "llm-heterogeneous"
    ]
    pairs = _mphiq_pairs()
    assignments = []
    ordinal = 1
    for block_index in range(2):
        block = f"block-{block_index}"
        cluster = f"cluster-{block_index}"
        name = f"mock-replay-{block}"
        config = _replay_config(name, block, cluster, seed=2101)
        assignments.append(
            _assignment(
                ordinal,
                block=block,
                cluster=cluster,
                seed=2101,
                design="replay",
                cell={"cell_id": "default"},
                cohorts=source_cohorts,
                config=config,
            )
        )
        ordinal += 1
        for value in range(32):
            code = f"{value:05b}"
            name = f"mock-mphiq-{block}-{code}"
            config = _mphiq_config(name, block, cluster, seed=3101, code=code)
            assignments.append(
                _assignment(
                    ordinal,
                    block=block,
                    cluster=cluster,
                    seed=3101,
                    design="mphiq",
                    cell={
                        "cell_id": code,
                        "mphiq_code": code,
                        "mphiq_pairs": [
                            pair
                            for pair in pairs
                            if code in {pair["different_code"], pair["same_code"]}
                        ],
                    },
                    cohorts=mphiq_cohort,
                    config=config,
                )
            )
            ordinal += 1
    payload = {
        "schema_version": 1,
        "study_id": "mock-aggregation-v1",
        "plan_hash": "a" * 64,
        "assignments": assignments,
        "exact_runs": len(assignments),
        "exact_steps": sum(item["exact_counts"]["steps"] for item in assignments),
        "exact_agent_steps": sum(
            item["exact_counts"]["agent_steps"] for item in assignments
        ),
        "exact_calls": sum(item["exact_counts"]["calls"] for item in assignments),
        "executable_runs": len(assignments),
    }
    payload["materialization_hash"] = "pending"
    draft = MaterializedStudy.model_validate_json(json.dumps(payload))
    normalized_assignments = [
        item.model_dump(mode="json") for item in draft.assignments
    ]
    payload = draft.model_dump(mode="json")
    payload["materialization_hash"] = hashlib.sha256(
        json.dumps(
            normalized_assignments, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    materialized = MaterializedStudy.model_validate_json(json.dumps(payload))
    assignments_path = root / "assignments.json"
    assignments_path.write_text(json.dumps(payload, indent=2))
    for assignment in normalized_assignments:
        _write_run(results_root, assignment)
    return assignments_path, results_root, materialized


def _verified(ok: bool = True) -> RunVerification:
    return RunVerification(
        ok=ok,
        errors=[] if ok else ["parse-failure gate violated"],
        warnings=[],
        decisions=10,
        fills=0,
        portfolio_rows=10,
    )


def test_aggregate_study_is_byte_identical_and_bundle_compatible(tmp_path, monkeypatch):
    assignments, results_root, _materialized = _write_bundle(tmp_path)
    monkeypatch.setattr("flock.experiments.aggregate.verify_run", lambda _path: _verified())

    first = aggregate_study(assignments, tmp_path / "aggregate-a", results_root=results_root)
    second = aggregate_study(assignments, tmp_path / "aggregate-b", results_root=results_root)

    assert first.aggregation_hash == second.aggregation_hash
    for name in (*AGGREGATION_ARTIFACTS, "aggregation-manifest.json"):
        assert (first.output_dir / name).read_bytes() == (second.output_dir / name).read_bytes()
    manifest = json.loads((first.output_dir / "aggregation-manifest.json").read_text())
    assert manifest["evidence_kind"] == "mock"
    assert manifest["independent_blocks"] == ["block-0", "block-1"]
    assert len(manifest["source_run_ids"]) == 66

    crossed = pd.read_parquet(first.output_dir / "crossed_rows.parquet")
    lineage = pd.read_parquet(first.output_dir / "lineage_rows.parquet")
    mphiq = pd.read_parquet(first.output_dir / "mphiq_rows.parquet")
    assert set(crossed["metric"]) == {"kappa"}
    assert set(lineage["relationship"]) == {
        "same_model",
        "same_provider",
        "cross_provider",
    }
    assert set(mphiq["component"]) == set("MPHIQ")
    estimates = analyze_first_paper_estimands(
        crossed,
        confirmatory_metrics=["kappa"],
        lineage_rows=lineage,
        mphiq_rows=mphiq,
        n_bootstrap=10,
    )
    assert set(estimates.block_effects["independent_block"]) == {"block-0", "block-1"}

    monkeypatch.chdir(tmp_path)
    cli = CliRunner().invoke(
        app,
        ["aggregate-study", str(assignments), "--output", str(tmp_path / "aggregate-cli")],
    )
    assert cli.exit_code == 0, cli.output
    assert "66 verified runs" in cli.output


def test_aggregate_study_fails_closed_on_raw_run_violations(tmp_path, monkeypatch):
    assignments_path, results_root, materialized = _write_bundle(tmp_path)
    monkeypatch.setattr("flock.experiments.aggregate.verify_run", lambda _path: _verified())
    first = materialized.assignments[0]
    first_dir = next(
        path
        for path in results_root.iterdir()
        if json.loads((path / "manifest.json").read_text())["config"]["name"]
        == first.assignment_id
    )

    duplicate = results_root / "duplicate-run"
    shutil.copytree(first_dir, duplicate)
    with pytest.raises(ValueError, match="duplicate completed raw runs"):
        aggregate_study(
            assignments_path, tmp_path / "duplicate-output", results_root=results_root
        )
    shutil.rmtree(duplicate)

    manifest_path = first_dir / "manifest.json"
    hidden_manifest = first_dir / "manifest.hidden"
    manifest_path.rename(hidden_manifest)
    with pytest.raises(ValueError, match="missing completed raw run"):
        aggregate_study(
            assignments_path, tmp_path / "missing-output", results_root=results_root
        )
    hidden_manifest.rename(manifest_path)

    monkeypatch.setattr(
        "flock.experiments.aggregate.verify_run", lambda _path: _verified(ok=False)
    )
    with pytest.raises(ValueError, match="parse-failure gate violated"):
        aggregate_study(
            assignments_path, tmp_path / "parse-output", results_root=results_root
        )


def test_aggregate_study_rejects_mixed_evidence_and_pseudoreplication(
    tmp_path, monkeypatch
):
    _assignments_path, results_root, materialized = _write_bundle(tmp_path)
    monkeypatch.setattr("flock.experiments.aggregate.verify_run", lambda _path: _verified())
    replay, _mphiq, _identities = _first_paper_assignments(materialized)
    real_assignment = replay[0]
    real_config = dict(real_assignment.execution_config or {})
    real_config["model_policy"] = "frontier_only"
    real_config["runtime_budget"] = {
        "max_requests": 1000,
        "max_input_tokens": 100000,
        "max_output_tokens": 100000,
        "max_cost_usd": 1000.0,
        "request_cost_reserve_usd": 1.0,
    }
    real_assignment = real_assignment.model_copy(
        update={"execution_config": real_config}
    )
    real_dir = next(
        path
        for path in results_root.iterdir()
        if json.loads((path / "manifest.json").read_text())["config"]["name"]
        == real_assignment.assignment_id
    )
    real_manifest = json.loads((real_dir / "manifest.json").read_text())
    real_manifest["config"] = real_config
    (real_dir / "manifest.json").write_text(json.dumps(real_manifest))
    with pytest.raises(ValueError, match="cannot mix mock and real evidence"):
        _load_verified_runs([real_assignment, replay[1]], results_root)

    assignments = list(materialized.assignments)
    collision = next(item for item in assignments if item.trajectory_id == "block-1")
    assignments[assignments.index(collision)] = collision.model_copy(
        update={"dependence_cluster_id": "cluster-0"}
    )
    invalid = materialized.model_copy(update={"assignments": tuple(assignments)})
    with pytest.raises(ValueError, match="dependence cluster"):
        _first_paper_assignments(invalid)


def test_current_paper_plan_uses_common_blocks_but_remains_execution_gated():
    materialized = materialize_study(
        compile_study_file(Path("configs/studies/paper-core.yaml"))
    )
    replay_blocks = {
        item.trajectory_id
        for item in materialized.assignments
        if item.stage_id == "confirmatory-replay"
    }
    mphiq_blocks = {
        item.trajectory_id
        for item in materialized.assignments
        if item.stage_id == "mphiq-factorial"
    }
    assert replay_blocks == mphiq_blocks
    with pytest.raises(ValueError, match="first-paper assignments are not executable"):
        _first_paper_assignments(materialized)
