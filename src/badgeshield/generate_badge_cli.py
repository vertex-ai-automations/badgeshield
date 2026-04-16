from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional

import typer
from rich import print as rprint
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table

from pylogshield import LogLevel

from .badge_generator import BadgeBatchGenerator, BadgeGenerator
from .utils import BadgeColor, BadgeStyle, BadgeTemplate, FrameType
from .coverage import coverage_color, parse_coverage_xml
from .presets import PRESETS
from .sources import get_test_results, get_coverage, get_lines_of_code

app = typer.Typer(
    name="badgeshield",
    help="Generate customizable SVG badges.",
    add_completion=False,
)


def _error(message: str) -> None:
    """Print a Rich error panel to stdout."""
    rprint(Panel(message, title="Error", border_style="red"))


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


@app.command()
def single(
    left_text: str = typer.Option(..., "--left_text", help="Text for the left section"),
    left_color: str = typer.Option(
        ..., "--left_color", help="Hex (#RRGGBB) or BadgeColor name e.g. GREEN"
    ),
    badge_name: str = typer.Option(
        ..., "--badge_name", help="Output filename, must end with .svg"
    ),
    template: str = typer.Option("DEFAULT", help="DEFAULT | CIRCLE | CIRCLE_FRAME"),
    output_path: Optional[str] = typer.Option(
        None, "--output_path", help="Output directory; defaults to current directory"
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
    style: str = typer.Option("flat", help="FLAT | ROUNDED | GRADIENT | SHADOWED"),
    format: Optional[str] = typer.Option(None, "--format", help="Embed snippet format: markdown | rst | html"),
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
        style_enum = BadgeStyle[style.upper()]
    except KeyError:
        _error(
            f"Invalid style '{style}'. "
            f"Choose from: {', '.join(s.name for s in BadgeStyle)}"
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
        generator = BadgeGenerator(template=template_enum, log_level=log_level_enum, style=style_enum)
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

    if format:
        fmt_lower = format.lower()
        if fmt_lower not in ("markdown", "rst", "html"):
            _error(f"Invalid format '{format}'. Choose from: markdown, rst, html")
            raise typer.Exit(1)
        svg_path = str(Path(output_path or ".") / badge_name)
        typer.echo(_format_snippet(svg_path, left_text, fmt_lower))


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
    style: str = typer.Option("flat", help="FLAT | ROUNDED | GRADIENT | SHADOWED"),
    format: Optional[str] = typer.Option(None, "--format", help="Embed snippet format: markdown | rst | html"),
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

    # --- Validate style ---
    try:
        style_enum = BadgeStyle[style.upper()]
    except KeyError:
        _error(
            f"Invalid style '{style}'. "
            f"Choose from: {', '.join(s.name for s in BadgeStyle)}"
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

    # --- Inject CLI-level template, output_path, and style ---
    for badge in badge_configs:
        badge["template"] = template_enum
        if output_path is not None:
            badge["output_path"] = output_path
        # Per-entry style takes priority; inject CLI style only if not set
        if "style" not in badge:
            badge["style"] = style_enum
        else:
            # Validate per-entry style string
            try:
                badge["style"] = BadgeStyle[str(badge["style"]).upper()]
            except KeyError:
                _error(
                    f"Invalid per-entry style '{badge['style']}'. "
                    f"Choose from: {', '.join(s.name for s in BadgeStyle)}"
                )
                raise typer.Exit(1)

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

    if format:
        fmt_lower = format.lower()
        if fmt_lower not in ("markdown", "rst", "html"):
            _error(f"Invalid format '{format}'. Choose from: markdown, rst, html")
            raise typer.Exit(1)
        for badge in badge_configs:
            if badge["badge_name"] not in failure_map:
                svg_path = str(Path(output_path or ".") / badge["badge_name"])
                typer.echo(_format_snippet(svg_path, badge.get("left_text", badge["badge_name"]), fmt_lower))

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
    format: Optional[str] = typer.Option(None, "--format", help="Embed snippet format: markdown | rst | html"),
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

    if format:
        fmt_lower = format.lower()
        if fmt_lower not in ("markdown", "rst", "html"):
            _error(f"Invalid format '{format}'. Choose from: markdown, rst, html")
            raise typer.Exit(1)
        svg_path = str(Path(output_path or ".") / badge_name)
        typer.echo(_format_snippet(svg_path, left_text, fmt_lower))


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


@app.command(name="presets")
def presets_list() -> None:
    """List all available badge presets."""
    table = Table(title="Available Presets", show_lines=True)
    table.add_column("Name", style="cyan")
    table.add_column("Label")
    table.add_column("Type")
    table.add_column("Description")
    for name, preset in PRESETS.items():
        kind = "data-wired" if (preset.source is not None or name in ("tests", "coverage")) else "cosmetic"
        table.add_row(name, preset.label, kind, preset.description)
    rprint(table)


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
                if right_text in _SKIP_VALUES:
                    skipped.append((name, f"resolved to '{right_text}'"))
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


@app.command(name="preset")
def preset_cmd(
    name: Optional[str] = typer.Argument(None, help="Preset name (see 'badgeshield presets')"),
    badge_name: Optional[str] = typer.Option(None, "--badge_name", help="Output filename (defaults to {name}.svg)"),
    output_path: Optional[str] = typer.Option(None, "--output_path", help="Output directory (default: current directory)"),
    search_path: str = typer.Option(".", "--search_path", help="Repo root for source resolution"),
    style: str = typer.Option("flat", help="FLAT | ROUNDED | GRADIENT | SHADOWED"),
    format: Optional[str] = typer.Option(None, "--format", help="markdown | rst | html"),
    extensions: Optional[List[str]] = typer.Option(None, help="File extensions for lines preset (repeatable)"),
    junit: Optional[Path] = typer.Option(None, "--junit", help="Path to JUnit XML for tests preset"),
    coverage_xml: Optional[Path] = typer.Option(None, "--coverage_xml", help="Path to coverage.xml for coverage preset"),
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
    elif p.source is not None:
        try:
            right_text = p.source(sp)
        except RuntimeError as exc:
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


def main() -> None:
    app()


if __name__ == "__main__":
    main()
