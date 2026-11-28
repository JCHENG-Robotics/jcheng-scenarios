"""Generate the consumer document ``jcheng.scenario_requirements.v1``.

The document is a flattened, JSON-safe view of the identifiers, capability
requirements and task constraints owned by this repository. It is generated
from the four declaration files named in the Phase 2 design:

* ``scenario.yaml``
* ``capability-requirements.yaml``
* ``task.yaml``
* ``evaluation.yaml``

Two hashes are distinct:

* ``provenance.scenario_content_hash`` is the canonical hash of the scenario
  declaration documents (see :mod:`jcheng_scenarios.hashing`).
* ``content_hash`` is the artifact self-hash: SHA-256 over the canonical JSON
  encoding of this document with ``content_hash`` removed. This is the
  convention the offline consumer harness uses to detect a stale or edited
  pinned copy.

It contains no execution plan and no device claim. A missing document, an
identifier mismatch or a version mismatch is an error, never a default value.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from . import __version__
from .hashing import content_hash
from .loader import ScenarioError, load_yaml
from .registry import _resolve_inside, load_registry
from .schema import validate_document

REQUIREMENTS_SCHEMA = "jcheng.scenario_requirements.v1"
GENERATOR = f"jcheng-scenarios.requirements {__version__}"

PROFILE_KINDS: dict[str, str] = {
    "capability_requirements": "jcheng.scenario.capability_requirements.v1",
    "task": "jcheng.scenario.task.v1",
    "evaluation": "jcheng.scenario.evaluation.v1",
}

REQUIRED_PROFILES = ("capability_requirements", "task", "evaluation")


class RequirementsError(ScenarioError):
    """A scenario cannot produce a consistent requirements document."""

    def __init__(self, path: Path | str, code: str, message: str) -> None:
        self.code = code
        super().__init__(path, f"{code}: {message}")


def _load_profile(
    scenario_dir: Path,
    profile: Mapping[str, Any],
    kind: str,
    scenario_id: str,
    scenario_version: str,
) -> tuple[Path, dict]:
    references = profile.get("profiles")
    if not isinstance(references, dict):
        raise RequirementsError(scenario_dir / "scenario.yaml", "profile.reference", "profiles must be a mapping")
    reference = references.get(kind)
    if not isinstance(reference, str) or not reference:
        raise RequirementsError(
            scenario_dir / "scenario.yaml",
            "profile.missing_reference",
            f"scenario profile does not reference a {kind} document",
        )
    path = _resolve_inside(scenario_dir, reference)
    if path is None:
        raise RequirementsError(
            scenario_dir / "scenario.yaml",
            "profile.reference",
            f"{kind}: reference {reference!r} escapes the scenario directory",
        )
    if not path.is_file():
        raise RequirementsError(path, "document.missing", f"missing {kind} profile")

    document = load_yaml(path)
    if not isinstance(document, dict):
        raise RequirementsError(path, "document.type", f"{kind} profile must be a mapping")

    issues = validate_document(kind, document, str(path))
    if issues:
        detail = "; ".join(issue.message for issue in issues)
        raise RequirementsError(path, "profile.schema", detail)

    expected_schema = PROFILE_KINDS[kind]
    if document.get("schema_version") != expected_schema:
        raise RequirementsError(
            path,
            "profile.schema_version",
            f"expected {expected_schema!r}, found {document.get('schema_version')!r}",
        )
    expected_id = f"{scenario_id}.{kind}"
    if document.get("id") != expected_id:
        raise RequirementsError(
            path,
            "profile.id",
            f"expected id {expected_id!r}, found {document.get('id')!r}",
        )
    if document.get("version") != scenario_version:
        raise RequirementsError(
            path,
            "profile.version",
            f"expected version {scenario_version!r}, found {document.get('version')!r}",
        )
    return path, document


def _capabilities(document: dict, path: Path) -> list[dict[str, Any]]:
    capabilities: list[dict[str, Any]] = []
    requirement_ids: set[str] = set()
    capability_ids: set[str] = set()
    sections = (
        ("device_requirements", "device"),
        ("algorithm_requirements", "algorithm"),
    )
    for section, requirement_owner in sections:
        items = document.get(section)
        if not isinstance(items, list) or not items:
            raise RequirementsError(path, "capability.section", f"{section} must be a non-empty list")
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise RequirementsError(path, "capability.type", f"{section}[{index}] must be a mapping")
            requirement_id = item.get("id")
            capability_id = item.get("capability")
            if not isinstance(requirement_id, str) or not requirement_id:
                raise RequirementsError(path, "capability.id", f"{section}[{index}] has no requirement id")
            if not isinstance(capability_id, str) or not capability_id:
                raise RequirementsError(
                    path,
                    "capability.id",
                    f"{section}[{index}] ({requirement_id}) has no capability id",
                )
            if requirement_id in requirement_ids:
                raise RequirementsError(
                    path,
                    "requirement.duplicate",
                    f"duplicate requirement id {requirement_id!r}",
                )
            if capability_id in capability_ids:
                raise RequirementsError(
                    path,
                    "capability.duplicate",
                    f"duplicate capability {capability_id!r}",
                )
            requirement_ids.add(requirement_id)
            capability_ids.add(capability_id)

            entry: dict[str, Any] = {
                "id": capability_id,
                "requirement_id": requirement_id,
                "requirement_owner": requirement_owner,
                "required": True,
                "statement": item["requirement"],
                "verification": item["verification"],
            }
            if requirement_owner == "device":
                entry["role"] = item["role"]
                entry["interface"] = item["interface"]
                threshold = item.get("threshold")
                if threshold is not None:
                    entry["threshold"] = dict(threshold)
            else:
                owner = item.get("owner")
                if not isinstance(owner, str) or not owner:
                    raise RequirementsError(
                        path,
                        "capability.owner",
                        f"{requirement_id}: an algorithm requirement needs an owner",
                    )
                entry["deferred_to"] = owner
            capabilities.append(entry)
    return capabilities


def _constraints(document: dict, path: Path) -> list[dict[str, Any]]:
    items = document.get("constraints")
    if not isinstance(items, list) or not items:
        raise RequirementsError(path, "constraint.missing", "task specification has no constraints")
    constraints: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise RequirementsError(path, "constraint.type", f"constraints[{index}] must be a mapping")
        constraints.append({"id": item.get("id"), "statement": item.get("statement")})
    return constraints


def artifact_content_hash(document: Mapping[str, Any]) -> str:
    """Return the canonical self-hash of a requirements document.

    The encoding matches the offline consumer harness: sorted keys, no
    whitespace, ASCII escaping, JSON-safe values and ``content_hash`` removed.
    """

    body = {key: value for key, value in document.items() if key != "content_hash"}
    try:
        canonical = json.dumps(
            body,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise RequirementsError("<requirements>", "document.json", f"document is not JSON-safe: {error}") from error
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_requirements(root: Path, scenario_id: str) -> dict[str, Any]:
    """Build the ``jcheng.scenario_requirements.v1`` document for one scenario."""

    resolved = Path(root).resolve()
    entries, issues = load_registry(resolved)
    if issues:
        raise RequirementsError(resolved / "registry.yaml", "registry.invalid", "registry is invalid; run validate first")
    entry = next((item for item in entries if item["id"] == scenario_id), None)
    if entry is None:
        raise RequirementsError(resolved / "registry.yaml", "scenario.unknown", f"unknown scenario id {scenario_id!r}")

    scenario_dir = _resolve_inside(resolved, entry["path"])
    if scenario_dir is None:
        raise RequirementsError(
            resolved / "registry.yaml",
            "scenario.path",
            f"{scenario_id}: path escapes the catalog root",
        )
    if not scenario_dir.is_dir():
        raise RequirementsError(scenario_dir, "scenario.missing", f"{scenario_id}: scenario directory is missing")

    profile_path = _resolve_inside(scenario_dir, entry["profile"])
    if profile_path is None:
        raise RequirementsError(scenario_dir, "scenario.profile", f"{scenario_id}: profile path escapes the scenario directory")
    if not profile_path.is_file():
        raise RequirementsError(profile_path, "document.missing", "missing scenario profile")
    profile = load_yaml(profile_path)
    if not isinstance(profile, dict):
        raise RequirementsError(profile_path, "document.type", "scenario profile must be a mapping")
    profile_issues = validate_document("profile", profile, str(profile_path))
    if profile_issues:
        detail = "; ".join(issue.message for issue in profile_issues)
        raise RequirementsError(profile_path, "profile.schema", detail)

    scenario_version = entry["version"]
    if profile.get("id") != scenario_id:
        raise RequirementsError(
            profile_path,
            "profile.id",
            f"expected id {scenario_id!r}, found {profile.get('id')!r}",
        )
    if profile.get("version") != scenario_version:
        raise RequirementsError(
            profile_path,
            "profile.version",
            f"registry version {scenario_version!r} != profile version {profile.get('version')!r}",
        )

    documents: dict[str, dict] = {}
    paths: dict[str, Path] = {}
    for kind in REQUIRED_PROFILES:
        paths[kind], documents[kind] = _load_profile(
            scenario_dir,
            profile,
            kind,
            scenario_id,
            scenario_version,
        )

    capabilities = _capabilities(documents["capability_requirements"], paths["capability_requirements"])
    constraints = _constraints(documents["task"], paths["task"])
    source_hash = content_hash(resolved, scenario_id)

    document: dict[str, Any] = {
        "schema": REQUIREMENTS_SCHEMA,
        "scenario_id": scenario_id,
        "scenario_version": scenario_version,
        "vocabulary_status": documents["capability_requirements"]["vocabulary_status"],
        "content_hash": "",
        "task_id": f"{documents['task']['id']}@{scenario_version}",
        "evaluation_id": f"{documents['evaluation']['id']}@{scenario_version}",
        "capabilities": capabilities,
        "constraints": constraints,
        "provenance": {
            "source_path": scenario_dir.relative_to(resolved).as_posix(),
            "generated_by": GENERATOR,
            "scenario_content_hash": source_hash,
        },
    }
    document["content_hash"] = artifact_content_hash(document)
    return document


def requirements_json(document: Mapping[str, Any]) -> str:
    """Serialise a requirements document deterministically for file consumption."""

    return json.dumps(document, ensure_ascii=False, indent=2) + "\n"
