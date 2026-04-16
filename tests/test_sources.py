"""Tests for sources.py — local data extraction functions."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

import pytest

from badgeshield.sources import (
    get_version,
    get_license,
    get_python_requires,
    get_git_branch,
    get_git_tag,
    get_git_commit_count,
    get_git_status,
    get_lines_of_code,
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


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

import shutil as _shutil

def _init_git_repo(path: Path, tag: Optional[str] = None) -> bool:
    """Initialise a minimal git repo. Returns False if git unavailable or commit fails."""
    import subprocess as _sp
    if not _shutil.which("git"):
        return False
    _sp.run(["git", "init"], cwd=str(path), capture_output=True)
    _sp.run(["git", "config", "user.email", "t@t.com"], cwd=str(path), capture_output=True)
    _sp.run(["git", "config", "user.name", "T"], cwd=str(path), capture_output=True)
    (path / "README.md").write_text("hi", encoding="utf-8")
    _sp.run(["git", "add", "."], cwd=str(path), capture_output=True)
    r = _sp.run(["git", "commit", "-m", "init"], cwd=str(path), capture_output=True)
    if r.returncode != 0:
        return False
    if tag:
        _sp.run(["git", "tag", tag], cwd=str(path), capture_output=True)
    return True


def test_get_git_branch(tmp_path):
    if not _init_git_repo(tmp_path):
        pytest.skip("git unavailable or commit failed")
    branch = get_git_branch(tmp_path)
    assert branch in ("main", "master", "HEAD")  # default varies by git config

def test_get_git_tag_with_tag(tmp_path):
    if not _init_git_repo(tmp_path, tag="1.0.0"):
        pytest.skip("git unavailable or commit failed")
    assert get_git_tag(tmp_path) == "1.0.0"

def test_get_git_tag_no_tags_returns_untagged(tmp_path):
    if not _init_git_repo(tmp_path):
        pytest.skip("git unavailable or commit failed")
    assert get_git_tag(tmp_path) == "untagged"

def test_get_git_commit_count(tmp_path):
    if not _init_git_repo(tmp_path):
        pytest.skip("git unavailable or commit failed")
    count = get_git_commit_count(tmp_path)
    assert count.isdigit() and int(count) >= 1

def test_get_git_status_clean(tmp_path):
    if not _init_git_repo(tmp_path):
        pytest.skip("git unavailable or commit failed")
    assert get_git_status(tmp_path) == "clean"

def test_get_git_status_dirty(tmp_path):
    if not _init_git_repo(tmp_path):
        pytest.skip("git unavailable or commit failed")
    (tmp_path / "dirty.txt").write_text("change", encoding="utf-8")
    assert get_git_status(tmp_path) == "dirty"

def test_get_git_status_non_repo_returns_unknown(tmp_path):
    """Non-git directory returns 'unknown', never 'clean' (would be a false positive)."""
    assert get_git_status(tmp_path) == "unknown"

def test_git_raises_runtime_error_when_git_missing(tmp_path, monkeypatch):
    """All git functions raise RuntimeError (not FileNotFoundError) when git not on PATH."""
    import subprocess as _sp2
    import badgeshield.sources as src_mod
    def raise_file_not_found(*args, **kwargs):
        raise FileNotFoundError("git not found")
    monkeypatch.setattr(_sp2, "run", raise_file_not_found)
    with pytest.raises(RuntimeError, match="git is not installed"):
        src_mod.get_git_branch(tmp_path)


def test_get_git_status_raises_runtime_error_when_git_missing(tmp_path, monkeypatch):
    """get_git_status raises RuntimeError (not FileNotFoundError) when git not on PATH."""
    import subprocess as _sp3
    def raise_file_not_found(*args, **kwargs):
        raise FileNotFoundError("git not found")
    monkeypatch.setattr(_sp3, "run", raise_file_not_found)
    from badgeshield.sources import get_git_status
    with pytest.raises(RuntimeError, match="git is not installed"):
        get_git_status(tmp_path)


# ---------------------------------------------------------------------------
# get_lines_of_code
# ---------------------------------------------------------------------------

def test_get_lines_of_code_basic(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\ny = 2\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("z = 3\n", encoding="utf-8")
    assert get_lines_of_code(tmp_path) == "3"

def test_get_lines_of_code_excludes_dirs(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "hidden.py").write_text("y = 2\n" * 100, encoding="utf-8")
    assert get_lines_of_code(tmp_path) == "1"

def test_get_lines_of_code_extensions_filter(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "b.js").write_text("let x = 1;\nlet y = 2;\n", encoding="utf-8")
    assert get_lines_of_code(tmp_path, extensions=(".js",)) == "2"

def test_get_lines_of_code_no_match_returns_zero(tmp_path):
    (tmp_path / "a.txt").write_text("hello\n", encoding="utf-8")
    assert get_lines_of_code(tmp_path) == "0"

def test_get_lines_of_code_blank_lines_not_counted(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n\n\ny = 2\n", encoding="utf-8")
    assert get_lines_of_code(tmp_path) == "2"

def test_get_lines_of_code_formatted_with_commas(tmp_path):
    for i in range(1200):
        (tmp_path / f"f{i}.py").write_text("x = 1\n", encoding="utf-8")
    result = get_lines_of_code(tmp_path)
    assert "," in result  # e.g. "1,200"


# ---------------------------------------------------------------------------
# get_test_results
# ---------------------------------------------------------------------------

JUNIT_ALL_PASS = """<?xml version="1.0"?>
<testsuite tests="5" failures="0" errors="0">
  <testcase name="test_a"/><testcase name="test_b"/>
  <testcase name="test_c"/><testcase name="test_d"/>
  <testcase name="test_e"/>
</testsuite>"""

JUNIT_WITH_FAILURES = """<?xml version="1.0"?>
<testsuite tests="10" failures="2" errors="1">
  <testcase name="test_a"/>
  <testcase name="test_b"><failure>bad</failure></testcase>
</testsuite>"""

def test_get_test_results_all_pass(tmp_path):
    from badgeshield.sources import get_test_results
    f = tmp_path / "junit.xml"
    f.write_text(JUNIT_ALL_PASS, encoding="utf-8")
    assert get_test_results(f) == "5 passed"

def test_get_test_results_with_failures(tmp_path):
    from badgeshield.sources import get_test_results
    f = tmp_path / "junit.xml"
    f.write_text(JUNIT_WITH_FAILURES, encoding="utf-8")
    result = get_test_results(f)
    assert "failed" in result

def test_get_test_results_missing_file(tmp_path):
    from badgeshield.sources import get_test_results
    with pytest.raises(FileNotFoundError):
        get_test_results(tmp_path / "nonexistent.xml")

def test_get_test_results_malformed_xml(tmp_path):
    from badgeshield.sources import get_test_results
    f = tmp_path / "bad.xml"
    f.write_text("<not valid xml", encoding="utf-8")
    with pytest.raises(ET.ParseError):
        get_test_results(f)

def test_get_test_results_non_junit_xml(tmp_path):
    from badgeshield.sources import get_test_results
    f = tmp_path / "other.xml"
    f.write_text("<project><name>foo</name></project>", encoding="utf-8")
    with pytest.raises(ValueError, match="JUnit"):
        get_test_results(f)

# ---------------------------------------------------------------------------
# get_coverage
# ---------------------------------------------------------------------------

COVERAGE_XML = """<?xml version="1.0"?>
<coverage line-rate="0.82" branch-rate="0.75" version="7.0">
</coverage>"""

def test_get_coverage_returns_percentage(tmp_path):
    from badgeshield.sources import get_coverage
    f = tmp_path / "coverage.xml"
    f.write_text(COVERAGE_XML, encoding="utf-8")
    assert get_coverage(f) == "82%"

def test_get_coverage_missing_file(tmp_path):
    from badgeshield.sources import get_coverage
    with pytest.raises(FileNotFoundError):
        get_coverage(tmp_path / "missing.xml")
