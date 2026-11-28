"""Canonical content hashing for scenario declaration documents.

The hash covers the scenario profile plus every sub-profile that the profile
references. It is a pure function of those documents: mappings are ordered by
key, list order is preserved (list order is semantic for goals, metrics and
conditions) and generation timestamps are dropped so a regenerated copy with a
new ``generated_at`` value keeps the same hash.

The digest is used as ``content_hash`` in the generated
``jcheng.scenario_requirements.v1`` document. It is an offline identity aid, not
a signature and not a safety or deployment approval.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .loader import ScenarioError, load_yaml
from .registry import _resolve_inside, load_registry

HASH_PREFIX = "sha256"

#: Fields that describe when a document was generated rather than what it
#: declares. They are removed at every nesting level before serialisation.
NON_SEMANTIC_KEYS = frozenset(
    {
        "exported_at",
        "generated",
        "generated_at",
        "generated_on",
        "generated_time",
        "generated_timestamp",
        "snapshot_at",
        "timestamp",
    }
)


def _canonicalise(value: Any, path: str) -> Any:
    """Return a JSON-safe, key-sorted copy of ``value`` without timestamps."""

    if isinstance(value, dict):
        canonical: dict[str, Any] = {}
        for key in sorted(value, key=str):
            if not isinstance(key, str):
                raise ScenarioError(path, f"non-string mapping key {key!r}")
            if key in NON_SEMANTIC_KEYS:
                continue
            canonical[key] = _canonicalise(value[key], path)
        return canonical
    if isinstance(value, list):
        return [_canonicalise(item, path) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise ScenarioError(path, f"unsupported value type {type(value).__name__}")


def canonical_document(document: Mapping[str, Any], path: str = "<document>") -> dict[str, Any]:
    """Canonicalise one declaration document for hashing or comparison."""

    if not isinstance(document, Mapping):
        raise ScenarioError(path, "declaration document must be a mapping")
    canonical = _canonicalise(dict(document), path)
    if not isinstance(canonical, dict):  # pragma: no cover - defensive
        raise ScenarioError(path, "declaration document must be a mapping")
    return canonical


def declaration_documents(root: Path, scenario_id: str) -> list[tuple[str, dict]]:
    """Load the scenario profile and every declaration it references.

    Returns ``(repository_relative_path, document)`` pairs ordered by path.
    The profile path comes from ``registry.yaml``; each sub-profile path comes
    from ``scenario.yaml``. A missing, escaping or duplicate reference is an
    error, so a hash always covers the complete declared document set.
    """

    resolved = Path(root).resolve()
    entries, issues = load_registry(resolved)
    if issues:
        raise ScenarioError(resolved / "registry.yaml", "registry is invalid; run validate first")
    entry = next((item for item in entries if item["id"] == scenario_id), None)
    if entry is None:
        raise ScenarioError(resolved / "registry.yaml", f"unknown scenario id {scenario_id!r}")

    scenario_dir = _resolve_inside(resolved, entry["path"])
    if scenario_dir is None:
        raise ScenarioError(resolved / "registry.yaml", f"{scenario_id}: path escapes the catalog root")
    if not scenario_dir.is_dir():
        raise ScenarioError(scenario_dir, f"{scenario_id}: scenario directory is missing")

    profile_path = _resolve_inside(scenario_dir, entry["profile"])
    if profile_path is None:
        raise ScenarioError(scenario_dir, f"{scenario_id}: profile path escapes the scenario directory")
    profile = _load_mapping(profile_path, "scenario profile")

    references = profile.get("profiles")
    if not isinstance(references, dict) or not references:
        raise ScenarioError(profile_path, "scenario profile has no profile references")
    if profile.get("id") != scenario_id:
        raise ScenarioError(profile_path, f"profile id {profile.get('id')!r} does not match {scenario_id!r}")

    documents: dict[str, dict] = {}
    for kind in sorted(references):
        reference = references[kind]
        if not isinstance(reference, str) or not reference:
            raise ScenarioError(profile_path, f"profile reference {kind!r} must be a non-empty string")
        path = _resolve_inside(scenario_dir, reference)
        if path is None:
            raise ScenarioError(profile_path, f"{kind}: reference {reference!r} escapes the scenario directory")
        relative = path.relative_to(scenario_dir).as_posix()
        if relative in documents:
            raise ScenarioError(profile_path, f"duplicate profile reference {relative!r}")
        documents[relative] = _load_mapping(path, f"{kind} profile")

    profile_relative = profile_path.relative_to(scenario_dir).as_posix()
    if profile_relative in documents:
        raise ScenarioError(profile_path, "the scenario profile is also referenced as a sub-profile")
    documents[profile_relative] = profile

    return sorted(documents.items(), key=lambda item: item[0])


def _load_mapping(path: Path, label: str) -> dict:
    if not path.is_file():
        raise ScenarioError(path, f"missing {label}")
    document = load_yaml(path)
    if not isinstance(document, dict):
        raise ScenarioError(path, f"{label} must be a mapping")
    return document


def canonical_payload(root: Path, scenario_id: str) -> bytes:
    """Return the canonical byte stream that is hashed.

    Each document is framed by its scenario-relative path so moving the same
    content to a different file changes the digest.
    """

    parts: list[bytes] = []
    for relative, document in declaration_documents(root, scenario_id):
        canonical = canonical_document(document, relative)
        serialised = json.dumps(
            canonical,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        parts.append(relative.encode("utf-8") + b"\0" + serialised.encode("utf-8"))
    return b"\n".join(parts) + b"\n"


def content_hash(root: Path, scenario_id: str) -> str:
    """Return ``sha256:<hex>`` over the scenario's canonical declaration set."""

    digest = hashlib.sha256(canonical_payload(root, scenario_id)).hexdigest()
    return f"{HASH_PREFIX}:{digest}"
