"""Command-line entry point for the offline SCEN catalog."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .compatibility import CompatibilityError, check
from .loader import ScenarioError, load_json, load_yaml
from .registry import load_profile, load_registry, validate_root
from .requirements import build_requirements, requirements_json


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jcheng-scenarios",
        description="Offline SCEN scenario catalog: validate, list and inspect declarative profiles.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate the registry and every scenario")
    validate.add_argument("--root", default=".", help="catalog root containing registry.yaml")
    validate.add_argument("--json", action="store_true", help="print the machine-readable report")

    listing = subparsers.add_parser("list", help="list registered scenarios")
    listing.add_argument("--root", default=".", help="catalog root containing registry.yaml")
    listing.add_argument("--json", action="store_true", help="print JSON")

    show = subparsers.add_parser("show", help="show one scenario profile")
    show.add_argument("scenario_id")
    show.add_argument("--root", default=".", help="catalog root containing registry.yaml")
    show.add_argument("--json", action="store_true", help="print JSON")

    requirements = subparsers.add_parser(
        "requirements",
        help="emit the jcheng.scenario_requirements.v1 document",
    )
    requirements.add_argument("scenario_id")
    requirements.add_argument("--root", default=".", help="catalog root containing registry.yaml")
    requirements.add_argument("--json", action="store_true", help="print JSON")
    requirements.add_argument(
        "--output",
        metavar="PATH",
        help="write the JSON document to PATH for an offline consumer",
    )

    compatibility = subparsers.add_parser(
        "compatibility",
        help="check scenario requirements against a device capability document",
    )
    compatibility.add_argument("scenario_id")
    compatibility.add_argument("--root", default=".", help="catalog root containing registry.yaml")
    compatibility.add_argument(
        "--device-capabilities",
        required=True,
        metavar="PATH",
        help="JSON or YAML device capability document",
    )
    compatibility.add_argument("--json", action="store_true", help="print JSON")

    return parser


def _print_issues(issues: Sequence) -> None:
    for issue in issues:
        print(f"[{issue.code}] {issue.path}: {issue.message}", file=sys.stderr)


def _validate(root: Path, as_json: bool) -> int:
    report = validate_root(root)
    if as_json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    elif report.ok:
        profiles = sum(item.profiles for item in report.scenarios)
        print(f"validated {len(report.scenarios)} scenario(s), {profiles} profile(s), 0 errors")
    else:
        print(f"validation failed: {len(report.issues)} error(s)", file=sys.stderr)
        _print_issues(report.issues)
    return 0 if report.ok else 1


def _list(root: Path, as_json: bool) -> int:
    entries, issues = load_registry(root)
    if issues:
        if as_json:
            print(json.dumps({"result": "fail", "issues": [issue.to_dict() for issue in issues]}, indent=2))
        else:
            print("registry is invalid", file=sys.stderr)
            _print_issues(issues)
        return 1
    if as_json:
        print(json.dumps({"result": "pass", "scenarios": entries}, indent=2, sort_keys=True))
        return 0
    for entry in entries:
        print(
            "\t".join(
                [
                    entry["id"],
                    entry["version"],
                    entry["delivery"],
                    entry["verification"],
                    entry["path"],
                ]
            )
        )
    return 0


def _show(root: Path, scenario_id: str, as_json: bool) -> int:
    try:
        profile = load_profile(root, scenario_id)
    except ScenarioError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    if as_json:
        print(json.dumps(profile, indent=2, sort_keys=True))
        return 0
    print(f"id: {profile['id']}")
    print(f"version: {profile['version']}")
    print(f"title: {profile['title']}")
    print(f"domain: {profile['domain']}")
    print(f"delivery: {profile['delivery']}")
    print(f"verification: {profile['verification']}")
    print(f"summary: {profile['summary']}")
    print("profiles:")
    for kind, reference in profile["profiles"].items():
        print(f"  {kind}: {reference}")
    return 0


def _requirements(root: Path, scenario_id: str, as_json: bool, output: str | None) -> int:
    try:
        document = build_requirements(root, scenario_id)
    except ScenarioError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    payload = requirements_json(document)
    if output is not None:
        destination = Path(output)
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(payload, encoding="utf-8")
        except OSError as error:
            print(f"error: cannot write {destination}: {error}", file=sys.stderr)
            return 1
        if not as_json:
            print(f"wrote {destination}")
    if as_json:
        print(payload, end="")
    elif output is None:
        print(f"scenario: {document['scenario_id']}@{document['scenario_version']}")
        print(f"content_hash: {document['content_hash']}")
        print(f"task: {document['task_id']}")
        print(f"evaluation: {document['evaluation_id']}")
        print(f"capabilities: {len(document['capabilities'])}")
        print(f"constraints: {len(document['constraints'])}")
    return 0


def _load_device_document(path: Path) -> object:
    if path.suffix.lower() in {".yaml", ".yml"}:
        return load_yaml(path)
    return load_json(path)


def _compatibility(
    root: Path,
    scenario_id: str,
    device_path: Path,
    as_json: bool,
) -> int:
    try:
        document = build_requirements(root, scenario_id)
    except ScenarioError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    try:
        device_document = _load_device_document(device_path)
        result = check(document, device_document)
    except (ScenarioError, CompatibilityError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if as_json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print(f"result: {result.status}")
        print(f"scenario: {result.scenario_id}@{result.scenario_version}")
        print(f"content_hash: {result.content_hash}")
        device = result.device_id or "undeclared"
        if result.device_version:
            device = f"{device}@{result.device_version}"
        print(f"device: {device}")
        print(f"deployable: {str(result.deployable).lower()} (compatibility is not deployment authorization)")
        for finding in result.errors:
            target = f" {finding.capability}" if finding.capability else ""
            print(f"[{finding.code}]{target}: {finding.message}", file=sys.stderr)
        for finding in result.warnings:
            target = f" {finding.capability}" if finding.capability else ""
            print(f"[{finding.code}]{target}: {finding.message}", file=sys.stderr)
    return 0 if result.ok else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    root = Path(arguments.root)
    if arguments.command == "validate":
        return _validate(root, arguments.json)
    if arguments.command == "list":
        return _list(root, arguments.json)
    if arguments.command == "show":
        return _show(root, arguments.scenario_id, arguments.json)
    if arguments.command == "requirements":
        return _requirements(root, arguments.scenario_id, arguments.json, arguments.output)
    if arguments.command == "compatibility":
        return _compatibility(
            root,
            arguments.scenario_id,
            Path(arguments.device_capabilities),
            arguments.json,
        )
    parser.error(f"unknown command: {arguments.command}")
    return 2
