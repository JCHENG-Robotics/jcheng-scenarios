"""Registry and scenario-profile validation beyond JSON Schema.

The schemas enforce shape. This module enforces the relationships JSON Schema
cannot express: unique IDs, containment inside the catalog root, file
references, cross-profile references, version agreement and finite numbers.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .loader import ScenarioError, load_yaml
from .model import ScenarioSummary, ValidationReport
from .schema import validate_document

PROFILE_KINDS: dict[str, str] = {
    "environment": "jcheng.scenario.environment.v1",
    "semantics": "jcheng.scenario.semantics.v1",
    "task": "jcheng.scenario.task.v1",
    "capability_requirements": "jcheng.scenario.capability_requirements.v1",
    "operational_constraints": "jcheng.scenario.operational_constraints.v1",
    "evaluation": "jcheng.scenario.evaluation.v1",
}

LIST_SECTIONS = (
    "business",
    "constraints",
    "consumers",
    "device_requirements",
    "environment",
    "failure_conditions",
    "frames",
    "interface_requirements",
    "metrics",
    "ontology",
    "preconditions",
    "relations",
    "risks",
    "stations",
    "success_conditions",
    "surfaces",
    "zones",
)


def _relative(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _resolve_inside(base: Path, reference: str) -> Path | None:
    """Resolve a relative reference, rejecting absolute paths and escapes."""

    candidate = (base / reference).expanduser()
    try:
        resolved = candidate.resolve()
        resolved.relative_to(base.resolve())
    except (OSError, ValueError):
        return None
    return resolved


def _load_document(
    root: Path,
    path: Path,
    kind: str,
    report: ValidationReport,
    label: str,
) -> dict | None:
    relative = _relative(root, path)
    if not path.is_file():
        report.add("document.missing", relative, f"missing {label}")
        return None
    try:
        document = load_yaml(path)
    except ScenarioError as error:
        report.add("document.parse", relative, error.message)
        return None
    if not isinstance(document, dict):
        report.add("document.type", relative, f"{label} must be a mapping")
        return None
    issues = validate_document(kind, document, relative)
    report.issues.extend(issues)
    _check_finite(document, relative, report)
    if issues:
        return None
    return document


def _check_finite(value: Any, path: str, report: ValidationReport, trail: str = "$") -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, float) and not math.isfinite(value):
        report.add("value.non_finite", path, f"{trail} is not a finite number")
    elif isinstance(value, dict):
        for key, item in value.items():
            _check_finite(item, path, report, f"{trail}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _check_finite(item, path, report, f"{trail}[{index}]")


def _check_duplicate_ids(document: dict, path: str, report: ValidationReport) -> None:
    for section in LIST_SECTIONS:
        items = document.get(section)
        if not isinstance(items, list):
            continue
        seen: set[str] = set()
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            identifier = item.get("id")
            if identifier is None:
                continue
            if identifier in seen:
                report.add(
                    "ids.duplicate",
                    path,
                    f"{section}[{index}] repeats id {identifier!r}",
                )
            seen.add(identifier)
    frames = document.get("frames")
    if isinstance(frames, list):
        names: set[str] = set()
        for index, frame in enumerate(frames):
            if not isinstance(frame, dict):
                continue
            name = frame.get("name")
            if name is None:
                continue
            if name in names:
                report.add("ids.duplicate", path, f"frames[{index}] repeats name {name!r}")
            names.add(name)


def _validate_entry(
    root: Path,
    entry: dict,
    report: ValidationReport,
    seen_ids: set[str],
) -> ScenarioSummary | None:
    scenario_id = entry["id"]
    if scenario_id in seen_ids:
        report.add("registry.duplicate_id", "registry.yaml", f"duplicate scenario id {scenario_id!r}")
        return None
    seen_ids.add(scenario_id)

    scenario_dir = _resolve_inside(root, entry["path"])
    if scenario_dir is None:
        report.add(
            "path.outside_root",
            "registry.yaml",
            f"{scenario_id}: path {entry['path']!r} escapes the catalog root",
        )
        return None
    if not scenario_dir.is_dir():
        report.add("path.missing", entry["path"], f"{scenario_id}: scenario directory is missing")
        return None
    if scenario_dir.name != scenario_id:
        report.add(
            "path.name_mismatch",
            entry["path"],
            f"{scenario_id}: directory name {scenario_dir.name!r} does not match the id",
        )

    profile_path = _resolve_inside(scenario_dir, entry["profile"])
    if profile_path is None:
        report.add("path.outside_root", entry["path"], f"{scenario_id}: profile path escapes the scenario directory")
        return None
    profile = _load_document(root, profile_path, "profile", report, "scenario profile")
    if profile is None:
        return None

    _check_duplicate_ids(profile, _relative(root, profile_path), report)

    for field in ("id", "version", "domain", "delivery", "verification"):
        if profile.get(field) != entry.get(field):
            report.add(
                "profile.registry_mismatch",
                _relative(root, profile_path),
                f"{field}: registry {entry.get(field)!r} != profile {profile.get(field)!r}",
            )
    if profile.get("id") != scenario_id:
        report.add("profile.id_mismatch", _relative(root, profile_path), "profile id does not match the registry id")

    documents: dict[str, dict] = {}
    for kind, expected_schema in PROFILE_KINDS.items():
        reference = profile["profiles"][kind]
        path = _resolve_inside(scenario_dir, reference)
        if path is None:
            report.add(
                "path.outside_root",
                _relative(root, profile_path),
                f"{kind}: reference {reference!r} escapes the scenario directory",
            )
            continue
        document = _load_document(root, path, kind, report, f"{kind} profile")
        if document is None:
            continue
        documents[kind] = document
        if document.get("schema_version") != expected_schema:
            report.add(
                "profile.schema_version",
                _relative(root, path),
                f"expected {expected_schema!r}, found {document.get('schema_version')!r}",
            )
        expected_id = f"{scenario_id}.{kind}"
        if document.get("id") != expected_id:
            report.add(
                "profile.id_mismatch",
                _relative(root, path),
                f"expected id {expected_id!r}, found {document.get('id')!r}",
            )
        if document.get("version") != profile["version"]:
            report.add(
                "profile.version_mismatch",
                _relative(root, path),
                f"expected version {profile['version']!r}, found {document.get('version')!r}",
            )
        _check_duplicate_ids(document, _relative(root, path), report)

    _validate_cross_references(root, scenario_dir, documents, report)
    _validate_evaluation(root, scenario_dir, documents, report)

    return ScenarioSummary(
        id=scenario_id,
        version=entry["version"],
        path=entry["path"],
        delivery=entry["delivery"],
        verification=entry["verification"],
        profiles=len(documents),
    )


def _validate_cross_references(
    root: Path,
    scenario_dir: Path,
    documents: dict[str, dict],
    report: ValidationReport,
) -> None:
    semantics = documents.get("semantics", {})
    environment = documents.get("environment", {})
    task = documents.get("task", {})

    classes = {item["id"] for item in semantics.get("ontology", [])}
    for attribute in semantics.get("attributes", []):
        for target in attribute.get("applies_to", []):
            if target not in classes:
                report.add(
                    "reference.unknown",
                    _relative(root, scenario_dir / "semantics.yaml"),
                    f"attribute {attribute['id']!r} refers to unknown class {target!r}",
                )
    for relation in semantics.get("relations", []):
        for role in ("subject", "object"):
            for target in relation.get(role, []):
                if target not in classes:
                    report.add(
                        "reference.unknown",
                        _relative(root, scenario_dir / "semantics.yaml"),
                        f"relation {relation['id']!r} {role} refers to unknown class {target!r}",
                    )

    frames = {frame["name"] for frame in environment.get("frames", [])}
    stations = {station["id"] for station in environment.get("stations", [])}
    for station in environment.get("stations", []):
        if station.get("frame") not in frames:
            report.add(
                "reference.unknown",
                _relative(root, scenario_dir / "environment.yaml"),
                f"station {station['id']!r} refers to unknown frame {station.get('frame')!r}",
            )
    for zone in environment.get("zones", []):
        if zone.get("frame") not in frames:
            report.add(
                "reference.unknown",
                _relative(root, scenario_dir / "environment.yaml"),
                f"zone {zone['id']!r} refers to unknown frame {zone.get('frame')!r}",
            )

    goal = task.get("goal", {})
    for role in ("target_class", "destination"):
        value = goal.get(role)
        if value is not None and value not in classes:
            report.add(
                "reference.unknown",
                _relative(root, scenario_dir / "task.yaml"),
                f"goal {role} {value!r} is not declared in the semantic ontology",
            )
    destination = goal.get("destination")
    if destination is not None and stations and destination not in stations:
        report.add(
            "reference.unknown",
            _relative(root, scenario_dir / "task.yaml"),
            f"goal destination {destination!r} is not a declared station",
        )


def _validate_evaluation(
    root: Path,
    scenario_dir: Path,
    documents: dict[str, dict],
    report: ValidationReport,
) -> None:
    evaluation = documents.get("evaluation")
    if not evaluation:
        return
    path = _relative(root, scenario_dir / "evaluation.yaml")
    for metric in evaluation.get("metrics", []):
        status = metric.get("threshold_status")
        threshold = metric.get("threshold")
        if status == "not_set" and threshold is not None:
            report.add("evaluation.threshold", path, f"metric {metric['id']!r} is not_set but has a threshold")
        if status == "fixed" and threshold is None:
            report.add("evaluation.threshold", path, f"metric {metric['id']!r} is fixed but has no threshold")


def validate_root(root: Path) -> ValidationReport:
    """Validate a catalog root: registry, every scenario and every profile."""

    resolved = root.resolve()
    report = ValidationReport(root=str(resolved))
    if not resolved.is_dir():
        report.add("root.missing", str(resolved), "catalog root is not a directory")
        return report

    registry_path = resolved / "registry.yaml"
    registry = _load_document(resolved, registry_path, "registry", report, "scenario registry")
    if registry is None:
        return report

    seen_ids: set[str] = set()
    for entry in registry["scenarios"]:
        summary = _validate_entry(resolved, entry, report, seen_ids)
        if summary is not None:
            report.scenarios.append(summary)
    return report


def load_registry(root: Path) -> tuple[list[dict], list]:
    """Load and schema-validate the registry without walking the scenarios."""

    resolved = root.resolve()
    report = ValidationReport(root=str(resolved))
    registry = _load_document(resolved, resolved / "registry.yaml", "registry", report, "scenario registry")
    if registry is None:
        return [], report.issues
    return list(registry["scenarios"]), report.issues


def load_profile(root: Path, scenario_id: str) -> dict:
    """Load one scenario profile after registry and schema checks."""

    resolved = root.resolve()
    entries, issues = load_registry(resolved)
    if issues:
        raise ScenarioError(resolved / "registry.yaml", "registry is invalid; run validate first")
    for entry in entries:
        if entry["id"] != scenario_id:
            continue
        scenario_dir = _resolve_inside(resolved, entry["path"])
        if scenario_dir is None:
            raise ScenarioError(resolved / "registry.yaml", f"{scenario_id}: path escapes the catalog root")
        path = _resolve_inside(scenario_dir, entry["profile"])
        if path is None:
            raise ScenarioError(scenario_dir, f"{scenario_id}: profile path escapes the scenario directory")
        profile = _load_document(resolved, path, "profile", ValidationReport(root=str(resolved)), "scenario profile")
        if profile is None:
            raise ScenarioError(path, "scenario profile is invalid; run validate first")
        return profile
    raise ScenarioError(resolved / "registry.yaml", f"unknown scenario id {scenario_id!r}")
