"""Read-only compatibility check: scenario requirements vs device capabilities.

The check consumes a ``jcheng.scenario_requirements.v1`` document and a device
capability document. It never reads a device profile repository, never talks to
a robot and never grants deployment authority. A compatible result means only
that the declared capability identifiers and parameters satisfy the declared
requirements; it is not a safety or deployment approval.

Device capability document forms accepted by :func:`check`:

* a list of entries: ``[{"id": "manipulation.arm.reach_m", "parameters": {...}}]``
* a mapping keyed by capability id: ``{"manipulation.arm.reach_m": {...}}``
* a wrapper with metadata and a ``capabilities`` member::

      {"scenario_id": "ore_sorting", "scenario_version": "0.1.0",
       "content_hash": "sha256:...", "capabilities": {...}}

A mapping entry may be a bare parameter mapping, ``{"parameters": {...}}`` or a
boolean/``{"supported": false}`` availability flag.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

REQUIREMENTS_SCHEMA = "jcheng.scenario_requirements.v1"
CONTENT_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
CAPABILITY_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
REFERENCE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._@:+-]{0,127}$")
SCENARIO_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")

RESERVED_ENTRY_KEYS = frozenset({"available", "evidence", "id", "parameters", "supported", "verification"})


class CompatibilityError(Exception):
    """The requirements or device capability document is malformed."""


@dataclass(frozen=True)
class CompatibilityFinding:
    """One explicit compatibility finding."""

    code: str
    capability: str | None
    message: str

    def to_dict(self) -> dict[str, object]:
        return {"code": self.code, "capability": self.capability, "message": self.message}

    def __getitem__(self, key: str) -> object:
        return self.to_dict()[key]


@dataclass(frozen=True)
class CompatibilityResult:
    """Deterministic result of one requirements-to-capabilities comparison."""

    scenario_id: str
    scenario_version: str
    content_hash: str
    device_id: str | None
    device_version: str | None
    status: str
    errors: tuple[CompatibilityFinding, ...]
    warnings: tuple[CompatibilityFinding, ...]

    @property
    def ok(self) -> bool:
        return not self.errors

    def __bool__(self) -> bool:
        return self.ok

    @property
    def deployable(self) -> bool:
        """Compatibility is never a deployment authorization."""

        return False

    def to_dict(self) -> dict[str, object]:
        result = {
            "compatible": "pass",
            "compatible_with_warnings": "warn",
            "incompatible": "fail",
        }[self.status]
        return {
            "result": result,
            "status": self.status,
            "scenario_id": self.scenario_id,
            "scenario_version": self.scenario_version,
            "content_hash": self.content_hash,
            "device_id": self.device_id,
            "device_version": self.device_version,
            "deployable": False,
            "errors": [finding.to_dict() for finding in self.errors],
            "warnings": [finding.to_dict() for finding in self.warnings],
        }

    def __getitem__(self, key: str) -> object:
        return self.to_dict()[key]


@dataclass(frozen=True)
class _Requirement:
    capability: str
    required: bool
    parameters: dict[str, Any]


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _exact_equal(expected: Any, actual: Any) -> bool:
    if isinstance(expected, bool) or isinstance(actual, bool):
        return type(expected) is type(actual) and expected == actual
    if _is_number(expected):
        return _is_number(actual) and math.isclose(float(expected), float(actual), rel_tol=1e-9, abs_tol=1e-12)
    if isinstance(expected, str):
        return isinstance(actual, str) and expected == actual
    if expected is None:
        return actual is None
    if isinstance(expected, list):
        return (
            isinstance(actual, list)
            and len(expected) == len(actual)
            and all(_exact_equal(item, other) for item, other in zip(expected, actual))
        )
    if isinstance(expected, Mapping):
        return (
            isinstance(actual, Mapping)
            and set(expected) == set(actual)
            and all(_exact_equal(expected[key], actual[key]) for key in expected)
        )
    return expected == actual


def _value_matches(expected: Any, actual: Any) -> bool:
    """Compare one required parameter value with a device value.

    A mapping with exactly ``op`` and ``value`` is the ecosystem comparison
    form used by the offline consumer harness. A mapping with only
    ``min``/``max`` members is a numeric range. Every other value must match
    exactly, with a small tolerance for floats.
    """

    if isinstance(expected, Mapping) and set(expected) == {"op", "value"}:
        op = expected["op"]
        reference = expected["value"]
        if not isinstance(op, str) or op not in {">=", "<=", ">", "<", "==", "!="}:
            raise CompatibilityError(f"unsupported comparison operator {op!r}")
        if isinstance(reference, Mapping):
            raise CompatibilityError("a comparison value must be a scalar or a flat list")
        if op in {">=", "<=", ">", "<"}:
            if not _is_number(actual) or not _is_number(reference):
                return False
            if op == ">=":
                return actual >= reference
            if op == "<=":
                return actual <= reference
            if op == ">":
                return actual > reference
            return actual < reference
        if op == "==":
            return _exact_equal(reference, actual)
        return not _exact_equal(reference, actual)

    if isinstance(expected, Mapping) and expected and set(expected) <= {"min", "max"}:
        if not _is_number(actual):
            return False
        for bound in ("min", "max"):
            if bound in expected and not _is_number(expected[bound]):
                raise CompatibilityError(f"parameter bound {bound!r} must be numeric, found {expected[bound]!r}")
        if "min" in expected and actual < expected["min"]:
            return False
        if "max" in expected and actual > expected["max"]:
            return False
        return True
    return _exact_equal(expected, actual)


def _parameter_mismatches(expected: Mapping[str, Any], actual: Mapping[str, Any]) -> list[str]:
    messages: list[str] = []
    for key in sorted(expected):
        if key not in actual:
            messages.append(f"parameter {key!r} is missing from the device capability")
            continue
        if not _value_matches(expected[key], actual[key]):
            messages.append(
                f"parameter {key!r} requires {expected[key]!r}, device declares {actual[key]!r}"
            )
    return messages


def _parse_requirements(requirements: Any) -> tuple[dict[str, Any], list[_Requirement]]:
    if not isinstance(requirements, Mapping):
        raise CompatibilityError("requirements document must be a mapping")
    if requirements.get("schema") != REQUIREMENTS_SCHEMA:
        raise CompatibilityError(
            f"requirements schema must be {REQUIREMENTS_SCHEMA!r}, found {requirements.get('schema')!r}"
        )
    scenario_id = requirements.get("scenario_id")
    if not isinstance(scenario_id, str) or not SCENARIO_ID_RE.fullmatch(scenario_id):
        raise CompatibilityError(f"requirements scenario_id is not a scenario identifier: {scenario_id!r}")
    scenario_version = requirements.get("scenario_version")
    if not isinstance(scenario_version, str) or not VERSION_RE.fullmatch(scenario_version):
        raise CompatibilityError(f"requirements scenario_version is not a semantic version: {scenario_version!r}")
    digest = requirements.get("content_hash")
    if not isinstance(digest, str) or not CONTENT_HASH_RE.fullmatch(digest):
        raise CompatibilityError(f"requirements content_hash is not sha256:<64 hex>: {digest!r}")
    for field in ("task_id", "evaluation_id"):
        value = requirements.get(field)
        if not isinstance(value, str) or not REFERENCE_ID_RE.fullmatch(value):
            raise CompatibilityError(f"requirements {field} is not a reference id: {value!r}")
        if "@" not in value:
            raise CompatibilityError(f"requirements {field} must carry an @version suffix: {value!r}")
        name, reference_version = value.rsplit("@", 1)
        if not name or not VERSION_RE.fullmatch(reference_version):
            raise CompatibilityError(f"requirements {field} must be <id>@MAJOR.MINOR.PATCH: {value!r}")
        if reference_version != scenario_version:
            raise CompatibilityError(
                f"requirements {field} version does not match scenario_version {scenario_version!r}: {value!r}"
            )
    constraints = requirements.get("constraints")
    if not isinstance(constraints, list):
        raise CompatibilityError("requirements constraints must be a list")
    for index, item in enumerate(constraints):
        if not isinstance(item, Mapping):
            raise CompatibilityError(f"constraints[{index}] must be a mapping")
        if not isinstance(item.get("id"), str) or not item["id"]:
            raise CompatibilityError(f"constraints[{index}].id must be a non-empty string")
        if not isinstance(item.get("statement"), str) or not item["statement"]:
            raise CompatibilityError(f"constraints[{index}].statement must be a non-empty string")
    provenance = requirements.get("provenance")
    if not isinstance(provenance, Mapping) or not provenance:
        raise CompatibilityError("requirements provenance must be a non-empty mapping")
    for field in ("source_path", "generated_by"):
        if field in provenance and (not isinstance(provenance.get(field), str) or not provenance.get(field)):
            raise CompatibilityError(f"requirements provenance.{field} must be a non-empty string")

    raw_capabilities = requirements.get("capabilities")
    if not isinstance(raw_capabilities, list) or not raw_capabilities:
        raise CompatibilityError("requirements capabilities must be a non-empty list")
    parsed: list[_Requirement] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_capabilities):
        if not isinstance(item, Mapping):
            raise CompatibilityError(f"capabilities[{index}] must be a mapping")
        capability = item.get("id")
        if not isinstance(capability, str) or not CAPABILITY_ID_RE.fullmatch(capability):
            raise CompatibilityError(f"capabilities[{index}].id is not a dotted capability id: {capability!r}")
        if capability in seen:
            raise CompatibilityError(f"duplicate capability {capability!r} in requirements")
        seen.add(capability)
        required = item.get("required")
        if not isinstance(required, bool):
            raise CompatibilityError(f"capabilities[{index}].required must be a boolean")
        parameters = item.get("parameters", {})
        if parameters is None:
            parameters = {}
        if not isinstance(parameters, Mapping):
            raise CompatibilityError(f"capabilities[{index}].parameters must be a mapping")
        parsed.append(_Requirement(capability=capability, required=required, parameters=dict(parameters)))
    return dict(requirements), parsed


def _parse_device_entry(raw: Any, context: str) -> tuple[bool, dict[str, Any]]:
    if raw is None:
        return True, {}
    if isinstance(raw, bool):
        return raw, {}
    if not isinstance(raw, Mapping):
        raise CompatibilityError(f"{context} must be a mapping, boolean or null")
    if "id" in raw and raw["id"] != context:
        raise CompatibilityError(f"{context}.id must match the capability key, found {raw['id']!r}")

    supported = True
    if "supported" in raw:
        if not isinstance(raw["supported"], bool):
            raise CompatibilityError(f"{context}.supported must be a boolean")
        supported = raw["supported"]
    if "available" in raw:
        if not isinstance(raw["available"], bool):
            raise CompatibilityError(f"{context}.available must be a boolean")
        supported = supported and raw["available"]

    parameters = raw.get("parameters")
    if parameters is None:
        parameters = {
            key: value for key, value in raw.items() if key not in RESERVED_ENTRY_KEYS and key not in {"available", "supported"}
        }
    elif not isinstance(parameters, Mapping):
        raise CompatibilityError(f"{context}.parameters must be a mapping")
    return supported, dict(parameters)


def _normalise_device(device_capabilities: Any) -> tuple[dict[str, Any], dict[str, tuple[bool, dict[str, Any]]]]:
    if device_capabilities is None:
        payload: Any = {}
        raw: Any = {}
    elif isinstance(device_capabilities, list):
        payload = device_capabilities
        raw = {}
    elif isinstance(device_capabilities, Mapping):
        raw = device_capabilities
        if "capabilities" in raw:
            payload = raw["capabilities"]
        elif "device_capabilities" in raw:
            payload = raw["device_capabilities"]
        else:
            payload = raw
    else:
        raise CompatibilityError("device capabilities must be a mapping or a list")

    metadata: dict[str, Any] = {}
    if isinstance(raw, Mapping):
        for key in ("scenario_id", "scenario_version", "content_hash", "device_id", "device_version", "source_device"):
            if key in raw and key != "capabilities":
                metadata[key] = raw[key]
        scenario_ref = raw.get("scenario_ref")
        if scenario_ref is not None:
            if not isinstance(scenario_ref, Mapping):
                raise CompatibilityError("scenario_ref must be a mapping")
            for key in ("scenario_id", "scenario_version", "content_hash"):
                if key in scenario_ref and key not in metadata:
                    metadata[key] = scenario_ref[key]
    for key, value in metadata.items():
        if not isinstance(value, str) or not value:
            raise CompatibilityError(f"device metadata {key} must be a non-empty string")
    if "device_id" not in metadata and "source_device" in metadata:
        metadata["device_id"] = metadata["source_device"]

    entries: dict[str, tuple[bool, dict[str, Any]]] = {}
    if isinstance(payload, Mapping):
        for capability, raw_entry in payload.items():
            if not isinstance(capability, str) or not CAPABILITY_ID_RE.fullmatch(capability):
                raise CompatibilityError(f"device capability id is not a dotted identifier: {capability!r}")
            entries[capability] = _parse_device_entry(raw_entry, capability)
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            if isinstance(item, str):
                capability, raw_entry = item, None
            elif isinstance(item, Mapping):
                capability = item.get("id")
                if not isinstance(capability, str):
                    raise CompatibilityError(f"device_capabilities[{index}].id must be a string")
                raw_entry = {key: value for key, value in item.items() if key != "id"}
            else:
                raise CompatibilityError(f"device_capabilities[{index}] must be a string or mapping")
            if not CAPABILITY_ID_RE.fullmatch(capability):
                raise CompatibilityError(f"device capability id is not a dotted identifier: {capability!r}")
            if capability in entries:
                raise CompatibilityError(f"duplicate device capability {capability!r}")
            entries[capability] = _parse_device_entry(raw_entry, capability)
    else:
        raise CompatibilityError("device capabilities must be a mapping or a list")
    return metadata, entries


def _finding(code: str, capability: str | None, message: str) -> CompatibilityFinding:
    return CompatibilityFinding(code=code, capability=capability, message=message)


def _ordered(findings: list[CompatibilityFinding]) -> tuple[CompatibilityFinding, ...]:
    return tuple(sorted(findings, key=lambda item: (item.capability or "", item.code, item.message)))


def check(requirements: Any, device_capabilities: Any) -> CompatibilityResult:
    """Check one requirements document against one device capability document.

    Errors are returned, not raised, for a capability mismatch. A malformed
    input document raises :class:`CompatibilityError`.
    """

    document, parsed = _parse_requirements(requirements)
    metadata, device = _normalise_device(device_capabilities)

    errors: list[CompatibilityFinding] = []
    warnings: list[CompatibilityFinding] = []

    if "scenario_id" in metadata and metadata["scenario_id"] != document["scenario_id"]:
        errors.append(
            _finding(
                "INCOMPATIBLE_SCENARIO",
                None,
                f"device refers to scenario {metadata['scenario_id']!r}, requirements are for {document['scenario_id']!r}",
            )
        )
    if "scenario_version" in metadata and metadata["scenario_version"] != document["scenario_version"]:
        errors.append(
            _finding(
                "INCOMPATIBLE_VERSION",
                None,
                f"device refers to scenario version {metadata['scenario_version']!r}, "
                f"requirements are {document['scenario_version']!r}",
            )
        )
    # A standalone device snapshot also has a content_hash, but it is that
    # artifact's own hash, not a reference to the scenario. Only compare the
    # hash when the device document also identifies the scenario or version.
    scenario_pinned = "scenario_id" in metadata or "scenario_version" in metadata
    if scenario_pinned and "content_hash" in metadata and metadata["content_hash"] != document["content_hash"]:
        errors.append(
            _finding(
                "INCOMPATIBLE_CONTENT_HASH",
                None,
                f"device refers to content hash {metadata['content_hash']!r}, "
                f"requirements are {document['content_hash']!r}",
            )
        )

    required_ids = {requirement.capability for requirement in parsed}
    for requirement in parsed:
        entry = device.get(requirement.capability)
        if entry is None:
            if requirement.required:
                errors.append(
                    _finding(
                        "MISSING_REQUIRED_CAPABILITY",
                        requirement.capability,
                        "required capability is not declared by the device",
                    )
                )
            else:
                warnings.append(
                    _finding(
                        "OPTIONAL_CAPABILITY_MISSING",
                        requirement.capability,
                        "optional capability is not declared by the device",
                    )
                )
            continue
        supported, device_parameters = entry
        if not supported:
            if requirement.required:
                errors.append(
                    _finding(
                        "MISSING_REQUIRED_CAPABILITY",
                        requirement.capability,
                        "capability is declared but marked unsupported or unavailable",
                    )
                )
            else:
                warnings.append(
                    _finding(
                        "OPTIONAL_CAPABILITY_MISSING",
                        requirement.capability,
                        "optional capability is declared but marked unsupported or unavailable",
                    )
                )
            continue
        for message in _parameter_mismatches(requirement.parameters, device_parameters):
            errors.append(_finding("INCOMPATIBLE_PARAMETER", requirement.capability, message))

    for capability in device:
        if capability not in required_ids:
            errors.append(
                _finding(
                    "UNKNOWN_CAPABILITY",
                    capability,
                    "device declares a capability that is not in the scenario requirements",
                )
            )

    ordered_errors = _ordered(errors)
    ordered_warnings = _ordered(warnings)
    if ordered_errors:
        status = "incompatible"
    elif ordered_warnings:
        status = "compatible_with_warnings"
    else:
        status = "compatible"

    return CompatibilityResult(
        scenario_id=document["scenario_id"],
        scenario_version=document["scenario_version"],
        content_hash=document["content_hash"],
        device_id=metadata.get("device_id"),
        device_version=metadata.get("device_version"),
        status=status,
        errors=ordered_errors,
        warnings=ordered_warnings,
    )
