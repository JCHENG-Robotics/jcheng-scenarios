"""Versioned JSON Schema loading and document validation.

Schemas are repository-local SCEN schemas, not jcheng-interfaces contracts.
Each schema is self-contained: cross-file references are resolved by the
scenario loader, not by JSON Schema ``$ref`` remotes.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import jsonschema

from .loader import load_json
from .model import Issue

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"

SCHEMA_FILES: dict[str, str] = {
    "registry": "scenario-registry.v1.schema.json",
    "profile": "scenario-profile.v1.schema.json",
    "environment": "environment-profile.v1.schema.json",
    "semantics": "semantic-profile.v1.schema.json",
    "task": "task-specification.v1.schema.json",
    "capability_requirements": "capability-requirements.v1.schema.json",
    "operational_constraints": "operational-constraints.v1.schema.json",
    "evaluation": "evaluation-specification.v1.schema.json",
}


def schema_path(kind: str) -> Path:
    try:
        return SCHEMA_DIR / SCHEMA_FILES[kind]
    except KeyError as error:
        raise KeyError(f"unknown schema kind: {kind}") from error


@lru_cache(maxsize=None)
def load_schema(kind: str) -> dict:
    return load_json(schema_path(kind))


@lru_cache(maxsize=None)
def _validator(kind: str) -> jsonschema.Draft202012Validator:
    schema = load_schema(kind)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def _location(error: jsonschema.ValidationError) -> str:
    parts = "$"
    for part in error.absolute_path:
        parts += f"[{part}]" if isinstance(part, int) else f".{part}"
    return parts


def validate_document(kind: str, document: object, path: str) -> list[Issue]:
    """Validate one document and return deterministic, path-qualified issues."""

    errors = list(_validator(kind).iter_errors(document))
    errors.sort(key=lambda error: (list(error.absolute_path), error.message))
    return [
        Issue(code="document.schema", path=path, message=f"{_location(error)}: {error.message}")
        for error in errors
    ]


def check_all_schemas() -> list[str]:
    """Return schema problems; an empty list means every schema is valid."""

    problems: list[str] = []
    for kind, filename in SCHEMA_FILES.items():
        path = SCHEMA_DIR / filename
        if not path.is_file():
            problems.append(f"{filename}: missing (kind {kind})")
            continue
        try:
            schema = load_json(path)
            jsonschema.Draft202012Validator.check_schema(schema)
        except Exception as error:  # schema files are data; report, do not crash
            problems.append(f"{filename}: {error}")
    return problems
