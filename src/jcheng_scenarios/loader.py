"""Strict YAML and JSON loading.

The loader rejects duplicate mapping keys: a duplicated field is an authoring
error, not a silent last-wins override. It never constructs arbitrary Python
objects (SafeLoader subclasses only).
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

import yaml


class ScenarioError(Exception):
    """A scenario document could not be read or parsed."""

    def __init__(self, path: Path | str, message: str) -> None:
        self.path = Path(path)
        self.message = message
        super().__init__(f"{self.path}: {message}")


class _UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that fails on duplicate mapping keys."""

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict:
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                mark = key_node.start_mark
                raise ScenarioError(
                    mark.name,
                    f"duplicate mapping key {key!r} at line {mark.line + 1}",
                )
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def _normalise(value: Any) -> Any:
    """Convert implicit YAML dates to ISO 8601 strings.

    An unquoted ``2026-11-27`` is a ``datetime.date`` in PyYAML. The catalog
    treats dates as ISO strings so the JSON Schemas and JSON reports stay
    stable regardless of whether an author quoted the value.
    """

    if isinstance(value, datetime.datetime):
        return value.isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _normalise(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalise(item) for item in value]
    return value


def load_yaml(path: Path) -> Any:
    """Load one YAML document, rejecting duplicate keys."""

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ScenarioError(path, f"cannot read: {error}") from error
    try:
        return _normalise(yaml.load(text, Loader=_UniqueKeyLoader))
    except ScenarioError:
        raise
    except yaml.YAMLError as error:
        raise ScenarioError(path, f"invalid YAML: {error}") from error


def load_json(path: Path) -> Any:
    """Load a JSON document with a path-qualified error."""

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ScenarioError(path, f"cannot read: {error}") from error
    except json.JSONDecodeError as error:
        raise ScenarioError(path, f"invalid JSON: {error}") from error
