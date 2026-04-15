# Pitch & High-Impact Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local data-aware badge generation (no network calls), 36 predefined presets, embed snippet output, and a "why badgeshield?" pitch to README and docs.

**Architecture:** Two new modules (`sources.py` for local data extraction, `presets.py` for the preset registry) feed into new `preset` and `presets` CLI subcommands. A `--format` flag is added to all existing subcommands. No changes to `badge_generator.py`.

**Tech Stack:** Python stdlib (`subprocess`, `xml.etree.ElementTree`, `tomllib`/`tomli`, `pathlib`, `re`), Typer, Rich, existing `BadgeGenerator`, `coverage.py`.

**Important — Python 3.8 compatibility:** This package supports Python `>=3.8`. Do NOT use `match` statements (Python 3.10+) or `tomllib` (Python 3.11+). Use `if/elif/else` chains and the `tomli` third-party library for TOML parsing (already available via `pyproject.toml` build deps, but not in `requirements.txt` — use `tomllib` with a fallback to `tomli` via try/except import). For Python 3.8/3.9 use `try: import tomllib except ImportError: import tomli as tomllib`.

**Important — test runner issue:** `test_coverage.py` and `test_generate_badge_cli.py` currently fail on collection due to `CliRunner(mix_stderr=False)` incompatibility with the installed Typer version. New CLI tests should use `CliRunner()` without `mix_stderr`. Run only `tests/test_badge_generator.py` and the new test files to verify — don't worry about the pre-existing failures.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/badgeshield/sources.py` | Create | All local data extraction functions |
| `src/badgeshield/presets.py` | Create | `Preset` dataclass + `PRESETS` registry |
| `src/badgeshield/generate_badge_cli.py` | Modify | Add `--format`, `preset`, `presets` subcommands |
| `src/badgeshield/__init__.py` | Modify | Export new public symbols |
| `tests/test_sources.py` | Create | Unit tests for all `sources.py` functions |
| `tests/test_presets.py` | Create | Unit tests for preset registry |
| `tests/test_preset_cli.py` | Create | CLI tests for `preset`, `presets`, `--format` |
| `README.md` | Modify | Add "Why badgeshield?" pitch section at top |
| `docs/index.md` | Modify | Mirror pitch |
| `docs/getting-started/cli_usage.md` | Modify | Add `preset`/`presets` examples |
| `docs/getting-started/usage.md` | Modify | Add `sources.py` programmatic API examples |
| `docs/reference/sources.md` | Create | API reference page |
| `docs/reference/presets.md` | Create | Full preset table |
| `mkdocs.yml` | Modify | Wire in two new reference pages |
| `requirements.txt` | Modify | Add `tomli>=2.0; python_version < "3.11"` |

---

## Task 1: Metadata source functions (`get_version`, `get_license`, `get_python_requires`)

**Files:**
- Create: `src/badgeshield/sources.py`
- Create: `tests/test_sources.py`

- [ ] **Step 1: Add `tomli` to requirements**

Edit `requirements.txt` to add:
```
tomli>=2.0; python_version < "3.11"
```

- [ ] **Step 2: Write failing tests for `get_version` (all four resolution steps in isolation)**

Create `tests/test_sources.py`:

```python
"""Tests for sources.py — local data extraction functions."""
from __future__ import annotations

import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

import pytest

from badgeshield.sources import (
    get_version,
    get_license,
    get_python_requires,
)


# ---------------------------------------------------------------------------
# get_version — four isolated steps
# ---------------------------------------------------------------------------

def test_get_version_from_pyproject(tmp_path):
    """Step 1: reads [project] version from pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "1.2.3"\n', encoding="utf-8"
    )
    assert get_version(tmp_path) == "1.2.3"


def test_get_version_from_setup_py(tmp_path):
    """Step 2: reads version= from setup.py when pyproject.toml has none."""
    (tmp_path / "pyproject.toml").write_text("[build-system]\n", encoding="utf-8")
    (tmp_path / "setup.py").write_text(
        'setup(name="pkg", version="2.0.0")\n', encoding="utf-8"
    )
    assert get_version(tmp_path) == "2.0.0"


def test_get_version_from_version_py(tmp_path):
    """Step 3: reads __version__ from version.py when setup.py has no literal."""
    (tmp_path / "setup.py").write_text(
        "setup(name='pkg', version=get_version())\n", encoding="utf-8"
    )
    (tmp_path / "version.py").write_text(
        '__version__ = "3.1.4"\n', encoding="utf-8"
    )
    assert get_version(tmp_path) == "3.1.4"


def test_get_version_fallback_unknown(tmp_path):
    """Step 5: returns 'unknown' when no source resolves."""
    assert get_version(tmp_path) == "unknown"


def test_get_version_setup_py_dynamic_falls_through(tmp_path):
    """setup.py with dynamic version should not match and fall through."""
    (tmp_path / "setup.py").write_text(
        "setup(name='pkg', version=get_version())\n", encoding="utf-8"
    )
    # No version.py, no pyproject version, no git tag → unknown
    assert get_version(tmp_path) == "unknown"


# ---------------------------------------------------------------------------
# get_license
# ---------------------------------------------------------------------------

def test_get_license_from_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nlicense = {text = "MIT"}\n', encoding="utf-8"
    )
    assert get_license(tmp_path) == "MIT"


def test_get_license_from_setup_py(tmp_path):
    (tmp_path / "setup.py").write_text(
        'setup(name="pkg", license="Apache-2.0")\n', encoding="utf-8"
    )
    assert get_license(tmp_path) == "Apache-2.0"


def test_get_license_fallback(tmp_path):
    assert get_license(tmp_path) == "unknown"


# ---------------------------------------------------------------------------
# get_python_requires
# ---------------------------------------------------------------------------

def test_get_python_requires_from_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nrequires-python = ">=3.8"\n', encoding="utf-8"
    )
    assert get_python_requires(tmp_path) == ">=3.8"


def test_get_python_requires_from_setup_py(tmp_path):
    (tmp_path / "setup.py").write_text(
        'setup(name="pkg", python_requires=">=3.9")\n', encoding="utf-8"
    )
    assert get_python_requires(tmp_path) == ">=3.9"


def test_get_python_requires_fallback(tmp_path):
    assert get_python_requires(tmp_path) == "unknown"
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
pytest tests/test_sources.py -v --tb=short
```
Expected: `ImportError: cannot import name 'get_version' from 'badgeshield.sources'`

- [ ] **Step 4: Create `sources.py` with metadata functions**

Create `src/badgeshield/sources.py`:

```python
"""Local data extraction — no network calls."""
from __future__ import annotations

import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]

from .coverage import parse_coverage_xml

_EXCLUDED_DIRS = {
    "__pycache__", ".git", "dist", "build", ".tox", ".venv",
    "node_modules", ".mypy_cache", ".pytest_cache",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_toml(path: Path) -> dict:
    """Return parsed TOML dict or empty dict on any failure."""
    if tomllib is None or not path.is_file():
        return {}
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def _regex_in_file(path: Path, pattern: str) -> str:
    """Return first capture group from pattern in file, or empty string."""
    if not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(pattern, text)
        return m.group(1) if m else ""
    except Exception:
        return ""


def _run_git(args: list, cwd: Path) -> str:
    """Run a git command and return stripped stdout, or raise RuntimeError if git not found."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except FileNotFoundError:
        raise RuntimeError(
            "git is not installed or not on PATH. "
            "Install git to use git-based badge sources."
        )


# ---------------------------------------------------------------------------
# Package metadata
# ---------------------------------------------------------------------------

def get_version(search_path: Path = Path(".")) -> str:
    """Return package version string from pyproject.toml, setup.py, version.py, or git tag."""
    search_path = Path(search_path)

    # Step 1: pyproject.toml [project] version
    data = _read_toml(search_path / "pyproject.toml")
    v = data.get("project", {}).get("version", "")
    if v:
        return str(v)

    # Step 2: setup.py literal version= value
    v = _regex_in_file(
        search_path / "setup.py",
        r'version\s*=\s*["\']([0-9][^"\']*)["\']',
    )
    if v:
        return v

    # Step 3: _version.py or version.py __version__
    for fname in ("_version.py", "version.py"):
        v = _regex_in_file(
            search_path / fname,
            r'__version__\s*=\s*["\']([^"\']+)["\']',
        )
        if v:
            return v

        # Also check inside the package src directory
        for candidate in search_path.glob(f"src/*/{fname}"):
            v = _regex_in_file(
                candidate,
                r'__version__\s*=\s*["\']([^"\']+)["\']',
            )
            if v:
                return v

    # Step 4: git tag
    try:
        v = _run_git(["describe", "--tags", "--abbrev=0"], search_path)
        if v:
            return v
    except RuntimeError:
        pass

    return "unknown"


def get_license(search_path: Path = Path(".")) -> str:
    """Return license identifier from pyproject.toml or setup.py."""
    search_path = Path(search_path)

    # pyproject.toml: license = {text = "MIT"} or license = "MIT"
    data = _read_toml(search_path / "pyproject.toml")
    lic = data.get("project", {}).get("license", "")
    if isinstance(lic, dict):
        lic = lic.get("text", lic.get("file", ""))
    if lic:
        return str(lic)

    # setup.py: license="MIT"
    v = _regex_in_file(
        search_path / "setup.py",
        r'license\s*=\s*["\']([^"\']+)["\']',
    )
    if v:
        return v

    return "unknown"


def get_python_requires(search_path: Path = Path(".")) -> str:
    """Return Python version requirement string."""
    search_path = Path(search_path)

    # pyproject.toml
    data = _read_toml(search_path / "pyproject.toml")
    req = data.get("project", {}).get("requires-python", "")
    if req:
        return str(req)

    # setup.py: python_requires=">=3.8"
    v = _regex_in_file(
        search_path / "setup.py",
        r'python_requires\s*=\s*["\']([^"\']+)["\']',
    )
    if v:
        return v

    return "unknown"
```

- [ ] **Step 5: Run tests — metadata functions should pass**

```bash
pytest tests/test_sources.py -v --tb=short -k "version or license or python_requires"
```
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt src/badgeshield/sources.py tests/test_sources.py
git commit -m "feat: add sources.py metadata extraction functions"
```

---

## Task 2: Git source functions

**Files:**
- Modify: `src/badgeshield/sources.py`
- Modify: `tests/test_sources.py`

- [ ] **Step 1: Write failing git tests**

Append to `tests/test_sources.py`:

```python
# ---------------------------------------------------------------------------
# Git functions — require a real git repo in tmp_path
# ---------------------------------------------------------------------------

def _init_git_repo(path: Path, tag: Optional[str] = None) -> None:
    """Initialise a minimal git repo with one commit and optional tag."""
    subprocess.run(["git", "init"], cwd=str(path), capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(path), capture_output=True)
    (path / "README.md").write_text("hi", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(path), capture_output=True)
    if tag:
        subprocess.run(["git", "tag", tag], cwd=str(path), capture_output=True)


def test_get_git_branch(tmp_path):
    from badgeshield.sources import get_git_branch
    _init_git_repo(tmp_path)
    branch = get_git_branch(tmp_path)
    assert branch in ("main", "master")  # git default varies by config


def test_get_git_tag(tmp_path):
    from badgeshield.sources import get_git_tag
    _init_git_repo(tmp_path, tag="1.0.0")
    assert get_git_tag(tmp_path) == "1.0.0"


def test_get_git_tag_no_tags_returns_untagged(tmp_path):
    from badgeshield.sources import get_git_tag
    _init_git_repo(tmp_path)
    assert get_git_tag(tmp_path) == "untagged"


def test_get_git_commit_count(tmp_path):
    from badgeshield.sources import get_git_commit_count
    _init_git_repo(tmp_path)
    count = get_git_commit_count(tmp_path)
    assert count.isdigit()
    assert int(count) >= 1


def test_get_git_status_clean(tmp_path):
    from badgeshield.sources import get_git_status
    _init_git_repo(tmp_path)
    assert get_git_status(tmp_path) == "clean"


def test_get_git_status_dirty(tmp_path):
    from badgeshield.sources import get_git_status
    _init_git_repo(tmp_path)
    (tmp_path / "dirty.txt").write_text("change", encoding="utf-8")
    assert get_git_status(tmp_path) == "dirty"


def test_get_git_status_failure_returns_unknown(tmp_path):
    """Non-git directory returns 'unknown', not 'clean'."""
    from badgeshield.sources import get_git_status
    # tmp_path has no .git dir
    assert get_git_status(tmp_path) == "unknown"


def test_git_function_raises_runtime_error_when_git_missing(tmp_path, monkeypatch):
    """All git functions raise RuntimeError (not FileNotFoundError) when git is not on PATH."""
    import badgeshield.sources as src_mod
    original_run = subprocess.run

    def raise_file_not_found(*args, **kwargs):
        raise FileNotFoundError("git not found")

    monkeypatch.setattr(subprocess, "run", raise_file_not_found)
    with pytest.raises(RuntimeError, match="git is not installed"):
        src_mod.get_git_branch(tmp_path)


def test_get_version_from_git_tag(tmp_path):
    """Step 4 of version chain: git tag."""
    _init_git_repo(tmp_path, tag="4.5.6")
    assert get_version(tmp_path) == "4.5.6"
```

- [ ] **Step 2: Run to confirm failures**

```bash
pytest tests/test_sources.py -v --tb=short -k "git"
```
Expected: `ImportError` on `get_git_branch` etc.

- [ ] **Step 3: Add git functions to `sources.py`**

Append to `src/badgeshield/sources.py` after `get_python_requires`:

```python
# ---------------------------------------------------------------------------
# Git functions
# ---------------------------------------------------------------------------

def get_git_branch(search_path: Path = Path(".")) -> str:
    """Return the current git branch name, or 'unknown' on failure."""
    search_path = Path(search_path)
    try:
        v = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], search_path)
        return v if v else "unknown"
    except RuntimeError:
        raise


def get_git_tag(search_path: Path = Path(".")) -> str:
    """Return the most recent git tag, or 'untagged' if none exist."""
    search_path = Path(search_path)
    try:
        v = _run_git(["describe", "--tags", "--abbrev=0"], search_path)
        return v if v else "untagged"
    except RuntimeError:
        raise


def get_git_commit_count(search_path: Path = Path(".")) -> str:
    """Return total number of commits as a string, or 'unknown' on failure."""
    search_path = Path(search_path)
    try:
        v = _run_git(["rev-list", "--count", "HEAD"], search_path)
        return v if v else "unknown"
    except RuntimeError:
        raise


def get_git_status(search_path: Path = Path(".")) -> str:
    """Return 'clean' or 'dirty' based on working tree state, or 'unknown' on failure."""
    search_path = Path(search_path)
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(search_path),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return "unknown"
        return "dirty" if result.stdout.strip() else "clean"
    except FileNotFoundError:
        raise RuntimeError(
            "git is not installed or not on PATH. "
            "Install git to use git-based badge sources."
        )
```

- [ ] **Step 4: Run git tests**

```bash
pytest tests/test_sources.py -v --tb=short -k "git"
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/badgeshield/sources.py tests/test_sources.py
git commit -m "feat: add git source functions to sources.py"
```

---

## Task 3: `get_lines_of_code`

**Files:**
- Modify: `src/badgeshield/sources.py`
- Modify: `tests/test_sources.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_sources.py`:

```python
# ---------------------------------------------------------------------------
# get_lines_of_code
# ---------------------------------------------------------------------------

def test_get_lines_of_code_basic(tmp_path):
    from badgeshield.sources import get_lines_of_code
    (tmp_path / "a.py").write_text("x = 1\ny = 2\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("z = 3\n", encoding="utf-8")
    assert get_lines_of_code(tmp_path) == "3"


def test_get_lines_of_code_excludes_dirs(tmp_path):
    from badgeshield.sources import get_lines_of_code
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "hidden.py").write_text("y = 2\n" * 100, encoding="utf-8")
    assert get_lines_of_code(tmp_path) == "1"


def test_get_lines_of_code_extensions_filter(tmp_path):
    from badgeshield.sources import get_lines_of_code
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "b.js").write_text("let x = 1;\nlet y = 2;\n", encoding="utf-8")
    assert get_lines_of_code(tmp_path, extensions=(".js",)) == "2"


def test_get_lines_of_code_no_match_returns_zero(tmp_path):
    from badgeshield.sources import get_lines_of_code
    (tmp_path / "a.txt").write_text("hello\n", encoding="utf-8")
    assert get_lines_of_code(tmp_path) == "0"


def test_get_lines_of_code_formatted_with_commas(tmp_path):
    from badgeshield.sources import get_lines_of_code
    for i in range(1200):
        (tmp_path / f"f{i}.py").write_text("x = 1\n", encoding="utf-8")
    result = get_lines_of_code(tmp_path)
    assert "," in result  # e.g. "1,200"
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_sources.py -v --tb=short -k "lines_of_code"
```

- [ ] **Step 3: Add `get_lines_of_code` to `sources.py`**

Append to `src/badgeshield/sources.py`:

```python
# ---------------------------------------------------------------------------
# Lines of code
# ---------------------------------------------------------------------------

def get_lines_of_code(
    search_path: Path = Path("."),
    extensions: tuple = (".py",),
) -> str:
    """Count non-blank lines across source files. Never raises; returns '0' on no match."""
    search_path = Path(search_path)
    total = 0
    for root, dirs, files in search_path.walk() if hasattr(search_path, "walk") else _os_walk(search_path):
        root = Path(root)
        # Prune excluded directories in-place (str(d) works for both Path and str entries)
        dirs[:] = [d for d in dirs if str(d) not in _EXCLUDED_DIRS and not str(d).endswith(".egg-info")]
        for fname in files:
            if any(fname.endswith(ext) for ext in extensions):
                try:
                    text = (root / fname).read_text(encoding="utf-8", errors="ignore")
                    total += sum(1 for line in text.splitlines() if line.strip())
                except Exception:
                    pass
    return f"{total:,}"


def _os_walk(path: Path):
    """Fallback for Path.walk() (Python < 3.12)."""
    import os
    for root, dirs, files in os.walk(str(path)):
        yield root, dirs, files
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_sources.py -v --tb=short -k "lines_of_code"
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/badgeshield/sources.py tests/test_sources.py
git commit -m "feat: add get_lines_of_code to sources.py"
```

---

## Task 4: `get_test_results` and `get_coverage`

**Files:**
- Modify: `src/badgeshield/sources.py`
- Modify: `tests/test_sources.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_sources.py`:

```python
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
```

- [ ] **Step 2: Run to confirm failures**

```bash
pytest tests/test_sources.py -v --tb=short -k "test_results or coverage"
```

- [ ] **Step 3: Add `get_test_results` and `get_coverage` to `sources.py`**

Append to `src/badgeshield/sources.py`:

```python
# ---------------------------------------------------------------------------
# Test results (JUnit XML)
# ---------------------------------------------------------------------------

def get_test_results(junit_xml: Path) -> str:
    """Parse a JUnit XML report and return a results summary string.

    Returns e.g. '47 passed' or '2 failed / 49'.
    Raises FileNotFoundError, ET.ParseError, or ValueError on bad input.
    """
    junit_xml = Path(junit_xml)
    if not junit_xml.is_file():
        raise FileNotFoundError(f"JUnit XML not found: {junit_xml}")

    tree = ET.parse(junit_xml)  # raises ET.ParseError on bad XML
    root = tree.getroot()

    # Support both <testsuite> root and <testsuites> wrapping root
    if root.tag == "testsuites":
        suites = list(root.findall("testsuite"))
    elif root.tag == "testsuite":
        suites = [root]
    else:
        raise ValueError(
            f"Not a recognisable JUnit XML structure — root element is <{root.tag}>. "
            "Expected <testsuite> or <testsuites>."
        )

    total = sum(int(s.get("tests", 0)) for s in suites)
    failures = sum(int(s.get("failures", 0)) + int(s.get("errors", 0)) for s in suites)

    if failures:
        return f"{failures} failed / {total}"
    return f"{total} passed"


# ---------------------------------------------------------------------------
# Coverage (wraps coverage.py)
# ---------------------------------------------------------------------------

def get_coverage(coverage_xml: Path) -> str:
    """Return coverage percentage string e.g. '82%'. Raises on bad input."""
    pct = parse_coverage_xml(coverage_xml, metric="line")
    return f"{pct:.0f}%"
```

- [ ] **Step 4: Add `import xml.etree.ElementTree as ET` at top of `sources.py` if not already there**

Check the top of `sources.py`. `ET` is imported in `coverage.py` but `sources.py` needs its own import since it parses JUnit XML directly. Confirm `import xml.etree.ElementTree as ET` is in the imports block.

- [ ] **Step 5: Run all sources tests**

```bash
pytest tests/test_sources.py -v --tb=short
```
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/badgeshield/sources.py tests/test_sources.py
git commit -m "feat: add get_test_results and get_coverage to sources.py"
```

---

## Task 5: `presets.py` — Preset dataclass and registry

**Files:**
- Create: `src/badgeshield/presets.py`
- Create: `tests/test_presets.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_presets.py`:

```python
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
    wired_names = [
        "version", "license", "python", "branch", "tag",
        "commits", "repo-status", "lines", "tests", "coverage",
    ]
    for name in wired_names:
        assert name in PRESETS, f"Missing preset: {name}"
        assert PRESETS[name].source is not None, f"Preset '{name}' missing source"


def test_preset_registry_size():
    assert len(PRESETS) >= 36


def test_preset_source_callable_protocol(tmp_path):
    """Data-wired presets (excluding tests/coverage/lines) accept search_path."""
    search_only = ["version", "license", "python", "branch", "tag", "commits", "repo-status"]
    for name in search_only:
        preset = PRESETS[name]
        # Should be callable with a Path — result may be "unknown" in tmp_path
        result = preset.source(tmp_path)
        assert isinstance(result, str), f"Preset '{name}' source did not return str"
```

- [ ] **Step 2: Run to confirm failures**

```bash
pytest tests/test_presets.py -v --tb=short
```
Expected: `ImportError: cannot import name 'PRESETS' from 'badgeshield.presets'`

- [ ] **Step 3: Create `presets.py`**

Create `src/badgeshield/presets.py`:

```python
"""Preset badge registry — maps preset names to badge configuration."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Union

from .utils import BadgeColor
from .sources import (
    get_version, get_license, get_python_requires,
    get_git_branch, get_git_tag, get_git_commit_count, get_git_status,
    get_lines_of_code, get_test_results, get_coverage,
)


@dataclass
class Preset:
    """Configuration for a named badge preset.

    Parameters
    ----------
    label:
        Left-section text of the badge.
    color:
        Left-section color — a BadgeColor enum member or hex string.
    source:
        Callable ``(search_path: Path) -> str`` that resolves the right-section
        value from local artifacts. ``None`` for cosmetic presets.
    right_text:
        Fixed right-section text for cosmetic presets.
    right_color:
        Right-section color hex string.
    description:
        Human-readable description shown by ``badgeshield presets``.
    """
    label: str
    color: Union[BadgeColor, str]
    source: Optional[Callable[[Path], str]] = None
    right_text: Optional[str] = None
    right_color: str = "#555555"
    description: str = ""


PRESETS: dict[str, Preset] = {
    # --- Data-wired ---
    "version": Preset(
        label="version", color=BadgeColor.DARK_BLUE, source=get_version,
        description="Package version from pyproject.toml, setup.py, version.py, or git tag",
    ),
    "license": Preset(
        label="license", color=BadgeColor.DARK_GRAY, source=get_license,
        description="License identifier from pyproject.toml or setup.py",
    ),
    "python": Preset(
        label="python", color=BadgeColor.DARK_BLUE, source=get_python_requires,
        description="Python version requirement from pyproject.toml or setup.py",
    ),
    "branch": Preset(
        label="branch", color=BadgeColor.DARK_CYAN, source=get_git_branch,
        description="Current git branch name",
    ),
    "tag": Preset(
        label="tag", color=BadgeColor.DARK_GREEN, source=get_git_tag,
        description="Most recent git tag",
    ),
    "commits": Preset(
        label="commits", color=BadgeColor.DARK_GRAY, source=get_git_commit_count,
        description="Total git commit count",
    ),
    "repo-status": Preset(
        label="repo", color=BadgeColor.GREEN, source=get_git_status,
        description="Git working tree status: clean or dirty",
    ),
    "lines": Preset(
        label="lines", color=BadgeColor.DARK_PURPLE, source=get_lines_of_code,
        description="Total non-blank lines of source code (default: .py files)",
    ),
    "tests": Preset(
        label="tests", color=BadgeColor.GREEN, source=None,  # CLI wraps get_test_results
        description="Test results from JUnit XML (requires --junit flag)",
    ),
    "coverage": Preset(
        label="coverage", color=BadgeColor.GREEN, source=None,  # CLI wraps get_coverage
        description="Line coverage percentage from coverage.xml (requires --coverage_xml flag)",
    ),
    # --- Code quality ---
    "black": Preset(label="code style", color=BadgeColor.BLACK, right_text="black",
                    description="Declares code is formatted with Black"),
    "ruff": Preset(label="linting", color=BadgeColor.DARK_PURPLE, right_text="ruff",
                   description="Declares linting with Ruff"),
    "flake8": Preset(label="linting", color=BadgeColor.DARK_BLUE, right_text="flake8",
                     description="Declares linting with flake8"),
    "isort": Preset(label="imports", color=BadgeColor.DARK_CYAN, right_text="isort",
                    description="Declares import sorting with isort"),
    "mypy": Preset(label="types", color=BadgeColor.DARK_BLUE, right_text="mypy",
                   description="Declares type checking with mypy"),
    # --- Lifecycle ---
    "passing": Preset(label="build", color=BadgeColor.GREEN, right_text="passing",
                      description="Build status: passing"),
    "failing": Preset(label="build", color=BadgeColor.RED, right_text="failing",
                      description="Build status: failing"),
    "stable": Preset(label="status", color=BadgeColor.GREEN, right_text="stable",
                     description="Project stability: stable"),
    "wip": Preset(label="status", color=BadgeColor.ORANGE, right_text="wip",
                  description="Project status: work in progress"),
    "alpha": Preset(label="status", color=BadgeColor.ORANGE, right_text="alpha",
                    description="Release stage: alpha"),
    "beta": Preset(label="status", color=BadgeColor.YELLOW, right_text="beta",
                   description="Release stage: beta"),
    "rc": Preset(label="status", color=BadgeColor.DARK_YELLOW, right_text="rc",
                 description="Release stage: release candidate"),
    "experimental": Preset(label="status", color=BadgeColor.ORANGE, right_text="experimental",
                            description="API is experimental — may change"),
    "maintained": Preset(label="maintained", color=BadgeColor.GREEN, right_text="maintained",
                         description="Project is actively maintained"),
    "deprecated": Preset(label="deprecated", color=BadgeColor.RED, right_text="deprecated",
                         description="Project or API is deprecated"),
    "archived": Preset(label="archived", color=BadgeColor.DARK_GRAY, right_text="archived",
                       description="Project is archived — no longer active"),
    # --- Project type ---
    "library": Preset(label="type", color=BadgeColor.DARK_BLUE, right_text="library",
                      description="Project type: library"),
    "cli": Preset(label="type", color=BadgeColor.DARK_CYAN, right_text="cli",
                  description="Project type: CLI tool"),
    "framework": Preset(label="type", color=BadgeColor.DARK_PURPLE, right_text="framework",
                        description="Project type: framework"),
    "api": Preset(label="type", color=BadgeColor.DARK_GREEN, right_text="api",
                  description="Project type: API"),
    # --- Community ---
    "contributions-welcome": Preset(
        label="contributions", color=BadgeColor.PASTEL_PURPLE, right_text="welcome",
        description="Contributions are welcome",
    ),
    "hacktoberfest": Preset(
        label="hacktoberfest", color=BadgeColor.DARK_PURPLE, right_text="hacktoberfest",
        description="Project participates in Hacktoberfest",
    ),
    # --- Platform ---
    "cross-platform": Preset(label="platform", color=BadgeColor.DARK_BLUE, right_text="cross-platform",
                              description="Runs on all platforms"),
    "linux": Preset(label="platform", color=BadgeColor.DARK_GRAY, right_text="linux",
                    description="Linux platform"),
    "windows": Preset(label="platform", color=BadgeColor.DARK_BLUE, right_text="windows",
                      description="Windows platform"),
    "macos": Preset(label="platform", color=BadgeColor.DARK_GRAY, right_text="macos",
                    description="macOS platform"),
}
```

- [ ] **Step 4: Run preset tests**

```bash
pytest tests/test_presets.py -v --tb=short
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/badgeshield/presets.py tests/test_presets.py
git commit -m "feat: add presets.py with Preset dataclass and 36-entry registry"
```

---

## Task 6: `--format` flag on existing subcommands (`single`, `batch`, `coverage`)

**Files:**
- Modify: `src/badgeshield/generate_badge_cli.py`
- Create: `tests/test_preset_cli.py`

- [ ] **Step 1: Write failing tests for `--format`**

Create `tests/test_preset_cli.py`:

```python
"""CLI tests for --format flag, preset, and presets subcommands."""
from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from badgeshield.generate_badge_cli import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# _format_snippet helper (tested indirectly via CLI)
# ---------------------------------------------------------------------------

def test_format_snippet_import():
    from badgeshield.generate_badge_cli import _format_snippet
    assert _format_snippet("badge.svg", "build", "markdown") == "![build](badge.svg)"
    assert _format_snippet("badge.svg", "build", "html") == '<img src="badge.svg" alt="build" />'
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
    assert '<img src=' in result.output
```

- [ ] **Step 2: Run to confirm failures**

```bash
pytest tests/test_preset_cli.py -v --tb=short -k "format"
```
Expected: failures on `_format_snippet` import and `--format` unknown option.

- [ ] **Step 3: Add `_format_snippet` and `--format` to `generate_badge_cli.py`**

After the `_error` function definition (around line 31), add:

```python
def _format_snippet(svg_path: str, alt_text: str, fmt: str) -> str:
    """Return an embed snippet for the given SVG path and format."""
    if fmt == "markdown":
        return f"![{alt_text}]({svg_path})"
    elif fmt == "rst":
        return f".. image:: {svg_path}\n   :alt: {alt_text}"
    elif fmt == "html":
        return f'<img src="{svg_path}" alt="{alt_text}" />'
    else:
        raise ValueError(f"Unknown format {fmt!r}. Expected: markdown, rst, html")
```

Add `format` parameter to the `single` command signature (after `style`):

```python
format: Optional[str] = typer.Option(
    None, "--format", help="Embed snippet format: markdown | rst | html"
),
```

After the `generator.generate_badge(...)` call in `single`, add:

```python
    if format:
        fmt_lower = format.lower()
        if fmt_lower not in ("markdown", "rst", "html"):
            _error(f"Invalid format '{format}'. Choose from: markdown, rst, html")
            raise typer.Exit(1)
        svg_path = str(Path(output_path or ".") / badge_name)
        typer.echo(_format_snippet(svg_path, left_text, fmt_lower))
```

Similarly add `format` parameter and snippet output to `batch` and `coverage` commands. For `batch`, print a snippet per badge after the summary table:

```python
# In batch command, after rprint(table):
if format:
    fmt_lower = format.lower()
    if fmt_lower not in ("markdown", "rst", "html"):
        _error(f"Invalid format '{format}'. Choose from: markdown, rst, html")
        raise typer.Exit(1)
    for badge in badge_configs:
        if badge["badge_name"] not in failure_map:
            svg_path = str(Path(output_path or ".") / badge["badge_name"])
            typer.echo(_format_snippet(svg_path, badge.get("left_text", badge["badge_name"]), fmt_lower))
```

- [ ] **Step 4: Run format tests**

```bash
pytest tests/test_preset_cli.py -v --tb=short -k "format"
```
Expected: all pass.

- [ ] **Step 5: Run full test suite to check for regressions**

```bash
pytest tests/test_badge_generator.py tests/test_sources.py tests/test_presets.py tests/test_preset_cli.py -v --tb=short
```
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/badgeshield/generate_badge_cli.py tests/test_preset_cli.py
git commit -m "feat: add --format flag and _format_snippet to CLI subcommands"
```

---

## Task 7: `presets` list subcommand and `preset` single-badge subcommand

**Files:**
- Modify: `src/badgeshield/generate_badge_cli.py`
- Modify: `tests/test_preset_cli.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_preset_cli.py`:

```python
# ---------------------------------------------------------------------------
# presets list subcommand
# ---------------------------------------------------------------------------

def test_presets_list_renders(tmp_path):
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
```

- [ ] **Step 2: Run to confirm failures**

```bash
pytest tests/test_preset_cli.py -v --tb=short -k "presets_list or preset_"
```
Expected: `No such command 'preset'` / `No such command 'presets'`.

- [ ] **Step 3: Add `presets` and `preset` subcommands to `generate_badge_cli.py`**

Add imports at the top of `generate_badge_cli.py`:

```python
from typing import List  # add to existing typing import line
from .presets import PRESETS, Preset
from .sources import get_test_results, get_coverage, get_lines_of_code
```

Add the `presets` subcommand (list):

```python
@app.command(name="presets")
def presets_list() -> None:
    """List all available badge presets."""
    table = Table(title="Available Presets", show_lines=True)
    table.add_column("Name", style="cyan")
    table.add_column("Label")
    table.add_column("Type")
    table.add_column("Description")
    for name, preset in PRESETS.items():
        kind = "data-wired" if preset.source is not None or name in ("tests", "coverage") else "cosmetic"
        table.add_row(name, preset.label, kind, preset.description)
    rprint(table)
```

Add the `preset` subcommand (single badge):

```python
@app.command(name="preset")
def preset_cmd(
    name: Optional[str] = typer.Argument(None, help="Preset name (see 'badgeshield presets')"),
    badge_name: Optional[str] = typer.Option(None, help="Output filename (defaults to {name}.svg)"),
    output_path: Optional[str] = typer.Option(None, help="Output directory (default: current directory)"),
    search_path: str = typer.Option(".", help="Repo root for source resolution"),
    style: str = typer.Option("flat", help="FLAT | ROUNDED | GRADIENT | SHADOWED"),
    format: Optional[str] = typer.Option(None, "--format", help="markdown | rst | html"),
    extensions: Optional[List[str]] = typer.Option(None, help="File extensions for lines preset (repeatable): --extensions .py --extensions .js"),
    junit: Optional[Path] = typer.Option(None, help="Path to JUnit XML for tests preset"),
    coverage_xml: Optional[Path] = typer.Option(None, help="Path to coverage.xml for coverage preset"),
    all_presets: bool = typer.Option(False, "--all", help="Generate all resolvable presets"),
) -> None:
    """Generate a badge from a named preset."""
    if all_presets:
        _run_all_presets(output_path, search_path, style, format, extensions, junit, coverage_xml)
        return

    if name is None:
        _error("Provide a preset name or use --all. Run 'badgeshield presets' to list available presets.")
        raise typer.Exit(1)

    if name not in PRESETS:
        _error(f"Unknown preset '{name}'. Run 'badgeshield presets' to see available options.")
        raise typer.Exit(1)

    p = PRESETS[name]
    out_name = badge_name or f"{name}.svg"
    sp = Path(search_path)

    try:
        style_enum = BadgeStyle[style.upper()]
    except KeyError:
        _error(f"Invalid style '{style}'. Choose from: {', '.join(s.name for s in BadgeStyle)}")
        raise typer.Exit(1)

    # Resolve right_text
    right_text = p.right_text
    if name == "lines":
        ext_tuple = tuple(extensions) if extensions else (".py",)
        try:
            right_text = get_lines_of_code(sp, extensions=ext_tuple)
        except Exception as exc:
            _error(str(exc))
            raise typer.Exit(1)
    elif right_text is None and p.source is not None:
        try:
            right_text = p.source(sp)
        except RuntimeError as exc:
            _error(str(exc))
            raise typer.Exit(1)
    elif name == "tests":
        if junit is None:
            _error("The 'tests' preset requires --junit <path-to-junit.xml>")
            raise typer.Exit(1)
        try:
            right_text = get_test_results(junit)
        except (FileNotFoundError, ValueError, Exception) as exc:
            _error(str(exc))
            raise typer.Exit(1)
    elif name == "coverage":
        if coverage_xml is None:
            _error("The 'coverage' preset requires --coverage_xml <path-to-coverage.xml>")
            raise typer.Exit(1)
        try:
            right_text = get_coverage(coverage_xml)
        except (FileNotFoundError, ValueError, Exception) as exc:
            _error(str(exc))
            raise typer.Exit(1)

    left_color = str(p.color)

    try:
        gen = BadgeGenerator(template=BadgeTemplate.DEFAULT, style=style_enum)
        gen.generate_badge(
            left_text=p.label,
            left_color=left_color,
            right_text=right_text,
            right_color=p.right_color,
            badge_name=out_name,
            output_path=output_path,
        )
    except (ValueError, TypeError) as exc:
        _error(str(exc))
        raise typer.Exit(1)

    if format:
        fmt_lower = format.lower()
        if fmt_lower not in ("markdown", "rst", "html"):
            _error(f"Invalid format '{format}'. Choose from: markdown, rst, html")
            raise typer.Exit(1)
        svg_path = str(Path(output_path or ".") / out_name)
        typer.echo(_format_snippet(svg_path, p.label, fmt_lower))
```

- [ ] **Step 4: Run preset subcommand tests**

```bash
pytest tests/test_preset_cli.py -v --tb=short
```
Expected: all pass.

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/test_badge_generator.py tests/test_sources.py tests/test_presets.py tests/test_preset_cli.py -v --tb=short
```
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/badgeshield/generate_badge_cli.py tests/test_preset_cli.py
git commit -m "feat: add preset and presets CLI subcommands"
```

---

## Task 8: `preset --all` subcommand

**Files:**
- Modify: `src/badgeshield/generate_badge_cli.py`
- Modify: `tests/test_preset_cli.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_preset_cli.py`:

```python
# ---------------------------------------------------------------------------
# preset --all
# ---------------------------------------------------------------------------

def test_preset_all_generates_cosmetic_badges(tmp_path):
    result = runner.invoke(app, [
        "preset", "--all",
        "--output_path", str(tmp_path),
    ])
    assert result.exit_code == 0
    # Cosmetic badges always generated
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
    import badgeshield.sources as src_mod
    monkeypatch.setattr(src_mod, "get_version", lambda p: "unknown")
    monkeypatch.setattr(src_mod, "get_git_branch", lambda p: "unknown")
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
```

- [ ] **Step 2: Run to confirm failures**

```bash
pytest tests/test_preset_cli.py -v --tb=short -k "all"
```
Expected: failures because `_run_all_presets` is not yet implemented.

- [ ] **Step 3: Add `_run_all_presets` helper to `generate_badge_cli.py`**

Add before the `preset_cmd` function:

```python
_SKIP_VALUES = {"unknown", "untagged"}


def _run_all_presets(
    output_path, search_path, style, format, extensions, junit, coverage_xml
) -> None:
    """Generate all resolvable presets. Called by `preset --all`."""
    try:
        style_enum = BadgeStyle[style.upper()]
    except KeyError:
        _error(f"Invalid style '{style}'.")
        raise typer.Exit(1)

    sp = Path(search_path)
    ext_tuple = tuple(extensions) if extensions else (".py",)

    written = []
    skipped = []

    for name, p in PRESETS.items():
        out_name = f"{name}.svg"
        right_text = p.right_text

        if right_text is None:
            # Data-wired preset — resolve value
            if name == "tests":
                if junit is None:
                    skipped.append((name, "no --junit provided"))
                    continue
                try:
                    right_text = get_test_results(junit)
                except Exception as exc:
                    skipped.append((name, str(exc)))
                    continue
            elif name == "coverage":
                if coverage_xml is None:
                    skipped.append((name, "no --coverage_xml provided"))
                    continue
                try:
                    right_text = get_coverage(coverage_xml)
                except Exception as exc:
                    skipped.append((name, str(exc)))
                    continue
            elif name == "lines":
                try:
                    right_text = get_lines_of_code(sp, extensions=ext_tuple)
                except Exception as exc:
                    skipped.append((name, str(exc)))
                    continue
            elif p.source is not None:
                try:
                    right_text = p.source(sp)
                except Exception as exc:
                    skipped.append((name, str(exc)))
                    continue
                if right_text in _SKIP_VALUES:
                    skipped.append((name, f"resolved to '{right_text}'"))
                    continue

        try:
            gen = BadgeGenerator(template=BadgeTemplate.DEFAULT, style=style_enum)
            gen.generate_badge(
                left_text=p.label,
                left_color=str(p.color),
                right_text=right_text,
                right_color=p.right_color,
                badge_name=out_name,
                output_path=output_path,
            )
            written.append((name, out_name, p.label))
        except Exception as exc:
            skipped.append((name, str(exc)))

    # Summary table
    if skipped:
        skip_table = Table(title="Skipped Presets", show_lines=True)
        skip_table.add_column("Preset", style="yellow")
        skip_table.add_column("Reason")
        for sname, reason in skipped:
            skip_table.add_row(sname, reason)
        rprint(skip_table)

    if not written:
        _error("No badges were written. Check that at least one preset is resolvable.")
        raise typer.Exit(1)

    rprint(f"[green]✓ Generated {len(written)} badge(s)[/green]")

    if format:
        fmt_lower = format.lower()
        if fmt_lower not in ("markdown", "rst", "html"):
            _error(f"Invalid format '{format}'.")
            raise typer.Exit(1)
        for _, out_name, alt_text in written:
            svg_path = str(Path(output_path or ".") / out_name)
            typer.echo(_format_snippet(svg_path, alt_text, fmt_lower))
```

- [ ] **Step 4: Run `--all` tests**

```bash
pytest tests/test_preset_cli.py -v --tb=short -k "all"
```
Expected: all pass.

- [ ] **Step 5: Full test suite**

```bash
pytest tests/test_badge_generator.py tests/test_sources.py tests/test_presets.py tests/test_preset_cli.py -v --tb=short
```
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/badgeshield/generate_badge_cli.py tests/test_preset_cli.py
git commit -m "feat: add preset --all with skip-filter and Rich summary table"
```

---

## Task 9: Public API exports (`__init__.py`)

**Files:**
- Modify: `src/badgeshield/__init__.py`

- [ ] **Step 1: Write a failing import test**

Append to `tests/test_presets.py`:

```python
def test_public_api_exports():
    from badgeshield import (
        get_version, get_license, get_python_requires,
        get_git_branch, get_git_tag, get_git_commit_count, get_git_status,
        get_lines_of_code, get_test_results, get_coverage,
        PRESETS, Preset,
    )
    assert callable(get_version)
    assert isinstance(PRESETS, dict)
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_presets.py::test_public_api_exports -v --tb=short
```
Expected: `ImportError`.

- [ ] **Step 3: Update `__init__.py`**

Replace the contents of `src/badgeshield/__init__.py`:

```python
from ._version import __version__
from .badge_generator import BadgeBatchGenerator, BadgeGenerator
from .coverage import coverage_color, parse_coverage_xml
from .utils import BadgeColor, BadgeTemplate, FrameType, BadgeStyle
from .sources import (
    get_version, get_license, get_python_requires,
    get_git_branch, get_git_tag, get_git_commit_count, get_git_status,
    get_lines_of_code, get_test_results, get_coverage,
)
from .presets import PRESETS, Preset
from pylogshield import LogLevel

__all__ = [
    "BadgeGenerator",
    "BadgeBatchGenerator",
    "BadgeColor",
    "BadgeTemplate",
    "BadgeStyle",
    "FrameType",
    "LogLevel",
    "__version__",
    "coverage_color",
    "parse_coverage_xml",
    "get_version",
    "get_license",
    "get_python_requires",
    "get_git_branch",
    "get_git_tag",
    "get_git_commit_count",
    "get_git_status",
    "get_lines_of_code",
    "get_test_results",
    "get_coverage",
    "PRESETS",
    "Preset",
]
```

- [ ] **Step 4: Run test**

```bash
pytest tests/test_presets.py::test_public_api_exports -v --tb=short
```
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add src/badgeshield/__init__.py tests/test_presets.py
git commit -m "feat: export sources and presets in public API"
```

---

## Task 10: Docs — README pitch, reference pages, mkdocs wiring

**Files:**
- Modify: `README.md`
- Modify: `docs/index.md`
- Modify: `docs/getting-started/cli_usage.md`
- Modify: `docs/getting-started/usage.md`
- Create: `docs/reference/sources.md`
- Create: `docs/reference/presets.md`
- Modify: `mkdocs.yml`

- [ ] **Step 1: Add pitch section to `README.md`**

Insert after the `</div>` closing tag and before `## 📋 Table of Contents`:

```markdown
---

## Why badgeshield instead of shields.io?

shields.io is great — but it makes an HTTP call to an external server on every CI run.

**badgeshield generates badges entirely offline:**

- **No network calls** — works in air-gapped CI, behind corporate proxies, and offline laptops
- **No rate limits** — generate thousands of badges in a single run
- **No data sent externally** — your version numbers, branch names, and repo stats stay local
- **Reproducible** — same inputs always produce the same SVG, no caching surprises

```bash
# Generate every standard badge for your Python project in one command
badgeshield preset --all --output_path ./badges/ --format markdown
```

Drop the output straight into your README. No account needed, no tokens, no network.
```

- [ ] **Step 2: Update Table of Contents in `README.md`**

Add `- [Why badgeshield?](#why-badgeshield-instead-of-shieldsio)` as the first item in the ToC list.

- [ ] **Step 3: Update `docs/index.md`** 

Read the file first, then add a matching "Why badgeshield?" section after the overview paragraph (same content as README, abbreviated for docs).

- [ ] **Step 4: Add `preset`/`presets` examples to `docs/getting-started/cli_usage.md`**

Read the file, then append a new section:

```markdown
## Preset Badges

Generate badges from named presets — no need to specify colors or text manually.

### List available presets

```bash
badgeshield presets
```

### Generate a single preset

```bash
# Cosmetic preset — value is fixed
badgeshield preset passing --output_path ./badges/

# Data-wired preset — value resolved from local repo
badgeshield preset version --output_path ./badges/
badgeshield preset lines --extensions .py --extensions .js --output_path ./badges/
badgeshield preset tests --junit tests/junit.xml --output_path ./badges/
```

### Generate all presets at once

```bash
badgeshield preset --all --output_path ./badges/ --format markdown
```

### Embed snippets

Add `--format markdown|rst|html` to any command to print an embed snippet:

```bash
badgeshield preset version --format markdown
# output: ![version](./version.svg)
```
```

- [ ] **Step 5: Add `sources.py` examples to `docs/getting-started/usage.md`**

Read the file, then append a new section:

```markdown
## Local Data Sources

`sources.py` provides functions for reading local project metadata — no network calls.

```python
from pathlib import Path
from badgeshield import get_version, get_git_branch, get_lines_of_code

# Reads pyproject.toml → setup.py → version.py → git tag, in order
version = get_version(Path("."))          # "1.2.3"

branch = get_git_branch(Path("."))        # "main"

loc = get_lines_of_code(Path("."), extensions=(".py", ".js"))  # "4,821"
```
```

- [ ] **Step 6: Create `docs/reference/sources.md`**

```markdown
# Sources

::: badgeshield.sources
```

- [ ] **Step 7: Create `docs/reference/presets.md`**

```markdown
# Presets

::: badgeshield.presets
```

- [ ] **Step 8: Update `mkdocs.yml` nav section**

In the `🔧 API Reference:` section, add two new entries:

```yaml
    - Sources: 'reference/sources.md'
    - Presets: 'reference/presets.md'
```

- [ ] **Step 9: Commit docs**

```bash
git add README.md docs/ mkdocs.yml
git commit -m "docs: add why-badgeshield pitch, preset CLI examples, sources API reference"
```

---

## Final verification

- [ ] **Run the full passing test suite one last time**

```bash
pytest tests/test_badge_generator.py tests/test_sources.py tests/test_presets.py tests/test_preset_cli.py -v --tb=short
```
Expected: all pass, no regressions.

- [ ] **Smoke-test the CLI manually**

```bash
badgeshield presets
badgeshield preset passing --output_path /tmp/
badgeshield preset version --output_path /tmp/
badgeshield preset --all --output_path /tmp/ --format markdown
```
