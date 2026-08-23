from __future__ import annotations

import subprocess
from collections import Counter, deque
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).parents[1]
BASE = "c1fd8cd5c0205dfdf66b587f90477b2014f8aff1"
BASE_TREE = "a6e1bff70a4421461341e15707b1094ac8514333"
SOURCE = "4016845d86b58b8da2715a60cd621a03dd049626"
EXPECTED_EXPERIMENTS = {f"exp-{index:03d}" for index in range(27)} | {"alpha-oos-001"}
ALLOWED_STATUSES = {"planned", "planned_exploratory", "blocked_external"}


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def _load(path: str) -> dict[str, Any]:
    data = yaml.safe_load((ROOT / path).read_text())
    assert isinstance(data, dict)
    return data


def _packet(study: dict[str, Any]) -> dict[str, Any]:
    path = f"studies/{study['study_id']}/study.yaml"
    data = yaml.safe_load(_git("show", f"{study['branch']}:{path}"))
    assert isinstance(data, dict)
    return data


def test_registry_owns_every_experiment_once() -> None:
    manifest = _load("research-program.yaml")
    studies = manifest["study_units"]
    assert manifest["schema_version"] == 2
    assert manifest["publication_base"] == BASE
    assert manifest["publication_base_tree"] == BASE_TREE
    assert manifest["recoverable_source"] == SOURCE
    assert len(studies) == 17
    assert len({study["study_id"] for study in studies}) == 17
    assert len({study["branch"] for study in studies}) == 17
    assert {study["status"] for study in studies} <= ALLOWED_STATUSES
    experiments = [experiment for study in studies for experiment in study["experiments"]]
    assert Counter(experiments) == Counter(EXPECTED_EXPERIMENTS)


def test_packets_descend_current_main_and_match_registry() -> None:
    manifest = _load("research-program.yaml")
    for study in manifest["study_units"]:
        branch = study["branch"]
        packet = _packet(study)
        subprocess.run(["git", "merge-base", "--is-ancestor", BASE, branch], cwd=ROOT, check=True)
        assert _git("rev-parse", study["initial_packet_commit"]) == study["initial_packet_commit"]
        assert packet["study_id"] == study["study_id"]
        assert packet["branch"] == branch
        assert packet["status"] == study["status"]
        assert packet["ownership"]["experiments"] == study["experiments"]
        assert packet["ownership"]["hypothesis_roles"] == study["hypothesis_roles"]
        assert packet["source"]["publication_base"] == BASE
        assert packet["source"]["recoverable_program_commit"] == SOURCE
        expected = {
            f"A\tstudies/{study['study_id']}/protocol.md",
            f"A\tstudies/{study['study_id']}/study.yaml",
        }
        assert set(_git("diff", "--name-status", f"{BASE}..{branch}").splitlines()) == expected


def test_dependency_artifacts_exist_and_graph_is_acyclic() -> None:
    studies = _load("research-program.yaml")["study_units"]
    by_id = {study["study_id"]: study for study in studies}
    outgoing = {study_id: set() for study_id in by_id}
    indegree = {study_id: 0 for study_id in by_id}
    for consumer in studies:
        for edge in consumer["depends_on"]:
            producer_id = edge["producer"]
            assert producer_id in by_id
            assert producer_id != consumer["study_id"]
            producer_outputs = set(_packet(by_id[producer_id])["outputs"])
            assert set(edge["artifacts"]) <= producer_outputs
            if consumer["study_id"] not in outgoing[producer_id]:
                outgoing[producer_id].add(consumer["study_id"])
                indegree[consumer["study_id"]] += 1
    queue = deque(study_id for study_id, degree in indegree.items() if degree == 0)
    visited = 0
    while queue:
        producer_id = queue.popleft()
        visited += 1
        for consumer_id in outgoing[producer_id]:
            indegree[consumer_id] -= 1
            if indegree[consumer_id] == 0:
                queue.append(consumer_id)
    assert visited == len(studies)


def test_correction_ledger_preserves_old_refs_and_maps_every_new_branch() -> None:
    manifest = _load("research-program.yaml")
    ledger = _load("branch-corrections.yaml")
    assert ledger["current_base"] == {"commit": BASE, "tree": BASE_TREE}
    assert ledger["superseded_base"]["tree"] == BASE_TREE
    assert _git("rev-parse", f"{BASE}^{{tree}}") == BASE_TREE
    assert _git("rev-parse", f"{ledger['superseded_base']['commit']}^{{tree}}") == BASE_TREE
    replacements = []
    old_branches = set()
    for family in ledger["superseded_families"]:
        assert family["old_branch"] not in old_branches
        old_branches.add(family["old_branch"])
        assert _git("rev-parse", family["recovery_ref"]) == family["tip"]
        replacements.extend(family["replaced_by"])
    active_branches = [study["branch"] for study in manifest["study_units"]]
    assert Counter(replacements) == Counter(active_branches)
