from ._version import __version__
from .badge_generator import BadgeBatchGenerator, BadgeGenerator, LogLevel
from .coverage import coverage_color, parse_coverage_xml
from .utils import BadgeColor, BadgeTemplate, FrameType

__all__ = [
    "BadgeGenerator",
    "BadgeBatchGenerator",
    "BadgeColor",
    "BadgeTemplate",
    "FrameType",
    "LogLevel",
    "__version__",
    "coverage_color",
    "parse_coverage_xml",
]
