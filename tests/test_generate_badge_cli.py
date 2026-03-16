import json

import pytest
from typer.testing import CliRunner

from badgeshield.generate_badge_cli import app


class TestCLICommands:
    """CLI tests for single, batch, coverage — network blocked."""

    pytestmark = pytest.mark.usefixtures("block_network")
    runner = CliRunner(mix_stderr=False)

    # ---------------------------------------------------------------------------
    # single command
    # ---------------------------------------------------------------------------

    def test_single_happy_path(self, tmp_path):
        """Single badge generation with valid args should create the SVG file."""
        result = self.runner.invoke(app, [
            "single",
            "--left-text", "Build",
            "--left-color", "GREEN",
            "--badge-name", "build.svg",
            "--output-path", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output
        assert (tmp_path / "build.svg").exists()

    def test_single_invalid_color(self, tmp_path):
        """An unrecognised color name should print an Error panel and exit 1."""
        result = self.runner.invoke(app, [
            "single",
            "--left-text", "Build",
            "--left-color", "NOTACOLOR",
            "--badge-name", "build.svg",
            "--output-path", str(tmp_path),
        ])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_single_missing_svg_suffix(self, tmp_path):
        """badge-name without .svg suffix must exit 1."""
        result = self.runner.invoke(app, [
            "single",
            "--left-text", "Build",
            "--left-color", "GREEN",
            "--badge-name", "no_suffix",
            "--output-path", str(tmp_path),
        ])
        assert result.exit_code == 1

    def test_single_invalid_template(self, tmp_path):
        """An invalid template name must exit 1."""
        result = self.runner.invoke(app, [
            "single",
            "--left-text", "Build",
            "--left-color", "GREEN",
            "--badge-name", "build.svg",
            "--template", "BOGUS",
            "--output-path", str(tmp_path),
        ])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_single_invalid_frame(self, tmp_path):
        """An invalid frame name must exit 1."""
        result = self.runner.invoke(app, [
            "single",
            "--left-text", "Build",
            "--left-color", "GREEN",
            "--badge-name", "build.svg",
            "--template", "CIRCLE_FRAME",
            "--frame", "BADFRAME",
            "--output-path", str(tmp_path),
        ])
        assert result.exit_code == 1
        assert "Error" in result.output

    # ---------------------------------------------------------------------------
    # batch command
    # ---------------------------------------------------------------------------

    def test_batch_happy_path(self, tmp_path):
        """Batch with valid config JSON should create all SVG files."""
        config = [
            {"badge_name": "a.svg", "left_text": "alpha", "left_color": "#001122"},
            {"badge_name": "b.svg", "left_text": "beta", "left_color": "BLUE"},
        ]
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config))
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        result = self.runner.invoke(app, [
            "batch",
            str(config_file),
            "--output-path", str(out_dir),
        ])
        assert result.exit_code == 0, result.output
        assert (out_dir / "a.svg").exists()
        assert (out_dir / "b.svg").exists()

    def test_batch_malformed_json(self, tmp_path):
        """Malformed JSON config must exit 1 with an error message."""
        config_file = tmp_path / "bad.json"
        config_file.write_text("{broken")

        result = self.runner.invoke(app, [
            "batch",
            str(config_file),
        ])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_batch_missing_config_file(self, tmp_path):
        """Non-existent config file path must exit 1 (Typer exists=True)."""
        result = self.runner.invoke(app, [
            "batch",
            str(tmp_path / "nonexistent.json"),
        ])
        assert result.exit_code != 0

    def test_batch_circle_frame_without_frame(self, tmp_path):
        """CIRCLE_FRAME template without frame key in config must exit 1."""
        config = [
            {"badge_name": "f.svg", "left_text": "framed", "left_color": "#abcdef"},
        ]
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config))
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        result = self.runner.invoke(app, [
            "batch",
            str(config_file),
            "--template", "CIRCLE_FRAME",
            "--output-path", str(out_dir),
        ])
        assert result.exit_code == 1

    def test_single_style_rounded(self, tmp_path):
        result = self.runner.invoke(
            app,
            [
                "single",
                "--left-text", "Build",
                "--left-color", "GREEN",
                "--badge-name", "style_test.svg",
                "--output-path", str(tmp_path),
                "--style", "rounded",
            ],
        )
        assert result.exit_code == 0
        svg = (tmp_path / "style_test.svg").read_text()
        assert 'rx="8"' in svg

    def test_single_style_invalid(self, tmp_path):
        result = self.runner.invoke(
            app,
            [
                "single",
                "--left-text", "Build",
                "--left-color", "GREEN",
                "--badge-name", "style_test.svg",
                "--output-path", str(tmp_path),
                "--style", "neon",
            ],
        )
        assert result.exit_code == 1

    def test_batch_per_entry_style_override(self, tmp_path):
        config = [
            {
                "left_text": "A",
                "left_color": "#555555",
                "badge_name": "a.svg",
                "style": "rounded",
            },
            {
                "left_text": "B",
                "left_color": "#555555",
                "badge_name": "b.svg",
            },
        ]
        config_file = tmp_path / "badges.json"
        config_file.write_text(json.dumps(config))
        result = self.runner.invoke(
            app,
            ["batch", str(config_file), "--output-path", str(tmp_path)],
        )
        assert result.exit_code == 0
        assert 'rx="8"' in (tmp_path / "a.svg").read_text()
        assert 'rx="8"' not in (tmp_path / "b.svg").read_text()

    def test_batch_per_entry_invalid_style(self, tmp_path):
        config = [
            {
                "left_text": "A",
                "left_color": "#555555",
                "badge_name": "a.svg",
                "style": "neon",
            },
        ]
        config_file = tmp_path / "badges.json"
        config_file.write_text(json.dumps(config))
        result = self.runner.invoke(
            app,
            ["batch", str(config_file), "--output-path", str(tmp_path)],
        )
        assert result.exit_code == 1


class TestAuditCommand:
    """audit subcommand tests — no block_network fixture (filesystem I/O only)."""

    runner = CliRunner()  # plain runner, no mix_stderr needed

    def test_audit_clean_svg(self, tmp_path):
        """A clean SVG (no external URLs) exits 0."""
        from badgeshield import BadgeGenerator, BadgeTemplate
        from badgeshield.utils import BadgeColor
        gen = BadgeGenerator(template=BadgeTemplate.DEFAULT)
        gen.generate_badge(
            left_text="build", left_color=BadgeColor.GREEN,
            badge_name="clean.svg", output_path=str(tmp_path),
        )
        result = self.runner.invoke(app, ["audit", str(tmp_path / "clean.svg")])
        assert result.exit_code == 0

    def test_audit_dirty_svg_exits_1(self, tmp_path):
        """An SVG with an external href exits 1 and reports the violation."""
        dirty = tmp_path / "dirty.svg"
        dirty.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<image href="https://cdn.example.com/img.png"/>'
            '</svg>',
            encoding="utf-8",
        )
        result = self.runner.invoke(app, ["audit", str(dirty)])
        assert result.exit_code == 1
        assert "https://cdn.example.com/img.png" in result.output

    def test_audit_dirty_svg_json_output(self, tmp_path):
        """--json flag outputs machine-readable JSON."""
        import json as _json
        dirty = tmp_path / "dirty.svg"
        dirty.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<image href="https://cdn.example.com/img.png"/>'
            '</svg>',
            encoding="utf-8",
        )
        result = self.runner.invoke(app, ["audit", str(dirty), "--json"])
        assert result.exit_code == 1
        data = _json.loads(result.output)
        assert data["clean"] is False
        assert len(data["violations"]) == 1
        assert data["violations"][0]["url"] == "https://cdn.example.com/img.png"

    def test_audit_nonexistent_file_exits_2(self, tmp_path):
        result = self.runner.invoke(app, ["audit", str(tmp_path / "nope.svg")])
        assert result.exit_code == 2

    def test_audit_malformed_xml_exits_2(self, tmp_path):
        bad = tmp_path / "bad.svg"
        bad.write_text("<not valid xml<<<", encoding="utf-8")
        result = self.runner.invoke(app, ["audit", str(bad)])
        assert result.exit_code == 2

    def test_audit_non_svg_root_exits_2(self, tmp_path):
        not_svg = tmp_path / "foo.xml"
        not_svg.write_text("<foo><bar/></foo>", encoding="utf-8")
        result = self.runner.invoke(app, ["audit", str(not_svg)])
        assert result.exit_code == 2

    def test_audit_style_url_violation(self, tmp_path):
        """External URL inside a style attribute url() is detected."""
        svg = tmp_path / "style_url.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<rect style="fill:url(\'https://evil.com/grad\')"/>'
            '</svg>',
            encoding="utf-8",
        )
        result = self.runner.invoke(app, ["audit", str(svg)])
        assert result.exit_code == 1
