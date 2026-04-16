"""Tests for presets.py."""
from __future__ import annotations

import pytest

from badgeshield.presets import PRESETS, Preset


def test_preset_dataclass_fields():
    p = Preset(label="build", color="#555555", right_text="passing")
    assert p.label == "build"
    assert p.right_text == "passing"
    assert p.source is None


def test_all_presets_have_label():
    for name, preset in PRESETS.items():
        assert preset.label, f"Preset '{name}' has empty label"


def test_cosmetic_presets_have_right_text():
    cosmetic_names = [
        "black", "ruff", "flake8", "isort", "mypy",
        "passing", "failing", "stable", "wip", "alpha", "beta", "rc",
        "experimental", "maintained", "deprecated", "archived",
        "library", "cli", "framework", "api",
        "contributions-welcome", "hacktoberfest",
        "cross-platform", "linux", "windows", "macos",
    ]
    for name in cosmetic_names:
        assert name in PRESETS, f"Missing preset: {name}"
        assert PRESETS[name].right_text, f"Cosmetic preset '{name}' missing right_text"


def test_data_wired_presets_have_source():
    """Data-wired presets that resolve via search_path must have source set.
    Note: tests and coverage have source=None because they need CLI-provided file paths.
    """
    search_path_wired = [
        "version", "license", "python", "branch", "tag",
        "commits", "repo-status", "lines",
    ]
    for name in search_path_wired:
        assert name in PRESETS, f"Missing preset: {name}"
        assert PRESETS[name].source is not None, f"Preset '{name}' missing source"

    # tests and coverage have source=None — CLI wraps them with lambdas
    assert PRESETS["tests"].source is None, "tests preset should have source=None"
    assert PRESETS["coverage"].source is None, "coverage preset should have source=None"


def test_preset_registry_size():
    assert len(PRESETS) >= 36


def test_preset_source_callable_protocol(tmp_path):
    """Data-wired presets (excluding tests/coverage/lines) accept search_path."""
    search_only = ["version", "license", "python", "branch", "tag", "commits", "repo-status"]
    for name in search_only:
        preset = PRESETS[name]
        result = preset.source(tmp_path)
        assert isinstance(result, str), f"Preset '{name}' source did not return str"
