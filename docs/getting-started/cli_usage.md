# CLI Usage

BadgeShield ships a Typer-powered CLI with Rich progress bars and error panels.

```bash
badgeshield --help
```

Two subcommands are available: `single` and `batch`.

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
| `--template` | | `DEFAULT` (default), `CIRCLE`, or `CIRCLE_FRAME` |
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
| `--template` | | `DEFAULT` (default), `CIRCLE`, or `CIRCLE_FRAME` |
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

!!! tip "CIRCLE_FRAME in batch mode"
    When using `--template CIRCLE_FRAME`, every entry in the JSON config must include a `"frame"` key (e.g. `"frame": "FRAME1"`).
