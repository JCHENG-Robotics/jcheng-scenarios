"""Repository contract: files, versions, manifest and release policy."""

from __future__ import annotations

from pathlib import Path
import re

import yaml

from jcheng_scenarios import __version__
from jcheng_scenarios.registry import load_profile

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = (
    "README.md",
    "README.zh-CN.md",
    "ROADMAP.md",
    "CHANGELOG.md",
    "ACCEPTANCE.md",
    "VERSION",
    "LICENSE-REVIEW.md",
    "SCHEMA_OWNERSHIP.md",
    "capability.yaml",
    "registry.yaml",
    "pyproject.toml",
    "docs/ARCHITECTURE.md",
    "docs/SCEN_LAYER.md",
    "docs/SCENARIO_MODEL.md",
    "docs/CAPABILITY_MATCHING.md",
    "docs/EVALUATION_MODEL.md",
    "docs/AUTHORING.md",
    "docs/DEPENDENCY_REVIEW.md",
    "docs/ASSET_AUDIT_20261127.md",
    "scenarios/README.md",
    "evidence/README.md",
    "scripts/check_repo_gate.sh",
    ".github/CODEOWNERS",
    ".github/workflows/ci.yml",
    "src/jcheng_scenarios/__init__.py",
    "src/jcheng_scenarios/__main__.py",
    "src/jcheng_scenarios/cli.py",
    "src/jcheng_scenarios/loader.py",
    "src/jcheng_scenarios/model.py",
    "src/jcheng_scenarios/registry.py",
    "src/jcheng_scenarios/schema.py",
)


def test_required_files_exist() -> None:
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    assert not missing, f"missing: {missing}"


def test_version_matches_package_manifest_and_catalog() -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    manifest = yaml.safe_load((ROOT / "capability.yaml").read_text(encoding="utf-8"))
    registry = yaml.safe_load((ROOT / "registry.yaml").read_text(encoding="utf-8"))
    profile = yaml.safe_load(
        (ROOT / "scenarios" / "ore_sorting" / "scenario.yaml").read_text(encoding="utf-8")
    )
    assert version == __version__ == manifest["version"] == "0.1.0"
    assert {entry["version"] for entry in registry["scenarios"]} == {version}
    assert profile["version"] == version


def test_capability_manifest_is_canonical_offline() -> None:
    manifest = yaml.safe_load((ROOT / "capability.yaml").read_text(encoding="utf-8"))
    assert set(manifest) == {
        "schema_version",
        "name",
        "version",
        "contract",
        "safety",
        "hardware_access",
        "runtime",
    }
    assert manifest["schema_version"] == 1
    assert manifest["name"] == "jcheng-scenarios"
    assert manifest["version"] == "0.1.0"
    assert manifest["contract"] == {
        "interfaces": ">=0.2,<0.3",
        "contract_hash": (
            "sha256:afca22a42f7163e0351d185d5a8577b0b51f2f3da4b92278f161a4a7d2c35b1c"
        ),
        "system_api": ">=0.2,<0.4",
    }
    assert manifest["safety"] == {
        "class": "offline",
        "scopes": [],
        "requires_lease": True,
        "max_rate_hz": 1,
        "deadman_ms": 500,
    }
    assert manifest["hardware_access"] == "none"
    assert manifest["runtime"] == {
        "ros_domains": [],
        "publishes": [],
        "subscribes": [],
    }


def test_every_schema_is_declared_in_schema_ownership() -> None:
    files = {
        f"schemas/{path.name}"
        for path in (ROOT / "schemas").glob("*.schema.json")
    }
    text = (ROOT / "SCHEMA_OWNERSHIP.md").read_text(encoding="utf-8")
    declared = set(re.findall(r"\| `(schemas/[^`]+\.schema\.json)` \|", text))
    assert declared == files, {
        "undeclared": sorted(files - declared),
        "missing": sorted(declared - files),
    }
    for line in text.splitlines():
        if "| `schemas/" not in line:
            continue
        assert "`repo-local`" in line, line
        assert "none;" in line, line


def test_no_license_before_review() -> None:
    assert not (ROOT / "LICENSE").exists()
    text = (ROOT / "LICENSE-REVIEW.md").read_text(encoding="utf-8")
    assert "does **not** ship a `LICENSE`" in text


def test_no_model_weights_or_recorded_bags() -> None:
    suffixes = {".pt", ".onnx", ".engine", ".bag", ".db3", ".mcap"}
    found = [
        path.relative_to(ROOT)
        for path in ROOT.rglob("*")
        if path.is_file() and path.suffix in suffixes
    ]
    assert not found, f"model weights or bags must stay out of the tree: {found}"


def test_ci_runs_the_repository_gate() -> None:
    text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "scenarios-gate" in text
    assert "bash scripts/check_repo_gate.sh" in text


def test_registry_has_only_the_reference_scenario() -> None:
    registry = yaml.safe_load((ROOT / "registry.yaml").read_text(encoding="utf-8"))
    ids = [entry["id"] for entry in registry["scenarios"]]
    assert ids == ["ore_sorting"]
    shipped = sorted(path.name for path in (ROOT / "scenarios").iterdir() if path.is_dir())
    assert shipped == ["ore_sorting"]


def test_candidate_scenarios_are_not_empty_shells() -> None:
    candidates = ("shopping_mall", "warehouse", "manufacturing")
    for candidate in candidates:
        assert not (ROOT / "scenarios" / candidate).exists(), candidate


def test_load_profile_round_trip() -> None:
    profile = load_profile(ROOT, "ore_sorting")
    assert profile["id"] == "ore_sorting"
    assert set(profile["profiles"]) == {
        "environment",
        "semantics",
        "task",
        "capability_requirements",
        "operational_constraints",
        "evaluation",
    }
