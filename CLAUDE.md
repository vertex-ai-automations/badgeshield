# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**badgeshield** is a Python package for generating customizable SVG badges. It supports rectangular, circle, and framed-circle templates with 51 predefined colors, logo embedding, batch processing, and both a programmatic API and CLI.

## Commands

### Testing
```bash
pytest tests/ -v --tb=short
# Run a single test file
pytest tests/test_badge_generator.py -v
# Run a single test
pytest tests/test_badge_generator.py::test_name -v
```

### Documentation
```bash
mkdocs build    # Build docs
mkdocs serve    # Serve docs locally
```

### Install for development
```bash
pip install -e .
pip install -r requirements.txt
```

### CLI usage
```bash
badgeshield single --left_text "Build" --left_color GREEN --badge_name build_badge.svg
badgeshield batch config.json --output_path ./badges/
```

Note: `badge_name` must always end with `.svg`.

## Architecture

### Source layout (`src/badgeshield/`)

- **`badge_generator.py`**: Two main classes:
  - `BadgeBatchGenerator`: Concurrent badge generation via `ThreadPoolExecutor`. Aggregates failures and raises `RuntimeError` with a summary if any badge fails.
  - `BadgeGenerator`: Core SVG generation. Uses Jinja2 to render templates. Text width is calculated using Pillow's `ImageFont` (DejaVuSans.ttf) with a character-width dict fallback. Logo images are base64-embedded and can be color-tinted by converting to RGBA and applying the tint while preserving alpha.

- **`generate_badge_cli.py`**: argparse CLI with two subcommands (`single`, `batch`). Validation functions normalize color names to hex before passing to `BadgeGenerator`.

- **`utils.py`**: Three enums — `BadgeColor` (51 colors), `FrameType` (11 PNG frames), `BadgeTemplate` (3 templates). These are the canonical type-safe inputs for the generator.

- **`templates/`**: Jinja2 SVG templates with autoescape enabled.
  - `label.svg` — DEFAULT: two-part horizontal badge, dynamic width, optional logo and links
  - `circle.svg` — CIRCLE: circle with font-size scaling based on text length
  - `circle_frame.svg` — CIRCLE_FRAME: circle overlaid with a PNG frame asset; requires `FrameType`

### Public API (`from badgeshield import ...`)

`BadgeGenerator`, `BadgeBatchGenerator`, `BadgeColor`, `BadgeTemplate`, `FrameType`, `LogLevel`

### Batch JSON config format

The JSON file passed to `batch` must be a list of objects, each with the same keys as `BadgeGenerator.generate_badge` kwargs. Required keys per entry: `left_text`, `left_color`, `badge_name` (ending in `.svg`). The `output_path` and `template` are supplied via CLI flags, not in the JSON.

### Key design decisions

- **Versioning**: `setuptools_scm` derives version from git tags (format `X.X.X`). The `_version.py` file is auto-generated — do not edit it manually.
- **Logging**: Uses `pylogshield` (`get_logger`), not stdlib `logging`. Log level can be passed as `LogLevel` enum or string.
- **Color input**: Accepts either a `BadgeColor` enum member or a hex string (`#RRGGBB`). Validation is done via `is_valid_hex_color()` and `validate_color()` in `badge_generator.py`.
- **Pillow is optional**: Only `jinja2` and `pylogshield` are required (`requirements.txt`). If Pillow is not installed, text width falls back to a char-width heuristic dict and logo tinting is silently skipped. Install Pillow separately for accurate text sizing: `pip install Pillow`.
- **CIRCLE_FRAME template**: Requires `frame` parameter (a `FrameType` enum); it is not optional for that template.

### CI/CD (`.github/workflows/release.yml`)

- **Docs job**: Triggers on push to `main` or manual dispatch — deploys MkDocs to GitHub Pages.
- **Publish job**: Triggers on tag push matching `X.X.X` — runs tests, builds, then publishes to TestPyPI then PyPI using GitHub OIDC trusted publishing.
