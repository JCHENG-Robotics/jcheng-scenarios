"""Content rules for the reference scenario: no fabricated facts, no execution plan."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

import pytest

from jcheng_scenarios.loader import load_yaml

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "scenarios" / "ore_sorting"

DELIVERY = {"Complete", "In progress", "Planned", "Not started"}
VERIFICATION = {"Verified", "Partially verified", "Unverified", "Inconclusive"}
FORBIDDEN_KEYS = {
    "true_centroid",
    "true_center",
    "full_extent",
    "volume",
    "mass",
    "material_composition",
    "ore_grade",
    "economic_value",
}
PROFILE_FILES = (
    "scenario.yaml",
    "environment.yaml",
    "semantics.yaml",
    "task.yaml",
    "capability-requirements.yaml",
    "operational-constraints.yaml",
    "evaluation.yaml",
)


def _walk(value: Any) -> Iterator[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


@pytest.fixture(scope="module")
def documents() -> dict[str, dict]:
    return {name: load_yaml(SCENARIO / name) for name in PROFILE_FILES}


def test_all_profile_files_ship() -> None:
    assert sorted(path.name for path in SCENARIO.iterdir() if path.is_file()) == sorted(PROFILE_FILES)


def test_status_vocabulary_is_standard(documents: dict[str, dict]) -> None:
    for name, document in documents.items():
        for key, value in _walk(document):
            if key == "verification":
                assert value in VERIFICATION, f"{name}: {value}"
            if key in {"delivery", "integration", "matching_status"}:
                assert value in DELIVERY, f"{name}: {value}"


def test_no_forbidden_measurement_keys(documents: dict[str, dict]) -> None:
    for name, document in documents.items():
        for key, _ in _walk(document):
            assert key not in FORBIDDEN_KEYS, f"{name}: fabricated field {key}"


def test_forbidden_inferences_cover_the_whole_list(documents: dict[str, dict]) -> None:
    declared = set(documents["semantics.yaml"]["forbidden_inferences"])
    assert declared == FORBIDDEN_KEYS


def test_every_metric_threshold_is_unset(documents: dict[str, dict]) -> None:
    for metric in documents["evaluation.yaml"]["metrics"]:
        assert metric["threshold"] is None
        assert metric["threshold_status"] == "not_set"
        assert metric["verification"] == "Unverified"


def test_no_integration_is_claimed(documents: dict[str, dict]) -> None:
    profile = documents["scenario.yaml"]
    assert profile["delivery"] == "In progress"
    assert profile["verification"] == "Unverified"
    assert {consumer["integration"] for consumer in profile["consumers"]} == {"Not started"}
    assert {consumer["repo"] for consumer in profile["consumers"]} == {
        "jcheng-applications",
        "jcheng-benchmark",
        "jcheng-devices",
        "jcheng-perception",
        "jcheng-simulation",
    }


def test_capability_matching_is_not_started(documents: dict[str, dict]) -> None:
    requirements = documents["capability-requirements.yaml"]
    assert requirements["matching_status"] == "Not started"
    assert requirements["vocabulary_status"] == "contracted"
    for requirement in requirements["device_requirements"] + requirements["algorithm_requirements"]:
        assert requirement["verification"] == "Unverified"
        assert "device_id" not in requirement
        assert "model" not in requirement


def test_every_profile_is_design_provenance(documents: dict[str, dict]) -> None:
    for name, document in documents.items():
        provenance = document["provenance"]
        assert provenance["source_kind"] == "design", name
        assert provenance["created"] == "2026-11-27"
        assert provenance["updated"] == "2026-11-27"
        assert provenance["sources"]


def test_task_references_exist(documents: dict[str, dict]) -> None:
    classes = {item["id"] for item in documents["semantics.yaml"]["ontology"]}
    stations = {item["id"] for item in documents["environment.yaml"]["stations"]}
    goal = documents["task.yaml"]["goal"]
    assert goal["target_class"] in classes
    assert goal["destination"] in classes
    assert goal["destination"] in stations


def test_task_is_declarative_not_executable(documents: dict[str, dict]) -> None:
    task = documents["task.yaml"]
    keys = {key for key, _ in _walk(task)}
    assert not keys & {"steps", "trajectory", "joint_targets", "waypoints", "gripper_commands"}
    assert task["out_of_scope"]


def test_environment_is_a_design_declaration(documents: dict[str, dict]) -> None:
    environment = documents["environment.yaml"]
    assert environment["basis"] == "design_target"
    assert {item["verification"] for item in environment["constraints"]} == {"Unverified"}


def test_safety_boundary_points_to_the_system_layer(documents: dict[str, dict]) -> None:
    boundary = documents["operational-constraints.yaml"]["safety_boundary"]
    assert boundary["owner"] == "jcheng-system"
    assert "jcheng-system" in boundary["statement"]


def test_evaluation_contains_no_result(documents: dict[str, dict]) -> None:
    evaluation = documents["evaluation.yaml"]
    keys = {key for key, _ in _walk(evaluation)}
    assert not keys & {"result", "measured_value", "observed_value", "score"}
    assert evaluation["reporting"]["owner"] == "jcheng-benchmark"
