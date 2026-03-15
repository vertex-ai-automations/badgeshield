import json

import pytest
from typer.testing import CliRunner

from badgeshield.generate_badge_cli import app

runner = CliRunner(mix_stderr=False)


# ---------------------------------------------------------------------------
# single command
# ---------------------------------------------------------------------------

def test_single_happy_path(tmp_path):
    """Single badge generation with valid args should create the SVG file."""
    result = runner.invoke(app, [
        "single",
        "--left-text", "Build",
        "--left-color", "GREEN",
        "--badge-name", "build.svg",
        "--output-path", str(tmp_path),
    ])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "build.svg").exists()


def test_single_invalid_color(tmp_path):
    """An unrecognised color name should print an Error panel and exit 1."""
    result = runner.invoke(app, [
        "single",
        "--left-text", "Build",
        "--left-color", "NOTACOLOR",
        "--badge-name", "build.svg",
        "--output-path", str(tmp_path),
    ])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_single_missing_svg_suffix(tmp_path):
    """badge-name without .svg suffix must exit 1."""
    result = runner.invoke(app, [
        "single",
        "--left-text", "Build",
        "--left-color", "GREEN",
        "--badge-name", "no_suffix",
        "--output-path", str(tmp_path),
    ])
    assert result.exit_code == 1


def test_single_invalid_template(tmp_path):
    """An invalid template name must exit 1."""
    result = runner.invoke(app, [
        "single",
        "--left-text", "Build",
        "--left-color", "GREEN",
        "--badge-name", "build.svg",
        "--template", "BOGUS",
        "--output-path", str(tmp_path),
    ])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_single_invalid_frame(tmp_path):
    """An invalid frame name must exit 1."""
    result = runner.invoke(app, [
        "single",
        "--left-text", "Build",
        "--left-color", "GREEN",
        "--badge-name", "build.svg",
        "--template", "CIRCLE_FRAME",
        "--frame", "BADFRAME",
        "--output-path", str(tmp_path),
    ])
    assert result.exit_code == 1
    assert "Error" in result.output


# ---------------------------------------------------------------------------
# batch command
# ---------------------------------------------------------------------------

def test_batch_happy_path(tmp_path):
    """Batch with valid config JSON should create all SVG files."""
    config = [
        {"badge_name": "a.svg", "left_text": "alpha", "left_color": "#001122"},
        {"badge_name": "b.svg", "left_text": "beta", "left_color": "BLUE"},
    ]
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config))
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    result = runner.invoke(app, [
        "batch",
        str(config_file),
        "--output-path", str(out_dir),
    ])
    assert result.exit_code == 0, result.output
    assert (out_dir / "a.svg").exists()
    assert (out_dir / "b.svg").exists()


def test_batch_malformed_json(tmp_path):
    """Malformed JSON config must exit 1 with an error message."""
    config_file = tmp_path / "bad.json"
    config_file.write_text("{broken")

    result = runner.invoke(app, [
        "batch",
        str(config_file),
    ])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_batch_missing_config_file(tmp_path):
    """Non-existent config file path must exit 1 (Typer exists=True)."""
    result = runner.invoke(app, [
        "batch",
        str(tmp_path / "nonexistent.json"),
    ])
    assert result.exit_code != 0


def test_batch_circle_frame_without_frame(tmp_path):
    """CIRCLE_FRAME template without frame key in config must exit 1."""
    config = [
        {"badge_name": "f.svg", "left_text": "framed", "left_color": "#abcdef"},
    ]
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config))
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    result = runner.invoke(app, [
        "batch",
        str(config_file),
        "--template", "CIRCLE_FRAME",
        "--output-path", str(out_dir),
    ])
    assert result.exit_code == 1
