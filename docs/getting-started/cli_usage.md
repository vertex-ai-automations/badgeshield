# CLI Usage

BadgeShield ships a Typer-powered CLI with Rich progress bars and error panels.

```bash
badgeshield --help
```

Four subcommands are available: `coverage`, `single`, `batch`, and `audit`.

---

## Coverage badge

Generate a correctly-colored badge from a `coverage.xml` file — no manual color picking needed.

```bash
badgeshield coverage --help
```

### Parameters

| Argument / Flag | Required | Description |
|-----------------|:--------:|-------------|
| `INPUT` (positional) | ✅ | Path to `coverage.xml` |
| `--badge-name` | ✅ | Output SVG filename — must end with `.svg` |
| `--output-path` | | Output directory; defaults to CWD |
| `--metric` | | `line` (default) or `branch` |
| `--left-text` | | Left segment label (default: `coverage`) |
| `--log-level` | | `DEBUG`, `INFO` (default), `WARNING`, `ERROR`, `CRITICAL` |

### Color thresholds

The right-side color is chosen automatically:

| Coverage | Color |
|----------|-------|
| ≥ 90% | `#44cc11` (green) |
| ≥ 80% | `#97ca00` (yellow-green) |
| ≥ 70% | `#a4a61d` (yellow) |
| ≥ 60% | `#dfb317` (orange) |
| < 60%  | `#e05d44` (red) |

### Examples

**Line coverage (default):**

```bash
badgeshield coverage coverage.xml \
  --badge-name coverage.svg \
  --output-path ./badges
```

**Branch coverage:**

```bash
badgeshield coverage coverage.xml \
  --metric branch \
  --badge-name coverage-branch.svg \
  --output-path ./badges
```

**Custom label:**

```bash
badgeshield coverage coverage.xml \
  --badge-name tested.svg \
  --left-text "tested" \
  --output-path ./badges
```

---

## Single badge

Generate one SVG badge from command-line arguments.

```bash
badgeshield single --help
```

### Parameters

| Flag | Required | Description |
|------|:--------:|-------------|
| `--left-text` | ✅ | Text on the left segment |
| `--left-color` | ✅ | Hex `#RRGGBB` or `BadgeColor` name (e.g. `GREEN`) |
| `--badge-name` | ✅ | Output SVG filename — must end with `.svg` |
| `--output-path` | | Output directory; defaults to CWD |
| `--template` | | `DEFAULT` (default), `PILL`, `CIRCLE`, `CIRCLE_FRAME`, or `BANNER` |
| `--style` | | `FLAT` (default), `ROUNDED`, `GRADIENT`, or `SHADOWED` |
| `--right-text` | | Text on the right segment |
| `--right-color` | | Color for the right segment |
| `--frame` | | `FRAME1`–`FRAME11`; required for `CIRCLE_FRAME` |
| `--logo` | | Path to an image to embed |
| `--logo-tint` | | Hex or `BadgeColor` name to recolor the logo |
| `--left-link` | | Hyperlink for the left segment |
| `--right-link` | | Hyperlink for the right segment |
| `--id-suffix` | | Appended to SVG element IDs |
| `--left-title` | | Accessible title for the left segment |
| `--right-title` | | Accessible title for the right segment |
| `--log-level` | | `DEBUG`, `INFO` (default), `WARNING`, `ERROR`, `CRITICAL` |

### Examples

**Minimal — left text only:**

```bash
badgeshield single \
  --left-text "flake8" \
  --left-color "#4b0082" \
  --badge-name flake8.svg
```

**Two-part badge:**

```bash
badgeshield single \
  --left-text "coverage" \
  --left-color "#555555" \
  --right-text "94%" \
  --right-color "#44cc11" \
  --badge-name coverage.svg \
  --output-path ./badges
```

**With logo:**

```bash
badgeshield single \
  --left-text "python" \
  --left-color "#3776ab" \
  --logo path/to/python.png \
  --logo-tint "#ffffff" \
  --badge-name python.svg \
  --output-path ./badges
```

**Pill template with gradient style:**

```bash
badgeshield single \
  --left-text "build" \
  --left-color "#555555" \
  --right-text "passing" \
  --right-color "#44cc11" \
  --template PILL \
  --style gradient \
  --badge-name build-pill.svg \
  --output-path ./badges
```

**Circle frame template:**

```bash
badgeshield single \
  --left-text "MH" \
  --left-color "#673ab7" \
  --template CIRCLE_FRAME \
  --frame FRAME1 \
  --badge-name initials.svg \
  --output-path ./badges
```

**Banner template:**

```bash
badgeshield single \
  --left-text "badgeshield" \
  --left-color "#1a1a2e" \
  --right-text "v1.0" \
  --right-color "#16213e" \
  --template BANNER \
  --badge-name banner.svg \
  --output-path ./badges
```

**With links and titles (accessibility):**

```bash
badgeshield single \
  --left-text "build" \
  --left-color "#555" \
  --right-text "passing" \
  --right-color "#44cc11" \
  --left-link "https://example.com/pipeline" \
  --right-link "https://example.com/results" \
  --left-title "Pipeline status" \
  --right-title "Test result" \
  --badge-name build.svg
```

---

## Batch generation

Generate many badges in parallel from a JSON configuration file.

```bash
badgeshield batch --help
```

### Parameters

| Argument / Flag | Required | Description |
|-----------------|:--------:|-------------|
| `CONFIG_FILE` (positional) | ✅ | Path to JSON config file |
| `--output-path` | | Output directory; defaults to CWD |
| `--template` | | `DEFAULT` (default), `PILL`, `CIRCLE`, `CIRCLE_FRAME`, or `BANNER` |
| `--style` | | `FLAT` (default), `ROUNDED`, `GRADIENT`, or `SHADOWED` |
| `--log-level` | | Logging verbosity |
| `--max-workers` | | Parallel threads (default: 4) |

### Config file format

The JSON file must be an **array** of badge objects. Each object accepts any parameter from the Python API:

```json
[
  {
    "badge_name": "build.svg",
    "left_text": "build",
    "left_color": "GREEN"
  },
  {
    "badge_name": "coverage.svg",
    "left_text": "coverage",
    "left_color": "#555555",
    "right_text": "94%",
    "right_color": "#44cc11"
  },
  {
    "badge_name": "version.svg",
    "left_text": "v2.1.0",
    "left_color": "#673ab7"
  }
]
```

### Example

```bash
badgeshield batch badges.json \
  --output-path ./badges \
  --max-workers 8
```

A Rich progress bar tracks completion. After all badges are processed, a summary table is printed:

```
                  Batch Results
┌──────────────┬────────────┬───────┐
│ Badge        │ Status     │ Error │
├──────────────┼────────────┼───────┤
│ build.svg    │ ✓ OK       │       │
│ coverage.svg │ ✓ OK       │       │
│ version.svg  │ ✓ OK       │       │
└──────────────┴────────────┴───────┘
```

Failures are shown in red with the error message. The command exits with code `1` if any badge fails.

Per-entry `style` keys in the JSON override the CLI `--style` flag for that badge:

```json
[
  { "badge_name": "a.svg", "left_text": "alpha", "left_color": "GREEN", "style": "gradient" },
  { "badge_name": "b.svg", "left_text": "beta",  "left_color": "BLUE" }
]
```

!!! tip "CIRCLE_FRAME in batch mode"
    When using `--template CIRCLE_FRAME`, every entry in the JSON config must include a `"frame"` key (e.g. `"frame": "FRAME1"`).

---

## SVG audit

Scan a generated SVG for external resource references (URLs in attributes or `style` properties). Useful in CI to confirm all assets are inlined.

```bash
badgeshield audit --help
```

### Parameters

| Argument / Flag | Required | Description |
|-----------------|:--------:|-------------|
| `SVG_FILE` (positional) | ✅ | Path to the SVG file to inspect |
| `--json` | | Emit machine-readable JSON instead of a Rich table |

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Clean — no external URLs found |
| `1` | Violations found |
| `2` | File not found or not valid SVG/XML |

### Examples

**Human-readable output:**

```bash
badgeshield audit badges/build.svg
```

**CI-friendly JSON output:**

```bash
badgeshield audit badges/build.svg --json
# {"clean": true, "violations": []}
```

**Integrate in CI (fails if any external URL is present):**

```bash
for f in badges/*.svg; do badgeshield audit "$f"; done
```

---

## Preset Badges

Generate badges from named presets — no need to specify colors or text manually.

### List available presets

```bash
badgeshield presets
```

### Generate a single preset

```bash
# Cosmetic preset — value is fixed
badgeshield preset passing --output_path ./badges/

# Data-wired preset — value resolved from local repo
badgeshield preset version --output_path ./badges/
badgeshield preset lines --extensions .py --extensions .js --output_path ./badges/
badgeshield preset tests --junit tests/junit.xml --output_path ./badges/
```

### Generate all presets at once

```bash
badgeshield preset --all --output_path ./badges/ --format markdown
```

### Embed snippets

Add `--format markdown|rst|html` to any command to print an embed snippet:

```bash
badgeshield preset version --format markdown
# output: ![version](./version.svg)
```
