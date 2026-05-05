# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**badgeshield** is a Python package for generating customizable SVG badges. It supports 5 templates (DEFAULT, CIRCLE, CIRCLE_FRAME, PILL, BANNER), 4 visual styles, 51 predefined colors, logo embedding, batch processing, and both a programmatic API and CLI.

## Commands

### Testing
```bash
pytest tests/ -v --tb=short
# Run a single test file
pytest tests/test_badge_generator.py -v
# Run a single test
pytest tests/test_badge_generator.py::test_name -v
# Regenerate snapshot files (pill_basic.svg, banner_basic.svg, _lighten_hex_*.txt)
UPDATE_SNAPSHOTS=1 pytest tests/ -v
```

### Documentation
```bash
zensical build              # Build docs (output: public/)
zensical serve              # Serve docs locally at localhost:8000
zensical serve --open       # Serve and open browser automatically
```

Config file: `zensical.toml`. Docs dependencies: `pip install -e ".[docs]"` or `pip install -r docs/requirements.txt`.

### Install for development
```bash
pip install -e ".[dev]"          # runtime + test deps
pip install -e ".[dev,image]"    # also include Pillow for accurate text sizing
pip install -r requirements-dev.txt  # alternative: install test deps directly
```

### CLI usage
```bash
badgeshield single --left-text "Build" --left-color GREEN --badge-name build_badge.svg
badgeshield single --left-text "Status" --left-color "#555555" --badge-name s.svg --style gradient
badgeshield single --left-text "Build" --left-color GREEN --badge-name b.svg --format markdown
badgeshield batch config.json --output-path ./badges/ --style rounded
badgeshield coverage coverage.xml --badge-name coverage.svg --metric line
badgeshield audit badge.svg          # check SVG for external URL references
badgeshield audit badge.svg --json   # machine-readable output
badgeshield presets                  # list all named presets
badgeshield preset passing           # generate a single named preset badge
badgeshield preset version --search-path .   # data-wired preset (reads pyproject.toml/git)
badgeshield preset tests --junit junit.xml   # test results from JUnit XML
badgeshield preset coverage --coverage-xml coverage.xml
badgeshield preset --all --output-path ./badges/  # generate all resolvable presets
```

Notes:
- `badge_name` must always end with `.svg`.
- `--style` accepts `FLAT | ROUNDED | GRADIENT | SHADOWED` (case-insensitive; defaults to `flat`). Per-entry `style` keys in batch JSON take priority over the CLI flag.
- `--format markdown | rst | html` prints an embed snippet to stdout after generating a badge (available on `single`, `batch`, `coverage`, and `preset` subcommands).
- `preset --all` skips data-wired presets that return `unknown` or `untagged`; exits 1 if no badges were written at all.

## Architecture

### Source layout (`src/badgeshield/`)

- **`badge_generator.py`**: Two main classes:
  - `BadgeBatchGenerator`: Concurrent badge generation via `ThreadPoolExecutor`. Aggregates failures and raises `RuntimeError` with a summary if any badge fails.
  - `BadgeGenerator`: Core SVG generation. Uses Jinja2 to render templates. Text width is calculated using Pillow's `ImageFont` (DejaVuSans.ttf) with a character-width dict fallback. Logo images are base64-embedded and can be color-tinted by converting to RGBA and applying the tint while preserving alpha.

- **`generate_badge_cli.py`**: Typer + Rich CLI with four subcommands: `single`, `batch`, `coverage`, and `audit`. Enum validation (template, frame, style, log_level) is done at CLI entry before calling `BadgeGenerator`. The `batch` command shows a Rich progress bar and summary table; failures exit with code 1. The `audit` command scans an SVG for external `http`/`https` URLs in attributes and inline styles.

- **`coverage.py`**: Two standalone functions — `parse_coverage_xml(path, metric)` reads `line-rate` or `branch-rate` from a `coverage.xml` produced by `coverage run`, returning a float 0–100; `coverage_color(pct)` maps the percentage to a hex color. The `coverage` CLI subcommand wires these together to produce a DEFAULT-template badge.

- **`presets.py`**: `PRESETS` dict mapping preset names (e.g. `"passing"`, `"version"`) to `Preset` dataclass instances. Each preset has `label`, `color`, `right_text`, `right_color`, and an optional `source` callable `(search_path: Path) -> str`. Presets with `source=None` and no `right_text` require a CLI-provided file path (`tests` needs `--junit`, `coverage` needs `--coverage_xml`). Adding a new preset requires only a new entry in this dict.

- **`sources.py`**: Local project metadata extractors used by data-wired presets. Functions include `get_version` (5-step chain: pyproject.toml → setup.py → `_version.py` → git tag → "unknown"), `get_license`, `get_python_requires`, `get_git_branch`, `get_git_tag`, `get_git_commit_count`, `get_git_status`, `get_lines_of_code` (non-blank line count across source files), `get_test_results` (JUnit XML parser), and `get_coverage` (wraps `parse_coverage_xml`). All git functions use `_run_git()`, which raises `RuntimeError` if git is not on PATH but returns `""` (not an error) on non-zero exit code.

- **`utils.py`**: Four enums — `BadgeColor` (51 colors), `FrameType` (11 PNG frames), `BadgeTemplate` (5 templates), `BadgeStyle` (FLAT/ROUNDED/GRADIENT/SHADOWED). These are the canonical type-safe inputs for the generator.

- **`templates/`**: Jinja2 SVG templates with autoescape enabled.
  - `label.svg` — DEFAULT: two-part horizontal badge, dynamic width, optional logo and links
  - `circle.svg` — CIRCLE: circle with font-size scaling based on text length
  - `circle_frame.svg` — CIRCLE_FRAME: circle overlaid with a PNG frame asset; requires `FrameType`
  - `pill.svg` — PILL: fully rounded ends (rx=10 always), always uses style_ctx but overrides `rx`
  - `banner.svg` — BANNER: fixed icon-zone on left (28px) + right text section

### Public API (`from badgeshield import ...`)

`BadgeGenerator`, `BadgeBatchGenerator`, `BadgeColor`, `BadgeTemplate`, `BadgeStyle`, `FrameType`, `LogLevel`, `parse_coverage_xml`, `coverage_color`

`PRESETS` and `Preset` are exported from the public API. `sources.*` functions are internal helpers; import directly from `badgeshield.sources` if needed.

### Batch JSON config format

The JSON file passed to `batch` must be a list of objects, each with the same keys as `BadgeGenerator.generate_badge` kwargs. Required keys per entry: `left_text`, `left_color`, `badge_name` (ending in `.svg`). The `output_path` and `template` are supplied via CLI flags, not in the JSON. An optional `style` key per entry (string, case-insensitive) overrides the CLI `--style` flag for that badge.

### Key design decisions

- **Versioning**: `setuptools_scm` derives version from git tags (format `X.X.X`). The `_version.py` file is auto-generated — do not edit it manually.
- **Logging**: Uses `pylogshield` (`get_logger`), not stdlib `logging`. Log level can be passed as `LogLevel` enum or string.
- **Color input**: Accepts either a `BadgeColor` enum member or a hex string (`#RRGGBB`). Validation is done via `is_valid_hex_color()` and `validate_color()` in `badge_generator.py`.
- **Pillow is optional**: Only `jinja2` and `pylogshield` are required (`requirements.txt`). If Pillow is not installed, text width falls back to a char-width heuristic dict and logo tinting is silently skipped. Install the extras group for accurate text sizing: `pip install badgeshield[image]`.
- **CIRCLE_FRAME template**: Requires `frame` parameter (a `FrameType` enum); it is not optional for that template.
- **Renderer dispatch**: `BadgeGenerator._RENDERERS` is a class-level dict mapping `BadgeTemplate` → `_render_*` method, populated after the class body. To add a new template, add a `_render_<name>` method and register it in `_RENDERERS`.
- **Style system**: `_style_context()` returns a dict of Jinja2 context vars (`rx`, `gradient_id`, `gradient_stop`, `gradient_base`, `shadow_id`). Templates that don't support gradient (e.g. CIRCLE_FRAME) clear gradient keys after calling `_style_context`. PILL always forces `rx="10"` regardless of style.

### CI/CD (`.github/workflows/release.yml`)

- **Docs job**: Triggers on push to `main` or manual dispatch — deploys MkDocs to GitHub Pages.
- **Publish job**: Triggers on tag push matching `X.X.X` — runs tests, builds, then publishes to TestPyPI then PyPI using GitHub OIDC trusted publishing.
