"""Documentation standard, status vocabulary and relative links."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _text(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_readme_language_switch_and_status_block() -> None:
    lines = _text("README.md").splitlines()
    assert lines[0] == "# jcheng-scenarios"
    assert lines[2] == "**English** | [简体中文](README.zh-CN.md)"
    text = _text("README.md")
    assert "> Status: **Experimental**" in text
    assert "| Hardware access |" in text
    assert "## Validation status" in text
    assert "## Related repositories" in text


def test_chinese_readme_is_a_full_translation() -> None:
    lines = _text("README.zh-CN.md").splitlines()
    assert lines[0] == "# jcheng-scenarios"
    assert lines[2] == "**简体中文** | [English](README.md)"
    text = _text("README.zh-CN.md")
    assert "本文为英文主文档的中文对照" in text
    assert "## 范围与边界" in text
    assert "## 验证状态" in text


def test_changelog_is_keep_a_changelog() -> None:
    text = _text("CHANGELOG.md")
    assert text.startswith("# Changelog")
    assert "## [Unreleased]" in text
    assert "## [0.1.0] — 2026-11-27" in text
    for group in ("### Added", "### Changed"):
        assert group in text


def test_roadmap_covers_the_long_term_versions() -> None:
    text = _text("ROADMAP.md")
    for version in ("v0.1.x", "v0.2.x", "v0.3.x", "v0.4.x", "v0.5.x", "v1.0.0"):
        assert version in text
    assert "## Out of scope" in text
    assert "## Dependencies" in text


def test_acceptance_declares_the_levels_and_no_hardware() -> None:
    text = _text("ACCEPTANCE.md")
    for level in ("L0", "L1", "L2", "L3", "L4", "L5"):
        assert level in text
    assert "Not applicable" in text
    assert "No motion command" in text
    assert "Sign-off" in text


def test_asset_audit_does_not_move_files() -> None:
    text = _text("docs/ASSET_AUDIT_20261127.md")
    assert "No file was moved" in text
    assert "jcheng-perception" in text
    assert "jcheng-scenarios" in text


def test_scen_layer_document_names_responsibilities_and_consumers() -> None:
    text = _text("docs/SCEN_LAYER.md")
    for consumer in (
        "jcheng-devices",
        "jcheng-applications",
        "jcheng-perception",
        "jcheng-simulation",
        "jcheng-benchmark",
        "jcheng-system",
        "jcheng-interfaces",
    ):
        assert consumer in text


def _documents() -> list[Path]:
    return [
        ROOT / "README.md",
        ROOT / "README.zh-CN.md",
        ROOT / "ROADMAP.md",
        ROOT / "CHANGELOG.md",
        ROOT / "ACCEPTANCE.md",
        ROOT / "LICENSE-REVIEW.md",
        *sorted((ROOT / "docs").glob("*.md")),
        ROOT / "scenarios" / "README.md",
        ROOT / "evidence" / "README.md",
        ROOT / "evidence" / "20261127_scaffold" / "README.md",
    ]


def test_relative_links_resolve() -> None:
    problems: list[str] = []
    for document in _documents():
        text = document.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = target.split("#", 1)[0].split("?", 1)[0]
            if not path:
                continue
            if not (document.parent / path).resolve().exists():
                problems.append(f"{document.relative_to(ROOT)}: {target}")
    assert not problems, "broken relative links:\n" + "\n".join(problems)
