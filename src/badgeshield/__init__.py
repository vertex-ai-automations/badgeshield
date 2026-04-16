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
