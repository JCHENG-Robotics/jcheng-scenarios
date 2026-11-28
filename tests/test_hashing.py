"""Canonical content hashing: stability, semantic scope and bad input."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

from jcheng_scenarios.hashing import (
    NON_SEMANTIC_KEYS,
    canonical_document,
    canonical_payload,
    content_hash,
)
from jcheng_scenarios.loader import ScenarioError

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "scenarios" / "ore_sorting"


def _catalog(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "scenarios", tmp_path / "scenarios")
    shutil.copy(ROOT / "registry.yaml", tmp_path / "registry.yaml")
    return tmp_path


def _read(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write(path: Path, document: Any) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_content_hash_is_stable_and_sha256_shaped() -> None:
    first = content_hash(ROOT, "ore_sorting")
    second = content_hash(ROOT, "ore_sorting")
    assert first == second
    assert first.startswith("sha256:")
    digest = first.split(":", 1)[1]
    assert len(digest) == 64
    assert set(digest) <= set("0123456789abcdef")
    assert canonical_payload(ROOT, "ore_sorting")


def test_content_hash_ignores_generated_timestamps(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    before = content_hash(root, "ore_sorting")
    path = root / "scenarios" / "ore_sorting" / "task.yaml"
    task = _read(path)
    task["generated_at"] = "2026-11-28T00:00:00Z"
    task["provenance"]["generated_on"] = "2026-11-28"
    _write(path, task)
    assert content_hash(root, "ore_sorting") == before


def test_content_hash_is_location_independent(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    assert content_hash(root, "ore_sorting") == content_hash(ROOT, "ore_sorting")


def test_content_hash_changes_with_semantic_content(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    before = content_hash(root, "ore_sorting")
    path = root / "scenarios" / "ore_sorting" / "task.yaml"
    task = _read(path)
    task["goal"]["statement"] = task["goal"]["statement"] + " Changed."
    _write(path, task)
    assert content_hash(root, "ore_sorting") != before


def test_content_hash_is_independent_of_mapping_order(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    before = content_hash(root, "ore_sorting")

    def reverse(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: reverse(value[key]) for key in reversed(list(value))}
        if isinstance(value, list):
            return [reverse(item) for item in value]
        return value

    path = root / "scenarios" / "ore_sorting" / "scenario.yaml"
    document = _read(path)
    _write(path, reverse(document))
    assert content_hash(root, "ore_sorting") == before


def test_content_hash_includes_the_file_path(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    before = content_hash(root, "ore_sorting")
    scenario_dir = root / "scenarios" / "ore_sorting"
    shutil.copy(scenario_dir / "task.yaml", scenario_dir / "task-copy.yaml")
    profile_path = scenario_dir / "scenario.yaml"
    profile = _read(profile_path)
    profile["profiles"]["task"] = "task-copy.yaml"
    _write(profile_path, profile)
    assert content_hash(root, "ore_sorting") != before


def test_content_hash_rejects_unknown_scenario() -> None:
    with pytest.raises(ScenarioError, match="unknown scenario id"):
        content_hash(ROOT, "no_such_scenario")


def test_content_hash_rejects_a_missing_declaration(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    (root / "scenarios" / "ore_sorting" / "task.yaml").unlink()
    with pytest.raises(ScenarioError, match="missing task profile"):
        content_hash(root, "ore_sorting")


def test_content_hash_rejects_a_duplicate_reference(tmp_path: Path) -> None:
    root = _catalog(tmp_path)
    path = root / "scenarios" / "ore_sorting" / "scenario.yaml"
    profile = _read(path)
    profile["profiles"]["evaluation"] = profile["profiles"]["task"]
    _write(path, profile)
    with pytest.raises(ScenarioError, match="duplicate profile reference"):
        content_hash(root, "ore_sorting")


def test_canonical_document_sorts_mappings_and_keeps_list_order() -> None:
    document = {
        "zeta": 1,
        "alpha": {"b": 2, "a": 1, "generated_at": "2026-11-28"},
        "items": [{"second": 2, "first": 1}, "tail"],
        "timestamp": "2026-11-28T00:00:00Z",
    }
    canonical = canonical_document(document)
    assert list(canonical) == ["alpha", "items", "zeta"]
    assert list(canonical["alpha"]) == ["a", "b"]
    assert canonical["items"][0] == {"first": 1, "second": 2}
    assert canonical["items"][1] == "tail"
    assert not set(canonical) & NON_SEMANTIC_KEYS
    assert "generated_at" not in canonical["alpha"]


def test_canonical_document_rejects_non_mapping_input() -> None:
    with pytest.raises(ScenarioError, match="must be a mapping"):
        canonical_document(["not", "a", "mapping"])  # type: ignore[arg-type]
