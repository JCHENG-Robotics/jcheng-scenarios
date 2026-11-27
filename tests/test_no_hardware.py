"""Static boundary check: the catalog must not reach DDS, devices or runtime execution.

Only executable and declarative sources are scanned; documentation may name the
robot, DDS or the system layer.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = (ROOT / "src", ROOT / "scripts", ROOT / "scenarios", ROOT / "schemas")
SUFFIXES = {".py", ".yaml", ".yml", ".sh", ".json", ".toml"}

FORBIDDEN = (
    "rclpy",
    "rospy",
    "ros2",
    "/dev/",
    "pyserial",
    "serial.serial",
    "socketcan",
    "can0",
    "pigpio",
    "rpi.gpio",
    "cv2.videocapture",
    "subprocess",
    "os.system",
    "popen",
    "socket.socket",
    "requests.",
    "urllib.request",
)


def _source_files():
    for directory in SCAN_DIRS:
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.suffix in SUFFIXES:
                yield path


def test_no_hardware_dds_or_execution_tokens_in_sources() -> None:
    problems = []
    for path in _source_files():
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        text = text.replace("/dev/null", "")
        for token in FORBIDDEN:
            if token in text:
                problems.append(f"{path.relative_to(ROOT)}: {token}")
    assert not problems, "hardware/DDS/execution tokens found:\n" + "\n".join(problems)


def test_manifest_has_no_topics_or_devices() -> None:
    manifest = yaml.safe_load((ROOT / "capability.yaml").read_text(encoding="utf-8"))
    assert manifest["topics"] == {"subscribes": [], "publishes": []}
    assert manifest["hardware_access"]["kind"] == "none"
    assert manifest["motion_authority"] == "none"
    assert manifest["control_path"] == "none"


def test_catalog_contains_no_runtime_code() -> None:
    package = ROOT / "src" / "jcheng_scenarios"
    modules = sorted(path.name for path in package.glob("*.py"))
    assert modules == ["__init__.py", "__main__.py", "cli.py", "loader.py", "model.py", "registry.py", "schema.py"]
