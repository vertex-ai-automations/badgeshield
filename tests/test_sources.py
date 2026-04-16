"""Tests for sources.py — local data extraction functions."""
from __future__ import annotations

from pathlib import Path

import pytest

from badgeshield.sources import (
    get_version,
    get_license,
    get_python_requires,
)


def test_get_version_from_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
    assert get_version(tmp_path) == "1.2.3"

def test_get_version_from_setup_py(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[build-system]\n", encoding="utf-8")
    (tmp_path / "setup.py").write_text('setup(name="pkg", version="2.0.0")\n', encoding="utf-8")
    assert get_version(tmp_path) == "2.0.0"

def test_get_version_from_version_py(tmp_path):
    (tmp_path / "setup.py").write_text("setup(name='pkg', version=get_version())\n", encoding="utf-8")
    (tmp_path / "version.py").write_text('__version__ = "3.1.4"\n', encoding="utf-8")
    assert get_version(tmp_path) == "3.1.4"

def test_get_version_from_git_tag(tmp_path):
    """Step 4: git tag fallback when no file-based sources exist."""
    import shutil
    import subprocess as _sp
    if not shutil.which("git"):
        pytest.skip("git not available")
    r = _sp.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    _sp.run(["git", "config", "user.email", "t@t.com"], cwd=str(tmp_path), capture_output=True)
    _sp.run(["git", "config", "user.name", "T"], cwd=str(tmp_path), capture_output=True)
    (tmp_path / "f.txt").write_text("hi", encoding="utf-8")
    _sp.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
    commit_result = _sp.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), capture_output=True)
    if commit_result.returncode != 0:
        pytest.skip("git commit failed — check git config")
    _sp.run(["git", "tag", "4.5.6"], cwd=str(tmp_path), capture_output=True)
    assert get_version(tmp_path) == "4.5.6"

def test_get_version_fallback_unknown(tmp_path):
    assert get_version(tmp_path) == "unknown"

def test_get_version_setup_py_dynamic_falls_through(tmp_path):
    (tmp_path / "setup.py").write_text("setup(name='pkg', version=get_version())\n", encoding="utf-8")
    assert get_version(tmp_path) == "unknown"

def test_get_license_from_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nlicense = {text = "MIT"}\n', encoding="utf-8")
    assert get_license(tmp_path) == "MIT"

def test_get_license_from_setup_py(tmp_path):
    (tmp_path / "setup.py").write_text('setup(name="pkg", license="Apache-2.0")\n', encoding="utf-8")
    assert get_license(tmp_path) == "Apache-2.0"

def test_get_license_fallback(tmp_path):
    assert get_license(tmp_path) == "unknown"

def test_get_python_requires_from_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.8"\n', encoding="utf-8")
    assert get_python_requires(tmp_path) == ">=3.8"

def test_get_python_requires_from_setup_py(tmp_path):
    (tmp_path / "setup.py").write_text('setup(name="pkg", python_requires=">=3.9")\n', encoding="utf-8")
    assert get_python_requires(tmp_path) == ">=3.9"

def test_get_python_requires_fallback(tmp_path):
    assert get_python_requires(tmp_path) == "unknown"
