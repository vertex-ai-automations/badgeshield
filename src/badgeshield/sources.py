"""Local project metadata extraction helpers."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

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
