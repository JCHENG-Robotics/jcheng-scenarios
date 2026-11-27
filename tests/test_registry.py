"""Relationship checks the JSON Schemas cannot express."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from jcheng_scenarios.loader import ScenarioError, load_yaml
from jcheng_scenarios.registry import _resolve_inside, validate_root

ROOT = Path(__file__).resolve().parents[1]


def _catalog(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "scenarios", tmp_path / "scenarios")
    shutil.copy(ROOT / "registry.yaml", tmp_path / "registry.yaml")
    return tmp_path


def _read(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _codes(root: Path) -> set[str]:
    return {issue.code for issue in validate_root(root).issues}


def test_copied_catalog_is_valid(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    assert validate_root(root).ok


def test_duplicate_registry_id_is_rejected(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    path = root / "registry.yaml"
    registry = _read(path)
    registry["scenarios"].append(dict(registry["scenarios"][0]))
    _write(path, registry)
    assert "registry.duplicate_id" in _codes(root)


def test_duplicate_station_id_is_rejected(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    path = root / "scenarios" / "ore_sorting" / "environment.yaml"
    environment = _read(path)
    environment["stations"].append(dict(environment["stations"][0]))
    _write(path, environment)
    assert "ids.duplicate" in _codes(root)


def test_profile_version_mismatch_is_rejected(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    path = root / "scenarios" / "ore_sorting" / "scenario.yaml"
    profile = _read(path)
    profile["version"] = "0.2.0"
    _write(path, profile)
    assert "profile.version_mismatch" in _codes(root)


def test_missing_sub_profile_is_rejected(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    path = root / "scenarios" / "ore_sorting" / "scenario.yaml"
    profile = _read(path)
    profile["profiles"]["task"] = "missing-task.yaml"
    _write(path, profile)
    assert "document.missing" in _codes(root)


def test_unknown_semantic_reference_is_rejected(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    path = root / "scenarios" / "ore_sorting" / "semantics.yaml"
    semantics = _read(path)
    semantics["attributes"][0]["applies_to"].append("ghost_class")
    _write(path, semantics)
    assert "reference.unknown" in _codes(root)


def test_non_finite_number_is_rejected(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    path = root / "scenarios" / "ore_sorting" / "environment.yaml"
    environment = _read(path)
    environment["stations"][0]["pose"]["x_m"] = float("nan")
    _write(path, environment)
    assert "value.non_finite" in _codes(root)


def test_fixed_threshold_without_value_is_rejected(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    path = root / "scenarios" / "ore_sorting" / "evaluation.yaml"
    evaluation = _read(path)
    evaluation["metrics"][0]["threshold_status"] = "fixed"
    evaluation["metrics"][0]["threshold"] = None
    _write(path, evaluation)
    assert "document.schema" in _codes(root)


def test_profile_reference_outside_scenario_directory_is_rejected(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    path = root / "scenarios" / "ore_sorting" / "scenario.yaml"
    profile = _read(path)
    profile["profiles"]["task"] = "../task.yaml"
    _write(path, profile)
    # The schema pattern rejects the traversal before the loader sees it.
    assert "document.schema" in _codes(root)


def test_resolve_inside_rejects_escapes(tmp_path: Path) -> None:
    base = tmp_path / "catalog"
    base.mkdir()
    assert _resolve_inside(base, "child.yaml") == (base / "child.yaml").resolve()
    assert _resolve_inside(base, "../outside.yaml") is None
    assert _resolve_inside(base, str(tmp_path / "absolute.yaml")) is None


def test_duplicate_yaml_key_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.yaml"
    path.write_text("id: one\nid: two\n", encoding="utf-8")
    with pytest.raises(ScenarioError, match="duplicate mapping key"):
        load_yaml(path)
