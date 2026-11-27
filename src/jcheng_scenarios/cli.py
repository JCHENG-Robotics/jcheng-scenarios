"""Command-line entry point for the offline SCEN catalog."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .loader import ScenarioError
from .registry import load_profile, load_registry, validate_root


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
    parser.error(f"unknown command: {arguments.command}")
    return 2
