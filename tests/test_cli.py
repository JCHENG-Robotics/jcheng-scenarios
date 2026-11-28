"""CLI exit codes and machine-readable output."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from jcheng_scenarios.cli import main
from jcheng_scenarios.requirements import build_requirements

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


def test_requirements_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["requirements", "ore_sorting", "--root", str(ROOT), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "jcheng.scenario_requirements.v1"
    assert payload["scenario_id"] == "ore_sorting"
    assert payload["content_hash"].startswith("sha256:")
    assert len(payload["capabilities"]) == 8


def test_requirements_output_file_is_consumable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    destination = tmp_path / "nested" / "requirements.json"
    assert (
        main(
            [
                "requirements",
                "ore_sorting",
                "--root",
                str(ROOT),
                "--output",
                str(destination),
            ]
        )
        == 0
    )
    assert "wrote" in capsys.readouterr().out
    assert json.loads(destination.read_text(encoding="utf-8")) == build_requirements(ROOT, "ore_sorting")


def test_requirements_unknown_scenario_fails(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["requirements", "unknown", "--root", str(ROOT)]) == 1
    assert "scenario.unknown" in capsys.readouterr().err


def _device_document(**overrides: object) -> dict:
    requirements = build_requirements(ROOT, "ore_sorting")
    device = {
        "scenario_id": requirements["scenario_id"],
        "scenario_version": requirements["scenario_version"],
        "content_hash": requirements["content_hash"],
        "device_id": "hiwonder.armpi-ultra",
        "device_version": "0.1.0",
        "capabilities": {item["id"]: {} for item in requirements["capabilities"]},
    }
    device.update(overrides)
    return device


def test_compatibility_passes_with_a_complete_device_document(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "device.json"
    path.write_text(json.dumps(_device_document()), encoding="utf-8")
    assert (
        main(
            [
                "compatibility",
                "ore_sorting",
                "--root",
                str(ROOT),
                "--device-capabilities",
                str(path),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "result: compatible" in output
    assert "deployable: false" in output


def test_compatibility_json_reports_missing_required(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    device = _device_document()
    device["capabilities"].pop("manipulation.arm.reach_m")
    path = tmp_path / "device.json"
    path.write_text(json.dumps(device), encoding="utf-8")
    assert (
        main(
            [
                "compatibility",
                "ore_sorting",
                "--root",
                str(ROOT),
                "--device-capabilities",
                str(path),
                "--json",
            ]
        )
        == 1
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["result"] == "fail"
    assert payload["deployable"] is False
    assert payload["errors"][0]["code"] == "MISSING_REQUIRED_CAPABILITY"


def test_compatibility_rejects_a_malformed_device_document(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "device.json"
    path.write_text(json.dumps({"manipulation.arm.reach_m": 42}), encoding="utf-8")
    assert (
        main(
            [
                "compatibility",
                "ore_sorting",
                "--root",
                str(ROOT),
                "--device-capabilities",
                str(path),
            ]
        )
        == 1
    )
    assert "error:" in capsys.readouterr().err
