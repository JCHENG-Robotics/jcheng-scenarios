"""CLI exit codes and machine-readable output."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from jcheng_scenarios.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_validate_succeeds(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", "--root", str(ROOT)]) == 0
    output = capsys.readouterr().out
    assert "validated 1 scenario(s), 6 profile(s), 0 errors" in output


def test_validate_json_report(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", "--root", str(ROOT), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["result"] == "pass"
    assert report["counts"] == {"errors": 0, "profiles": 6, "scenarios": 1}
    assert report["scenarios"][0]["id"] == "ore_sorting"


def test_list_succeeds(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["list", "--root", str(ROOT)]) == 0
    output = capsys.readouterr().out
    assert output.split("\t")[0] == "ore_sorting"


def test_list_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["list", "--root", str(ROOT), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["result"] == "pass"
    assert payload["scenarios"][0]["id"] == "ore_sorting"


def test_show_succeeds(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["show", "ore_sorting", "--root", str(ROOT)]) == 0
    output = capsys.readouterr().out
    assert "id: ore_sorting" in output
    assert "task: task.yaml" in output


def test_unknown_scenario_fails(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["show", "unknown", "--root", str(ROOT)]) == 1
    assert "unknown scenario id" in capsys.readouterr().err


def test_missing_root_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", "--root", str(tmp_path / "absent")]) == 1
    assert "not a directory" in capsys.readouterr().err


def test_missing_registry_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", "--root", str(tmp_path)]) == 1
    assert "missing scenario registry" in capsys.readouterr().err


def test_version_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as error:
        main(["--version"])
    assert error.value.code == 0
    assert "jcheng-scenarios 0.1.0" in capsys.readouterr().out
