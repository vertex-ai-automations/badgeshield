"""CLI tests for --format flag, preset, and presets subcommands."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from badgeshield.generate_badge_cli import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# _format_snippet helper
# ---------------------------------------------------------------------------

def test_format_snippet_markdown():
    from badgeshield.generate_badge_cli import _format_snippet
    assert _format_snippet("badge.svg", "build", "markdown") == "![build](badge.svg)"


def test_format_snippet_html():
    from badgeshield.generate_badge_cli import _format_snippet
    assert _format_snippet("badge.svg", "build", "html") == '<img src="badge.svg" alt="build" />'


def test_format_snippet_rst():
    from badgeshield.generate_badge_cli import _format_snippet
    assert "image::" in _format_snippet("badge.svg", "build", "rst")


def test_format_snippet_invalid_format():
    from badgeshield.generate_badge_cli import _format_snippet
    with pytest.raises(ValueError, match="Unknown format"):
        _format_snippet("badge.svg", "build", "pdf")


# ---------------------------------------------------------------------------
# single --format
# ---------------------------------------------------------------------------

def test_single_with_format_markdown(tmp_path):
    result = runner.invoke(app, [
        "single",
        "--left_text", "build",
        "--left_color", "GREEN",
        "--badge_name", "build.svg",
        "--output_path", str(tmp_path),
        "--format", "markdown",
    ])
    assert result.exit_code == 0
    assert "![build](" in result.output
    assert (tmp_path / "build.svg").exists()


def test_single_with_format_rst(tmp_path):
    result = runner.invoke(app, [
        "single",
        "--left_text", "build",
        "--left_color", "GREEN",
        "--badge_name", "build.svg",
        "--output_path", str(tmp_path),
        "--format", "rst",
    ])
    assert result.exit_code == 0
    assert ".. image::" in result.output


def test_single_with_format_html(tmp_path):
    result = runner.invoke(app, [
        "single",
        "--left_text", "build",
        "--left_color", "GREEN",
        "--badge_name", "build.svg",
        "--output_path", str(tmp_path),
        "--format", "html",
    ])
    assert result.exit_code == 0
    assert "<img src=" in result.output


# ---------------------------------------------------------------------------
# presets list subcommand
# ---------------------------------------------------------------------------

def test_presets_list_renders():
    result = runner.invoke(app, ["presets"])
    assert result.exit_code == 0
    assert "version" in result.output
    assert "passing" in result.output


# ---------------------------------------------------------------------------
# preset single-badge subcommand
# ---------------------------------------------------------------------------

def test_preset_cosmetic_no_args(tmp_path):
    result = runner.invoke(app, [
        "preset", "passing",
        "--output_path", str(tmp_path),
    ])
    assert result.exit_code == 0
    assert (tmp_path / "passing.svg").exists()


def test_preset_default_badge_name(tmp_path):
    """badge_name defaults to {preset-name}.svg."""
    result = runner.invoke(app, [
        "preset", "stable",
        "--output_path", str(tmp_path),
    ])
    assert result.exit_code == 0
    assert (tmp_path / "stable.svg").exists()


def test_preset_override_badge_name(tmp_path):
    result = runner.invoke(app, [
        "preset", "passing",
        "--badge_name", "ci.svg",
        "--output_path", str(tmp_path),
    ])
    assert result.exit_code == 0
    assert (tmp_path / "ci.svg").exists()


def test_preset_unknown_name_exits_1():
    result = runner.invoke(app, ["preset", "nonexistent-preset"])
    assert result.exit_code == 1


def test_preset_with_format(tmp_path):
    result = runner.invoke(app, [
        "preset", "passing",
        "--output_path", str(tmp_path),
        "--format", "markdown",
    ])
    assert result.exit_code == 0
    assert "![" in result.output


def test_preset_data_wired_version(tmp_path):
    """version preset resolves from pyproject.toml in search_path."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "9.9.9"\n', encoding="utf-8"
    )
    result = runner.invoke(app, [
        "preset", "version",
        "--search_path", str(tmp_path),
        "--output_path", str(tmp_path),
    ])
    assert result.exit_code == 0
    svg = (tmp_path / "version.svg").read_text(encoding="utf-8")
    assert "9.9.9" in svg


def test_preset_tests_requires_junit(tmp_path):
    """tests preset without --junit exits with code 1."""
    result = runner.invoke(app, [
        "preset", "tests",
        "--output_path", str(tmp_path),
    ])
    assert result.exit_code == 1


def test_preset_tests_with_junit(tmp_path):
    junit = tmp_path / "junit.xml"
    junit.write_text(
        '<?xml version="1.0"?><testsuite tests="5" failures="0"></testsuite>',
        encoding="utf-8",
    )
    result = runner.invoke(app, [
        "preset", "tests",
        "--junit", str(junit),
        "--output_path", str(tmp_path),
    ])
    assert result.exit_code == 0
    assert (tmp_path / "tests.svg").exists()


# ---------------------------------------------------------------------------
# preset --all
# ---------------------------------------------------------------------------

def test_preset_all_generates_cosmetic_badges(tmp_path):
    result = runner.invoke(app, [
        "preset", "--all",
        "--output_path", str(tmp_path),
    ])
    assert result.exit_code == 0
    assert (tmp_path / "passing.svg").exists()
    assert (tmp_path / "black.svg").exists()


def test_preset_all_with_version_source(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "1.0.0"\n', encoding="utf-8"
    )
    result = runner.invoke(app, [
        "preset", "--all",
        "--search_path", str(tmp_path),
        "--output_path", str(tmp_path),
    ])
    assert result.exit_code == 0
    assert (tmp_path / "version.svg").exists()


def test_preset_all_skips_unresolved(tmp_path, monkeypatch):
    """Data-wired presets returning 'unknown'/'untagged' are skipped."""
    from badgeshield.presets import PRESETS
    monkeypatch.setattr(PRESETS["version"], "source", lambda p: "unknown")
    monkeypatch.setattr(PRESETS["branch"], "source", lambda p: "unknown")
    result = runner.invoke(app, [
        "preset", "--all",
        "--output_path", str(tmp_path),
    ])
    assert result.exit_code == 0
    assert not (tmp_path / "version.svg").exists()
    assert not (tmp_path / "branch.svg").exists()
    assert (tmp_path / "passing.svg").exists()  # cosmetic still runs


def test_preset_all_zero_badges_exits_1(tmp_path, monkeypatch):
    """Empty preset registry → exit code 1."""
    import badgeshield.generate_badge_cli as cli_mod
    monkeypatch.setattr(cli_mod, "PRESETS", {})
    result = runner.invoke(app, [
        "preset", "--all",
        "--output_path", str(tmp_path),
    ])
    assert result.exit_code == 1


def test_preset_all_format_markdown(tmp_path):
    result = runner.invoke(app, [
        "preset", "--all",
        "--output_path", str(tmp_path),
        "--format", "markdown",
    ])
    assert result.exit_code == 0
    assert "![" in result.output
