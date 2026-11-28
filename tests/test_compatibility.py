"""Read-only compatibility outcomes and bad-input rejection."""

from __future__ import annotations

from pathlib import Path

import pytest

from jcheng_scenarios.compatibility import CompatibilityError, check
from jcheng_scenarios.requirements import build_requirements

ROOT = Path(__file__).resolve().parents[1]
HASH = "sha256:" + "a" * 64


def _requirements(capabilities: list[dict] | None = None) -> dict:
    if capabilities is None:
        capabilities = [
            {"id": "manipulation.arm.reach_m", "required": True},
            {"id": "perception.scene_state", "required": True},
            {"id": "perception.reachability", "required": False},
        ]
    return {
        "schema": "jcheng.scenario_requirements.v1",
        "scenario_id": "ore_sorting",
        "scenario_version": "0.1.0",
        "content_hash": HASH,
        "task_id": "ore_sorting.task@0.1.0",
        "evaluation_id": "ore_sorting.evaluation@0.1.0",
        "capabilities": capabilities,
        "constraints": [],
        "provenance": {
            "source_path": "scenarios/ore_sorting",
            "generated_by": "test",
        },
    }


def _device(capabilities: dict | list, **metadata) -> dict:
    payload = {
        "scenario_id": "ore_sorting",
        "scenario_version": "0.1.0",
        "content_hash": HASH,
        "device_id": "hiwonder.armpi-ultra",
        "device_version": "0.1.0",
        "capabilities": capabilities,
    }
    payload.update(metadata)
    return payload


def _complete() -> dict:
    return {
        "manipulation.arm.reach_m": {},
        "perception.scene_state": {},
        "perception.reachability": {},
    }


def _codes(result) -> set[str]:
    return {finding.code for finding in result.errors}


def test_matching_requirements_and_capabilities_pass() -> None:
    result = check(_requirements(), _device(_complete()))
    assert result.status == "compatible"
    assert result.errors == ()
    assert result.warnings == ()
    assert result.ok
    assert result
    assert result.device_id == "hiwonder.armpi-ultra"
    assert result.deployable is False
    assert result["status"] == "compatible"


def test_device_capability_document_forms_are_accepted() -> None:
    requirements = _requirements()
    list_form = [
        {"id": "manipulation.arm.reach_m", "parameters": {}},
        {"id": "perception.scene_state"},
        "perception.reachability",
    ]
    bare_mapping = {
        "manipulation.arm.reach_m": {"reach_m": 0.5},
        "perception.scene_state": {"valid": True},
        "perception.reachability": {"advisory": True},
    }
    assert check(requirements, list_form).status == "compatible"
    assert check(requirements, bare_mapping).status == "compatible"


def test_unknown_device_capability_is_an_error() -> None:
    device = _complete()
    device["ghost.capability"] = {}
    result = check(_requirements(), _device(device))
    assert result.status == "incompatible"
    assert _codes(result) == {"UNKNOWN_CAPABILITY"}
    assert result.errors[0].capability == "ghost.capability"
    assert result.errors[0]["code"] == "UNKNOWN_CAPABILITY"
    assert not result.ok
    assert not result


def test_missing_required_capability_is_an_error() -> None:
    device = _complete()
    del device["manipulation.arm.reach_m"]
    result = check(_requirements(), _device(device))
    assert result.status == "incompatible"
    assert _codes(result) == {"MISSING_REQUIRED_CAPABILITY"}
    assert result.errors[0].capability == "manipulation.arm.reach_m"


def test_missing_optional_capability_is_a_warning() -> None:
    device = _complete()
    del device["perception.reachability"]
    result = check(_requirements(), _device(device))
    assert result.status == "compatible_with_warnings"
    assert result.errors == ()
    assert result.warnings[0].code == "OPTIONAL_CAPABILITY_MISSING"
    assert result.ok


def test_unsupported_required_capability_is_an_error() -> None:
    device = _complete()
    device["manipulation.arm.reach_m"] = {"supported": False}
    result = check(_requirements(), _device(device))
    assert result.status == "incompatible"
    assert _codes(result) == {"MISSING_REQUIRED_CAPABILITY"}
    assert "unsupported" in result.errors[0].message


def test_parameter_range_is_checked() -> None:
    requirements = _requirements(
        [
            {
                "id": "manipulation.arm.reach_m",
                "required": True,
                "parameters": {"reach_m": {"min": 0.45}},
            },
            {"id": "perception.scene_state", "required": True},
            {"id": "perception.reachability", "required": False},
        ]
    )
    passing = _complete()
    passing["manipulation.arm.reach_m"] = {"reach_m": 0.50}
    assert check(requirements, _device(passing)).status == "compatible"

    boundary = _complete()
    boundary["manipulation.arm.reach_m"] = {"reach_m": 0.45}
    assert check(requirements, _device(boundary)).status == "compatible"

    failing = _complete()
    failing["manipulation.arm.reach_m"] = {"reach_m": 0.30}
    result = check(requirements, _device(failing))
    assert result.status == "incompatible"
    assert _codes(result) == {"INCOMPATIBLE_PARAMETER"}


def test_parameter_expectation_form_is_checked() -> None:
    requirements = _requirements(
        [
            {
                "id": "manipulation.arm.reach_m",
                "required": True,
                "parameters": {"reach_m": {"op": ">=", "value": 0.45}},
            },
            {"id": "perception.scene_state", "required": True},
            {"id": "perception.reachability", "required": False},
        ]
    )
    passing = _complete()
    passing["manipulation.arm.reach_m"] = {"reach_m": 0.50}
    assert check(requirements, _device(passing)).status == "compatible"

    failing = _complete()
    failing["manipulation.arm.reach_m"] = {"reach_m": 0.30}
    result = check(requirements, _device(failing))
    assert result.status == "incompatible"
    assert _codes(result) == {"INCOMPATIBLE_PARAMETER"}


def test_parameter_exact_value_and_type_are_checked() -> None:
    requirements = _requirements(
        [
            {
                "id": "manipulation.arm.dof",
                "required": True,
                "parameters": {"dof": 4},
            },
            {"id": "perception.scene_state", "required": True},
            {"id": "perception.reachability", "required": False},
        ]
    )
    device = {
        "manipulation.arm.dof": {"dof": 4},
        "perception.scene_state": {},
        "perception.reachability": {},
    }
    assert check(requirements, _device(device)).status == "compatible"

    device["manipulation.arm.dof"] = {"dof": "4"}
    result = check(requirements, _device(device))
    assert result.status == "incompatible"
    assert _codes(result) == {"INCOMPATIBLE_PARAMETER"}


def test_missing_parameter_is_a_parameter_error() -> None:
    requirements = _requirements(
        [
            {
                "id": "manipulation.arm.reach_m",
                "required": True,
                "parameters": {"reach_m": {"min": 0.45}},
            },
            {"id": "perception.scene_state", "required": True},
            {"id": "perception.reachability", "required": False},
        ]
    )
    result = check(requirements, _device(_complete()))
    assert result.status == "incompatible"
    assert _codes(result) == {"INCOMPATIBLE_PARAMETER"}
    assert "missing" in result.errors[0].message


def test_scenario_version_mismatch_is_an_error() -> None:
    result = check(_requirements(), _device(_complete(), scenario_version="0.2.0"))
    assert result.status == "incompatible"
    assert _codes(result) == {"INCOMPATIBLE_VERSION"}


def test_content_hash_mismatch_is_an_error() -> None:
    other = "sha256:" + "b" * 64
    result = check(_requirements(), _device(_complete(), content_hash=other))
    assert result.status == "incompatible"
    assert _codes(result) == {"INCOMPATIBLE_CONTENT_HASH"}


def test_scenario_id_mismatch_is_an_error() -> None:
    result = check(_requirements(), _device(_complete(), scenario_id="other_scenario"))
    assert result.status == "incompatible"
    assert _codes(result) == {"INCOMPATIBLE_SCENARIO"}


def test_scenario_ref_mapping_is_checked() -> None:
    device = {
        "scenario_ref": {
            "scenario_id": "ore_sorting",
            "scenario_version": "0.2.0",
            "content_hash": HASH,
        },
        "capabilities": _complete(),
    }
    result = check(_requirements(), device)
    assert _codes(result) == {"INCOMPATIBLE_VERSION"}


def test_device_artifact_hash_is_not_treated_as_a_scenario_pin() -> None:
    device = {
        "source_device": "hiwonder.armpi-ultra",
        "device_version": "0.1.0",
        "content_hash": "sha256:" + "b" * 64,
        "capabilities": [
            {"id": capability, "parameters": {}} for capability in _complete()
        ],
    }
    result = check(_requirements(), device)
    assert result.status == "compatible"
    assert result.device_id == "hiwonder.armpi-ultra"


def test_generated_requirements_pass_against_a_complete_capability_set() -> None:
    requirements = build_requirements(ROOT, "ore_sorting")
    device = {item["id"]: {} for item in requirements["capabilities"]}
    result = check(requirements, device)
    assert result.status == "compatible"
    assert result.scenario_id == "ore_sorting"
    assert result.content_hash == requirements["content_hash"]
    assert result.to_dict()["deployable"] is False


def test_malformed_requirements_are_rejected() -> None:
    with pytest.raises(CompatibilityError, match="schema"):
        check({"schema": "wrong"}, {})
    duplicate = _requirements(
        [
            {"id": "manipulation.arm.reach_m", "required": True},
            {"id": "manipulation.arm.reach_m", "required": True},
        ]
    )
    with pytest.raises(CompatibilityError, match="duplicate"):
        check(duplicate, {})
    bad_required = _requirements([{"id": "manipulation.arm.reach_m", "required": "yes"}])
    with pytest.raises(CompatibilityError, match="required"):
        check(bad_required, {})
    bad_hash = _requirements()
    bad_hash["content_hash"] = "not-a-hash"
    with pytest.raises(CompatibilityError, match="content_hash"):
        check(bad_hash, {})


def test_malformed_device_documents_are_rejected() -> None:
    with pytest.raises(CompatibilityError, match="dotted identifier"):
        check(_requirements(), {"Not-A-Capability": {}})
    with pytest.raises(CompatibilityError, match="must be a mapping, boolean or null"):
        check(_requirements(), {"manipulation.arm.reach_m": 42})
    with pytest.raises(CompatibilityError, match="duplicate"):
        check(
            _requirements(),
            [
                {"id": "manipulation.arm.reach_m"},
                {"id": "manipulation.arm.reach_m"},
            ],
        )
    with pytest.raises(CompatibilityError, match="scenario_ref"):
        check(_requirements(), {"scenario_ref": "not-a-mapping", "capabilities": {}})
    with pytest.raises(CompatibilityError, match="mapping or a list"):
        check(_requirements(), "not-a-document")
