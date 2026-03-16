from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table

from pylogshield import LogLevel

from .badge_generator import BadgeBatchGenerator, BadgeGenerator
from .utils import BadgeColor, BadgeTemplate, FrameType
from .coverage import coverage_color, parse_coverage_xml

app = typer.Typer(
    name="badgeshield",
    help="Generate customizable SVG badges.",
    add_completion=False,
)


def _error(message: str) -> None:
    """Print a Rich error panel to stdout."""
    rprint(Panel(message, title="Error", border_style="red"))


@app.command()
def single(
    left_text: str = typer.Option(..., help="Text for the left section"),
    left_color: str = typer.Option(
        ..., help="Hex (#RRGGBB) or BadgeColor name e.g. GREEN"
    ),
    badge_name: str = typer.Option(
        ..., help="Output filename, must end with .svg"
    ),
    template: str = typer.Option("DEFAULT", help="DEFAULT | CIRCLE | CIRCLE_FRAME"),
    output_path: Optional[str] = typer.Option(
        None, help="Output directory; defaults to current directory"
    ),
    right_text: Optional[str] = typer.Option(None),
    right_color: Optional[str] = typer.Option(None),
    logo: Optional[str] = typer.Option(None, help="Path to a logo image"),
    logo_tint: Optional[str] = typer.Option(
        None, help="Hex or BadgeColor name to tint the logo"
    ),
    frame: Optional[str] = typer.Option(
        None, help="Frame type — required for CIRCLE_FRAME template"
    ),
    left_link: Optional[str] = typer.Option(None),
    right_link: Optional[str] = typer.Option(None),
    id_suffix: str = typer.Option(""),
    left_title: Optional[str] = typer.Option(None),
    right_title: Optional[str] = typer.Option(None),
    log_level: str = typer.Option(
        "INFO", help="DEBUG | INFO | WARNING | ERROR | CRITICAL"
    ),
) -> None:
    """Generate a single SVG badge."""
    try:
        log_level_enum = LogLevel[log_level.upper()]
    except KeyError:
        _error(
            f"Invalid log_level '{log_level}'. "
            f"Choose from: {', '.join(lv.name for lv in LogLevel)}"
        )
        raise typer.Exit(1)

    try:
        template_enum = BadgeTemplate[template.upper()]
    except KeyError:
        _error(
            f"Invalid template '{template}'. "
            f"Choose from: {', '.join(tmpl.name for tmpl in BadgeTemplate)}"
        )
        raise typer.Exit(1)

    try:
        frame_enum = FrameType[frame.upper()] if frame else None
    except KeyError:
        _error(
            f"Invalid frame '{frame}'. "
            f"Choose from: {', '.join(ft.name for ft in FrameType)}"
        )
        raise typer.Exit(1)

    try:
        generator = BadgeGenerator(template=template_enum, log_level=log_level_enum)
        generator.generate_badge(
            left_text=left_text,
            left_color=left_color,
            badge_name=badge_name,
            output_path=output_path,
            right_text=right_text,
            right_color=right_color,
            logo=logo,
            frame=frame_enum,
            left_link=left_link,
            right_link=right_link,
            id_suffix=id_suffix,
            left_title=left_title,
            right_title=right_title,
            logo_tint=logo_tint,
        )
    except (ValueError, TypeError) as exc:
        _error(str(exc))
        raise typer.Exit(1)


@app.command()
def batch(
    config_file: Path = typer.Argument(
        ...,
        exists=True,
        help="Path to JSON config file containing badge definitions",
    ),
    output_path: Optional[str] = typer.Option(
        None, help="Output directory; defaults to current directory"
    ),
    template: str = typer.Option("DEFAULT", help="DEFAULT | CIRCLE | CIRCLE_FRAME"),
    log_level: str = typer.Option("INFO"),
    max_workers: int = typer.Option(4, help="Parallel worker threads"),
) -> None:
    """Batch-generate SVG badges from a JSON config file."""
    # --- Validate log_level ---
    try:
        log_level_enum = LogLevel[log_level.upper()]
    except KeyError:
        _error(
            f"Invalid log_level '{log_level}'. "
            f"Choose from: {', '.join(lv.name for lv in LogLevel)}"
        )
        raise typer.Exit(1)

    # --- Validate template ---
    try:
        template_enum = BadgeTemplate[template.upper()]
    except KeyError:
        _error(
            f"Invalid template '{template}'. "
            f"Choose from: {', '.join(tmpl.name for tmpl in BadgeTemplate)}"
        )
        raise typer.Exit(1)

    # --- Parse config ---
    try:
        badge_configs = json.loads(config_file.read_text(encoding="utf-8"))
        if not isinstance(badge_configs, list):
            _error("Config file must contain a JSON array of badge objects.")
            raise typer.Exit(1)
    except json.JSONDecodeError as exc:
        _error(f"Invalid JSON in config file: {exc}")
        raise typer.Exit(1)

    # --- Validate each badge entry has badge_name ---
    for entry in badge_configs:
        if "badge_name" not in entry or not entry["badge_name"].endswith(".svg"):
            _error(
                "Each badge entry must include a 'badge_name' ending with '.svg'."
            )
            raise typer.Exit(1)

    # --- Inject CLI-level template and output_path ---
    for badge in badge_configs:
        badge["template"] = template_enum
        if output_path is not None:
            badge["output_path"] = output_path

    # --- CIRCLE_FRAME requires 'frame' in every badge entry ---
    if template_enum == BadgeTemplate.CIRCLE_FRAME:
        for badge in badge_configs:
            if "frame" not in badge:
                _error(
                    "CIRCLE_FRAME template requires a 'frame' key in every badge entry."
                )
                raise typer.Exit(1)

    # --- Run with Rich progress ---
    batch_gen = BadgeBatchGenerator(max_workers=max_workers, log_level=log_level_enum)
    total = len(badge_configs)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
    ) as progress:
        task = progress.add_task("Generating badges...", total=total)

        try:
            batch_gen.generate_batch(
                badge_configs,
                progress_callback=lambda name: progress.advance(task),
            )
        except RuntimeError:
            pass  # failures surfaced via summary table

    # --- Print summary table ---
    table = Table(title="Batch Results", show_lines=True)
    table.add_column("Badge", style="cyan")
    table.add_column("Status")
    table.add_column("Error", style="red")

    failure_map = {name: err for name, err in batch_gen._failures}
    for badge in badge_configs:
        name = badge["badge_name"]
        if name in failure_map:
            table.add_row(name, "[red]✗ FAIL[/red]", failure_map[name])
        else:
            table.add_row(name, "[green]✓ OK[/green]", "")

    rprint(table)

    if batch_gen._failures:
        raise typer.Exit(1)


@app.command()
def coverage(
    input: Path = typer.Argument(..., help="Path to coverage.xml"),
    badge_name: str = typer.Option(..., help="Output SVG filename (must end with .svg)"),
    output_path: Optional[str] = typer.Option(None, help="Output directory; defaults to CWD"),
    metric: str = typer.Option("line", help="Coverage metric: 'line' or 'branch'"),
    left_text: str = typer.Option("coverage", help="Left segment label"),
    log_level: str = typer.Option("INFO", help="Logging verbosity"),
) -> None:
    """Generate a coverage badge from a coverage.xml report."""
    try:
        log_level_enum = LogLevel[log_level.upper()]
    except KeyError:
        _error(f"Invalid log_level '{log_level}'. Choose from: {', '.join(lv.name for lv in LogLevel)}")
        raise typer.Exit(1)

    try:
        pct = parse_coverage_xml(input, metric=metric)
    except (FileNotFoundError, ValueError, ET.ParseError) as exc:
        _error(str(exc))
        raise typer.Exit(1)

    right_color = coverage_color(pct)
    right_text = f"{pct:.0f}%"

    try:
        gen = BadgeGenerator(template=BadgeTemplate.DEFAULT, log_level=log_level_enum)
        gen.generate_badge(
            left_text=left_text,
            left_color="#555555",
            right_text=right_text,
            right_color=right_color,
            badge_name=badge_name,
            output_path=output_path,
        )
    except (ValueError, TypeError) as exc:
        _error(str(exc))
        raise typer.Exit(1)

    typer.echo(f"Coverage badge generated: {pct:.1f}% ({metric} coverage)")


@app.command()
def audit(
    svg_file: Path = typer.Argument(..., help="Path to SVG file to audit"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Audit an SVG file for external resource references."""
    try:
        tree = ET.parse(svg_file)
    except FileNotFoundError:
        _error(f"File not found: {svg_file}")
        raise typer.Exit(2)
    except ET.ParseError as exc:
        _error(f"XML parse error: {exc}")
        raise typer.Exit(2)

    root = tree.getroot()
    tag = root.tag
    if not (tag == "svg" or tag.endswith("}svg")):
        _error(f"Root element is <{tag}>, not <svg>. Not an SVG file.")
        raise typer.Exit(2)

    violations = []
    for elem in root.iter():
        for attr_name, attr_value in elem.attrib.items():
            if attr_value.startswith("http://") or attr_value.startswith("https://"):
                violations.append({
                    "element": elem.tag,
                    "attribute": attr_name,
                    "url": attr_value,
                })
            if attr_name == "style":
                for match in re.findall(
                    r'url\(["\']?(https?://[^"\')\s]+)', attr_value
                ):
                    violations.append({
                        "element": elem.tag,
                        "attribute": "style[url]",
                        "url": match,
                    })

    if json_output:
        typer.echo(json.dumps({"clean": len(violations) == 0, "violations": violations}))
    else:
        if not violations:
            rprint("[green]\u2713 Clean \u2014 no external resource references found.[/green]")
        else:
            table = Table(title="External URL Violations", show_lines=True)
            table.add_column("Element", style="cyan")
            table.add_column("Attribute", style="yellow")
            table.add_column("URL", style="red", no_wrap=True)
            for v in violations:
                table.add_row(v["element"], v["attribute"], v["url"])
            rprint(table)

    if violations:
        raise typer.Exit(1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
