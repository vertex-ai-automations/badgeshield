from __future__ import annotations

import xml.etree.ElementTree as ET
import pytest
from typer.testing import CliRunner

from badgeshield.coverage import coverage_color, parse_coverage_xml
from badgeshield.generate_badge_cli import app

runner = CliRunner(mix_stderr=False)


def test_parse_invalid_metric(tmp_path):
    xml = tmp_path / "coverage.xml"
    xml.write_text('<coverage line-rate="0.943"/>')
    with pytest.raises(ValueError, match="metric must be"):
        parse_coverage_xml(xml, metric="foo")


def test_parse_missing_file():
    with pytest.raises(FileNotFoundError):
        parse_coverage_xml("/nonexistent/coverage.xml")


def test_parse_line_coverage(tmp_path):
    xml = tmp_path / "coverage.xml"
    xml.write_text('<coverage line-rate="0.943" branch-rate="0.812"/>')
    assert parse_coverage_xml(xml) == pytest.approx(94.3)


def test_parse_branch_coverage(tmp_path):
    xml = tmp_path / "coverage.xml"
    xml.write_text('<coverage line-rate="0.943" branch-rate="0.812"/>')
    assert parse_coverage_xml(xml, metric="branch") == pytest.approx(81.2)


def test_parse_malformed_xml(tmp_path):
    xml = tmp_path / "coverage.xml"
    xml.write_text("not xml at all <<<")
    with pytest.raises(ET.ParseError):
        parse_coverage_xml(xml)


def test_parse_missing_attribute(tmp_path):
    xml = tmp_path / "coverage.xml"
    xml.write_text('<coverage line-rate="0.943"/>')
    with pytest.raises(ValueError):
        parse_coverage_xml(xml, metric="branch")


def test_parse_zero_coverage(tmp_path):
    xml = tmp_path / "coverage.xml"
    xml.write_text('<coverage line-rate="0.0" branch-rate="0.0"/>')
    assert parse_coverage_xml(xml) == pytest.approx(0.0)


def test_color_thresholds():
    assert coverage_color(100.0) == "#44cc11"  # >= 90
    assert coverage_color(90.0)  == "#44cc11"  # boundary
    assert coverage_color(89.9)  == "#97ca00"  # >= 80
    assert coverage_color(80.0)  == "#97ca00"  # boundary
    assert coverage_color(79.9)  == "#a4a61d"  # >= 70
    assert coverage_color(70.0)  == "#a4a61d"  # boundary
    assert coverage_color(69.9)  == "#dfb317"  # >= 60
    assert coverage_color(60.0)  == "#dfb317"  # boundary
    assert coverage_color(59.9)  == "#e05d44"  # < 60
    assert coverage_color(0.0)   == "#e05d44"  # zero
