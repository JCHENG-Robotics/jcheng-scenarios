"""Schema validity and strictness."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from jcheng_scenarios.loader import load_yaml
from jcheng_scenarios.registry import validate_root
from jcheng_scenarios.schema import (
    SCHEMA_FILES,
    check_all_schemas,
    load_schema,
    validate_document,
)

ROOT = Path(__file__).resolve().parents[1]


def test_every_schema_is_valid_json_schema() -> None:
    assert check_all_schemas() == []


def test_the_expected_schema_set_ships() -> None:
    shipped = sorted(path.name for path in (ROOT / "schemas").glob("*.schema.json"))
    assert shipped == sorted(SCHEMA_FILES.values())


def test_shipped_catalog_validates() -> None:
    report = validate_root(ROOT)
    assert report.ok, [issue.to_dict() for issue in report.issues]
    assert [item.id for item in report.scenarios] == ["ore_sorting"]
    assert report.scenarios[0].profiles == 6


def test_profile_schema_rejects_an_unknown_field() -> None:
    profile = load_yaml(ROOT / "scenarios" / "ore_sorting" / "scenario.yaml")
    mutated = copy.deepcopy(profile)
    mutated["runtime_executor"] = True
    issues = validate_document("profile", mutated, "scenario.yaml")
    assert issues and issues[0].code == "document.schema"
    assert "runtime_executor" in issues[0].message


def test_registry_schema_requires_a_registered_path() -> None:
    registry = load_yaml(ROOT / "registry.yaml")
    mutated = copy.deepcopy(registry)
    del mutated["scenarios"][0]["path"]
    issues = validate_document("registry", mutated, "registry.yaml")
    assert issues
    assert any("path" in issue.message for issue in issues)


def test_registry_schema_rejects_unknown_delivery_word() -> None:
    registry = load_yaml(ROOT / "registry.yaml")
    mutated = copy.deepcopy(registry)
    mutated["scenarios"][0]["delivery"] = "done"
    issues = validate_document("registry", mutated, "registry.yaml")
    assert issues


def _refs(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "$ref":
                yield item
            else:
                yield from _refs(item)
    elif isinstance(value, list):
        for item in value:
            yield from _refs(item)


def test_schema_refs_are_repository_local() -> None:
    for kind in SCHEMA_FILES:
        for reference in _refs(load_schema(kind)):
            assert reference.startswith("#/$defs/"), reference


def test_unknown_schema_kind_is_rejected() -> None:
    with pytest.raises(KeyError):
        load_schema("unknown")

