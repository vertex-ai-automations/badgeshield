from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Union


def parse_coverage_xml(
    path: Union[str, Path],
    metric: str = "line",
) -> float:
    """Parse a coverage.xml report and return coverage as a percentage.

    Parameters
    ----------
    path : str or Path
        Path to the ``coverage.xml`` file produced by ``coverage run``.
    metric : str
        Which coverage metric to read. ``"line"`` reads ``line-rate``;
        ``"branch"`` reads ``branch-rate``. Defaults to ``"line"``.

    Returns
    -------
    float
        Coverage percentage in the range 0.0–100.0.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    ValueError
        If *metric* is not ``"line"`` or ``"branch"``, if the expected
        attribute is absent from the report, or if the attribute value
        cannot be converted to a float.
    xml.etree.ElementTree.ParseError
        If the XML is malformed. NOT a ``ValueError`` — catch explicitly.
    """
    if metric not in ("line", "branch"):
        raise ValueError(f"metric must be 'line' or 'branch', got {metric!r}")

    if not Path(path).is_file():
        raise FileNotFoundError(f"coverage.xml not found: {path}")

    attr = "line-rate" if metric == "line" else "branch-rate"
    tree = ET.parse(path)
    root = tree.getroot()
    value = root.get(attr)
    if value is None:
        raise ValueError(f"coverage.xml has no '{attr}' attribute on the root element")
    return float(value) * 100


def coverage_color(pct: float) -> str:
    """Return a hex color for the given coverage percentage."""
    if pct >= 90:
        return "#44cc11"
    if pct >= 80:
        return "#97ca00"
    if pct >= 70:
        return "#a4a61d"
    if pct >= 60:
        return "#dfb317"
    return "#e05d44"
