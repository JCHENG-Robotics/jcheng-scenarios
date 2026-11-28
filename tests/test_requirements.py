"""The generated jcheng.scenario_requirements.v1 document."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

from jcheng_scenarios.hashing import content_hash
from jcheng_scenarios.requirements import (
    GENERATOR,
    REQUIREMENTS_SCHEMA,
    RequirementsError,
    _capabilities,
    artifact_content_hash,
    build_requirements,
    requirements_json,
)

ROOT = Path(__file__).resolve().parents[1]
SCENARIO_DIR = ROOT / "scenarios" / "ore_sorting"


def _catalog(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "scenarios", tmp_path / "scenarios")
    shutil.copy(ROOT / "registry.yaml", tmp_path / "registry.yaml")
    return tmp_path


def _read(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write(path: Path, document: Any) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _mutate(root: Path, name: str, change) -> None:
    path = root / "scenarios" / "ore_sorting" / name
    document = _read(path)
    change(document)
    _write(path, document)


def test_document_identity_fields() -> None:
    document = build_requirements(ROOT, "ore_sorting")
    assert list(document) == [
        "schema",
        "scenario_id",
        "scenario_version",
        "vocabulary_status",
        "content_hash",
        "task_id",
        "evaluation_id",
        "capabilities",
        "constraints",
        "provenance",
    ]
    assert document["schema"] == REQUIREMENTS_SCHEMA
    assert document["scenario_id"] == "ore_sorting"
    assert document["scenario_version"] == "0.1.0"
    assert document["vocabulary_status"] == "contracted"
    assert document["task_id"] == "ore_sorting.task@0.1.0"
    assert document["evaluation_id"] == "ore_sorting.evaluation@0.1.0"


def test_content_hash_is_the_artifact_self_hash() -> None:
    document = build_requirements(ROOT, "ore_sorting")
    assert document["content_hash"] == artifact_content_hash(document)
    assert document["content_hash"].startswith("sha256:")
    assert document["content_hash"] != document["provenance"]["scenario_content_hash"]


def test_provenance_records_the_scenario_source_hash() -> None:
    document = build_requirements(ROOT, "ore_sorting")
    assert document["provenance"]["scenario_content_hash"] == content_hash(ROOT, "ore_sorting")


def test_non_projected_declaration_changes_both_hashes(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    before = build_requirements(root, "ore_sorting")

    def change_environment(environment: dict) -> None:
        environment["lighting"]["note"] = "Changed lighting note for the hash test."

    _mutate(root, "environment.yaml", change_environment)
    after = build_requirements(root, "ore_sorting")
    assert after["provenance"]["scenario_content_hash"] != before["provenance"]["scenario_content_hash"]
    assert after["content_hash"] != before["content_hash"]
    assert after["content_hash"] == artifact_content_hash(after)


def test_capabilities_cover_device_and_algorithm_requirements() -> None:
    document = build_requirements(ROOT, "ore_sorting")
    requirements = _read(SCENARIO_DIR / "capability-requirements.yaml")
    expected = [
        item["capability"]
        for item in requirements["device_requirements"] + requirements["algorithm_requirements"]
    ]
    assert [item["id"] for item in document["capabilities"]] == expected
    assert len(set(expected)) == len(expected)
    for item in document["capabilities"]:
        assert item["required"] is True
        assert item["verification"] == "Unverified"
        assert item["statement"]
        if item["requirement_owner"] == "device":
            source = next(
                row
                for row in requirements["device_requirements"]
                if row["capability"] == item["id"]
            )
            assert item["role"] == source["role"]
            assert item["interface"] == source["interface"]
            assert item.get("threshold") == source.get("threshold")
            assert "deferred_to" not in item
        else:
            source = next(
                row
                for row in requirements["algorithm_requirements"]
                if row["capability"] == item["id"]
            )
            assert item["deferred_to"] == source["owner"]
            assert "role" not in item and "threshold" not in item


def test_constraints_are_copied_from_the_task_specification() -> None:
    document = build_requirements(ROOT, "ore_sorting")
    task = _read(SCENARIO_DIR / "task.yaml")
    assert document["constraints"] == [
        {"id": item["id"], "statement": item["statement"]}
        for item in task["constraints"]
    ]
    assert {item["id"] for item in document["constraints"]} == {
        "motion_via_system_only",
        "no_grade_claim",
        "no_gangue_to_ore_bin",
    }


def test_provenance_and_json_round_trip() -> None:
    document = build_requirements(ROOT, "ore_sorting")
    assert document["provenance"] == {
        "source_path": "scenarios/ore_sorting",
        "generated_by": GENERATOR,
        "scenario_content_hash": content_hash(ROOT, "ore_sorting"),
    }
    payload = requirements_json(document)
    assert payload.endswith("\n")
    assert json.loads(payload) == document


def test_unknown_scenario_is_rejected() -> None:
    with pytest.raises(RequirementsError, match="scenario.unknown") as error:
        build_requirements(ROOT, "no_such_scenario")
    assert error.value.code == "scenario.unknown"


def test_missing_profile_is_rejected(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    (root / "scenarios" / "ore_sorting" / "task.yaml").unlink()
    with pytest.raises(RequirementsError, match="document.missing") as error:
        build_requirements(root, "ore_sorting")
    assert error.value.code == "document.missing"


def test_task_id_mismatch_is_rejected(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    _mutate(root, "task.yaml", lambda task: task.update({"id": "ore_sorting.other_task"}))
    with pytest.raises(RequirementsError, match="profile.id") as error:
        build_requirements(root, "ore_sorting")
    assert error.value.code == "profile.id"


def test_profile_version_mismatch_is_rejected(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    _mutate(root, "evaluation.yaml", lambda evaluation: evaluation.update({"version": "9.9.9"}))
    with pytest.raises(RequirementsError, match="profile.version") as error:
        build_requirements(root, "ore_sorting")
    assert error.value.code == "profile.version"


def test_scenario_version_mismatch_with_registry_is_rejected(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    _mutate(root, "scenario.yaml", lambda profile: profile.update({"version": "0.2.0"}))
    with pytest.raises(RequirementsError, match="registry version") as error:
        build_requirements(root, "ore_sorting")
    assert error.value.code == "profile.version"


def test_duplicate_capability_is_rejected(tmp_path: Path) -> None:
    root = _catalog(tmp_path)

    def duplicate(document: dict) -> None:
        document["algorithm_requirements"][0]["capability"] = document["device_requirements"][0]["capability"]

    _mutate(root, "capability-requirements.yaml", duplicate)
    with pytest.raises(RequirementsError, match="capability.duplicate") as error:
        build_requirements(root, "ore_sorting")
    assert error.value.code == "capability.duplicate"


def test_duplicate_requirement_id_is_rejected(tmp_path: Path) -> None:
    root = _catalog(tmp_path)

    def duplicate(document: dict) -> None:
        document["algorithm_requirements"][0]["id"] = document["device_requirements"][0]["id"]

    _mutate(root, "capability-requirements.yaml", duplicate)
    with pytest.raises(RequirementsError, match="requirement.duplicate") as error:
        build_requirements(root, "ore_sorting")
    assert error.value.code == "requirement.duplicate"


def test_invalid_source_document_is_rejected(tmp_path: Path) -> None:
    root = _catalog(tmp_path)

    def invalid(document: dict) -> None:
        del document["goal"]

    _mutate(root, "task.yaml", invalid)
    with pytest.raises(RequirementsError, match="profile.schema") as error:
        build_requirements(root, "ore_sorting")
    assert error.value.code == "profile.schema"


def test_document_satisfies_the_applications_reference_contract() -> None:
    document = build_requirements(ROOT, "ore_sorting")
    assert set(document) == {
        "schema",
        "scenario_id",
        "scenario_version",
        "vocabulary_status",
        "content_hash",
        "task_id",
        "evaluation_id",
        "capabilities",
        "constraints",
        "provenance",
    }
    assert document["schema"] == "jcheng.scenario_requirements.v1"
    assert re.fullmatch(r"[a-z0-9][a-z0-9_-]{1,63}", document["scenario_id"])
    assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", document["scenario_version"])
    for field in ("task_id", "evaluation_id"):
        reference = document[field]
        assert re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._@:+-]{0,127}", reference)
        assert reference.rsplit("@", 1)[1] == document["scenario_version"]
    for item in document["capabilities"]:
        assert set(item) <= {
            "id",
            "requirement_id",
            "requirement_owner",
            "required",
            "statement",
            "verification",
            "role",
            "interface",
            "threshold",
            "deferred_to",
        }
        assert isinstance(item["required"], bool)
        assert item["requirement_owner"] in {"device", "algorithm"}
        assert re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+", item["id"])
    for item in document["constraints"]:
        assert set(item) == {"id", "statement"}
    assert document["provenance"]

    body = {key: value for key, value in document.items() if key != "content_hash"}
    canonical = json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    expected = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert document["content_hash"] == expected


def test_algorithm_requirement_without_owner_is_rejected(tmp_path: Path) -> None:
    root = _catalog(tmp_path)

    def remove_owner(document: dict) -> None:
        del document["algorithm_requirements"][0]["owner"]

    _mutate(root, "capability-requirements.yaml", remove_owner)
    with pytest.raises(RequirementsError, match="profile.schema") as error:
        build_requirements(root, "ore_sorting")
    assert error.value.code == "profile.schema"


def test_emitter_rejects_algorithm_without_owner() -> None:
    document = _read(SCENARIO_DIR / "capability-requirements.yaml")
    del document["algorithm_requirements"][0]["owner"]
    with pytest.raises(RequirementsError, match="capability.owner") as error:
        _capabilities(document, SCENARIO_DIR / "capability-requirements.yaml")
    assert error.value.code == "capability.owner"
