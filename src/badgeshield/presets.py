"""Preset badge registry — maps preset names to badge configuration."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path  # kept for get_type_hints() resolution of Callable[[Path], str]
from typing import Callable, Optional, Union

from .utils import BadgeColor
from .sources import (
    get_version, get_license, get_python_requires,
    get_git_branch, get_git_tag, get_git_commit_count, get_git_status,
    get_lines_of_code,
)


@dataclass
class Preset:
    """Configuration for a named badge preset.

    ``source`` is a callable ``(search_path: Path) -> str`` for data-wired presets.
    When ``source=None``, the CLI supplies a lambda at dispatch time (e.g., for
    ``tests`` and ``coverage`` which require an explicit file path argument).
    """
    label: str
    color: Union[BadgeColor, str]
    source: Optional[Callable[[Path], str]] = None
    right_text: Optional[str] = None
    right_color: str = "#555555"  # right panel color; maps to BadgeGenerator right_color kwarg
    description: str = ""


PRESETS: dict[str, Preset] = {
    # --- Data-wired (search_path-based) ---
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
    # --- Data-wired (require CLI-provided file path; source=None) ---
    "tests": Preset(
        label="tests", color=BadgeColor.GREEN, source=None,
        description="Test results from JUnit XML (requires --junit flag)",
    ),
    "coverage": Preset(
        label="coverage", color=BadgeColor.GREEN, source=None,
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
