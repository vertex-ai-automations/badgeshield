"""Local project metadata extraction helpers."""
from __future__ import annotations

import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from .coverage import parse_coverage_xml

_EXCLUDED_DIRS = {
    "__pycache__",
    ".git",
    "dist",
    "build",
    ".tox",
    ".venv",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _read_toml(path: Path) -> dict:
    """Parse a TOML file, returning {} on any failure."""
    try:
        try:
            import tomllib  # type: ignore[import]
        except ImportError:
            import tomli as tomllib  # type: ignore[import,no-redef]
        with path.open("rb") as fh:
            return tomllib.load(fh)
    except Exception:
        return {}


def _regex_in_file(path: Path, pattern: str) -> str:
    """Return the first capture group of *pattern* in *path*, or ''."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        m = re.search(pattern, text)
        if m:
            return m.group(1)
    except Exception:
        pass
    return ""


def _run_git(args: list, cwd: Path) -> str:
    """Run a git command; return stripped stdout, "" on failure, raise RuntimeError if git not on PATH."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except FileNotFoundError:
        raise RuntimeError(
            "git is not installed or not on PATH. "
            "Install git to use git-based badge sources."
        )
    except subprocess.TimeoutExpired:
        return ""


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def get_version(search_path: Path = Path(".")) -> str:
    """
    Resolve project version using a 5-step chain; first non-empty wins.

    1. pyproject.toml  → project.version
    2. setup.py        → literal version= string
    3. _version.py / version.py (also src/*/_version.py, src/*/version.py)
    4. git describe --tags --abbrev=0
    5. "unknown"
    """
    # 1 — pyproject.toml
    pyproject = search_path / "pyproject.toml"
    if pyproject.exists():
        data = _read_toml(pyproject)
        version = data.get("project", {}).get("version", "")
        if version:
            return str(version)

    # 2 — setup.py (literal only)
    setup_py = search_path / "setup.py"
    if setup_py.exists():
        version = _regex_in_file(
            setup_py,
            r'version\s*=\s*["\']([0-9][^"\']*)["\']',
        )
        if version:
            return version

    # 3 — _version.py / version.py (direct + under src/*)
    candidates = [
        search_path / "_version.py",
        search_path / "version.py",
    ]
    src_dir = search_path / "src"
    if src_dir.is_dir():
        for pkg_dir in src_dir.iterdir():
            if pkg_dir.is_dir() and pkg_dir.name not in _EXCLUDED_DIRS:
                candidates.append(pkg_dir / "_version.py")
                candidates.append(pkg_dir / "version.py")

    version_pattern = r'__version__\s*=\s*["\']([^"\']+)["\']'
    for candidate in candidates:
        if candidate.exists():
            version = _regex_in_file(candidate, version_pattern)
            if version:
                return version

    # 4 — git tag
    try:
        version = _run_git(["describe", "--tags", "--abbrev=0"], cwd=search_path)
        if version:
            return version
    except RuntimeError:
        pass

    # 5 — fallback
    return "unknown"


def get_license(search_path: Path = Path(".")) -> str:
    """
    Resolve project license using a 2-step chain; first non-empty wins.

    1. pyproject.toml → project.license (string or dict with text/file key)
    2. setup.py       → literal license= string
    """
    # 1 — pyproject.toml
    pyproject = search_path / "pyproject.toml"
    if pyproject.exists():
        data = _read_toml(pyproject)
        lic = data.get("project", {}).get("license")
        if lic is not None:
            if isinstance(lic, dict):
                value = lic.get("text") or lic.get("file") or ""
            else:
                value = str(lic)
            if value:
                return value

    # 2 — setup.py
    setup_py = search_path / "setup.py"
    if setup_py.exists():
        value = _regex_in_file(setup_py, r'license\s*=\s*["\']([^"\']+)["\']')
        if value:
            return value

    return "unknown"


def get_python_requires(search_path: Path = Path(".")) -> str:
    """
    Resolve python_requires using a 2-step chain; first non-empty wins.

    1. pyproject.toml → project.requires-python
    2. setup.py       → literal python_requires= string
    """
    # 1 — pyproject.toml
    pyproject = search_path / "pyproject.toml"
    if pyproject.exists():
        data = _read_toml(pyproject)
        value = data.get("project", {}).get("requires-python", "")
        if value:
            return str(value)

    # 2 — setup.py
    setup_py = search_path / "setup.py"
    if setup_py.exists():
        value = _regex_in_file(
            setup_py,
            r'python_requires\s*=\s*["\']([^"\']+)["\']',
        )
        if value:
            return value

    return "unknown"


def get_git_branch(search_path: Path = Path(".")) -> str:
    """Return the current git branch name, or 'unknown' on failure."""
    v = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], Path(search_path))
    return v if v else "unknown"


def get_git_tag(search_path: Path = Path(".")) -> str:
    """Return the most recent git tag, or 'untagged' if none exist."""
    v = _run_git(["describe", "--tags", "--abbrev=0"], Path(search_path))
    return v if v else "untagged"


def get_git_commit_count(search_path: Path = Path(".")) -> str:
    """Return total number of commits as a string, or 'unknown' on failure."""
    v = _run_git(["rev-list", "--count", "HEAD"], Path(search_path))
    return v if v else "unknown"


def _os_walk(path: Path):
    """Fallback os.walk wrapper for Path.walk() which requires Python 3.12."""
    import os
    for root, dirs, files in os.walk(str(path)):
        yield root, dirs, files


def get_lines_of_code(
    search_path: Path = Path("."),
    extensions: tuple = (".py",),
) -> str:
    """Count non-blank lines across source files matching extensions.

    Never raises. Returns '0' if no files match. Returns comma-formatted integer string.
    Excludes directories in _EXCLUDED_DIRS and any directory ending with .egg-info.
    """
    search_path = Path(search_path)
    total = 0

    # Use Path.walk() on Python 3.12+, fall back to os.walk otherwise
    try:
        walker = search_path.walk()
    except AttributeError:
        walker = _os_walk(search_path)

    for root, dirs, files in walker:
        root = Path(root)
        # str(d) works for both Path objects (3.12 walk) and str names (os.walk)
        dirs[:] = [d for d in dirs if str(d) not in _EXCLUDED_DIRS and not str(d).endswith(".egg-info")]
        for fname in files:
            if any(str(fname).endswith(ext) for ext in extensions):
                try:
                    text = (root / fname).read_text(encoding="utf-8", errors="ignore")
                    total += sum(1 for line in text.splitlines() if line.strip())
                except Exception:
                    pass

    return f"{total:,}"


def get_git_status(search_path: Path = Path(".")) -> str:
    """Return 'clean' or 'dirty' based on working tree state, or 'unknown' on failure.

    IMPORTANT: Uses direct subprocess.run (not _run_git) to distinguish
    non-zero exit (not a git repo) from zero exit with empty output (clean).
    Never returns 'clean' on failure — that would be a false positive.
    """
    search_path = Path(search_path)
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(search_path),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return "unknown"
        return "dirty" if result.stdout.strip() else "clean"
    except FileNotFoundError:
        raise RuntimeError(
            "git is not installed or not on PATH. "
            "Install git to use git-based badge sources."
        )
    except subprocess.TimeoutExpired:
        return "unknown"


def get_test_results(junit_xml: Path) -> str:
    """Parse a JUnit XML report and return a results summary string.

    Returns e.g. '47 passed' or '2 failed / 49'.

    Raises
    ------
    FileNotFoundError
        If junit_xml does not exist.
    xml.etree.ElementTree.ParseError
        If the XML is malformed.
    ValueError
        If the root element is not a recognisable JUnit structure.
    """
    junit_xml = Path(junit_xml)
    if not junit_xml.is_file():
        raise FileNotFoundError(f"JUnit XML not found: {junit_xml}")

    tree = ET.parse(junit_xml)  # raises ET.ParseError on bad XML
    root = tree.getroot()

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


def get_coverage(coverage_xml: Path) -> str:
    """Return line coverage percentage string e.g. '82%'.

    Raises FileNotFoundError or ValueError on bad input (delegates to parse_coverage_xml).
    """
    pct = parse_coverage_xml(coverage_xml, metric="line")
    return f"{pct:.0f}%"
