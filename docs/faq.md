# FAQ

## General

### What badge templates are available?

Five templates are included:

| Template | Shape | Notes |
|----------|-------|-------|
| `DEFAULT` | Rectangular, two-part | Width calculated from text; supports logos, links, titles |
| `PILL` | Fully-rounded two-part | Always rx=10 regardless of style |
| `CIRCLE` | Circle | Font size shrinks for longer text |
| `CIRCLE_FRAME` | Circle with decorative frame | Requires a `FrameType` (FRAME1–FRAME11) |
| `BANNER` | Wide banner | 28px icon-zone on left (first letter of `left_text`), text section on right |

---

### Can I use custom colors?

Yes. Pass any six-digit hex string (`#RRGGBB`) for `left_color`, `right_color`, or `logo_tint`. You can also use any of the 51 built-in `BadgeColor` enum names (e.g. `GREEN`, `DARK_PURPLE`, `NEON_CYAN`). See [Utilities](reference/utils.md) for the full color list.

---

### Does BadgeShield require Pillow?

Pillow is **optional**. When installed, it:

- Measures text widths using real font metrics (DejaVuSans.ttf) for accurate badge sizing.
- Enables logo color tinting.

Without Pillow, badge generation still works — text widths fall back to a character-width lookup table, and logos are embedded without tinting.

Install with image support:
```bash
pip install "badgeshield[image]"
```

---

## Coverage Badge

### How do I generate a coverage badge from coverage.xml?

Run `coverage run` and `coverage xml` first, then pass the output to `badgeshield coverage`:

```bash
coverage run -m pytest
coverage xml
badgeshield coverage coverage.xml --badge-name coverage.svg --output-path ./badges
```

The color is chosen automatically based on the percentage.

---

### How do I badge on branch coverage instead of line coverage?

Pass `--metric branch`:

```bash
badgeshield coverage coverage.xml --metric branch --badge-name coverage.svg
```

Or in Python:

```python
from badgeshield import parse_coverage_xml
pct = parse_coverage_xml("coverage.xml", metric="branch")
```

---

### Can I use the coverage functions without the CLI?

Yes — `parse_coverage_xml()` and `coverage_color()` are public API:

```python
from badgeshield import parse_coverage_xml, coverage_color

pct = parse_coverage_xml("coverage.xml")   # float, e.g. 94.3
color = coverage_color(pct)               # str, e.g. "#44cc11"
```

---

## CLI

### Do I use underscores or hyphens in CLI flags?

It depends on the subcommand. The `single` command uses explicit underscore flags for its four core arguments — this is intentional to preserve backwards compatibility:

```bash
badgeshield single --left_text "build" --left_color GREEN --badge_name build.svg --output_path ./badges
```

All other `single` flags (e.g. `--right-text`, `--logo-tint`, `--id-suffix`) use hyphens, as does every flag in the `batch`, `coverage`, and `audit` subcommands. When in doubt, run `badgeshield <subcommand> --help` to see the exact flag names.

---

### The CLI exits with code 1 — what happened?

An error panel is printed to stdout describing the cause. Common reasons:

- **Invalid color**: unrecognized `BadgeColor` name or malformed hex string.
- **Missing `.svg` suffix**: the badge name argument must end with `.svg`.
- **Invalid template**: must be `DEFAULT`, `PILL`, `CIRCLE`, `CIRCLE_FRAME`, or `BANNER`.
- **Invalid style**: must be `FLAT`, `ROUNDED`, `GRADIENT`, or `SHADOWED`.
- **Missing `--frame`**: required when `--template CIRCLE_FRAME` is used.
- **Output path not found**: the output directory must already exist.

---

### How do I use CIRCLE_FRAME in batch mode?

Each badge entry in the JSON config must include a `"frame"` key:

```json
[
  {
    "badge_name": "initials.svg",
    "left_text": "MH",
    "left_color": "#673ab7",
    "frame": "FRAME1"
  }
]
```

Then pass `--template CIRCLE_FRAME` to the `batch` command:

```bash
badgeshield batch config.json --template CIRCLE_FRAME --output-path ./out
```

---

## Programmatic API

### How do I generate badges into different directories per badge?

Set `output_path` individually on each badge dict when using `BadgeBatchGenerator`:

```python
badges = [
    {"badge_name": "a.svg", "left_text": "alpha", "left_color": "GREEN",  "output_path": "./team-a"},
    {"badge_name": "b.svg", "left_text": "beta",  "left_color": "#0000ff", "output_path": "./team-b"},
]
batch.generate_batch(badges)
```

---

### Can I track progress during batch generation?

Yes — pass a `progress_callback` callable that accepts a badge name:

```python
from badgeshield import BadgeBatchGenerator

batch = BadgeBatchGenerator(max_workers=4)

completed = []
batch.generate_batch(badges, progress_callback=lambda name: completed.append(name))
print(f"Done: {len(completed)} badges")
```

---

### How do I handle batch failures without crashing?

Wrap `generate_batch` in a `try/except RuntimeError` and inspect `batch._failures`:

```python
try:
    batch.generate_batch(badges)
except RuntimeError:
    for badge_name, error in batch._failures:
        print(f"  FAIL {badge_name}: {error}")
```

---

### Can I embed multiple badges in the same HTML page?

Yes. Use `id_suffix` to make SVG element IDs unique when embedding more than one badge:

```python
gen.generate_badge(..., badge_name="build.svg",    id_suffix="-build")
gen.generate_badge(..., badge_name="coverage.svg", id_suffix="-coverage")
```

---

### Can I apply visual styles to badges?

Yes — pass a `BadgeStyle` value to `BadgeGenerator` at construction time:

```python
from badgeshield import BadgeGenerator, BadgeStyle, BadgeTemplate

gen = BadgeGenerator(template=BadgeTemplate.DEFAULT, style=BadgeStyle.GRADIENT)
gen.generate_badge(
    left_text="build",
    left_color="#555555",
    right_text="passing",
    right_color="#44cc11",
    badge_name="build.svg",
)
```

Available styles: `FLAT` (default), `ROUNDED`, `GRADIENT`, `SHADOWED`. The `--style` CLI flag accepts the same values (case-insensitive).

---

### Can I verify my SVG has no external URLs?

Yes — use the `audit` subcommand:

```bash
badgeshield audit badges/build.svg
badgeshield audit badges/build.svg --json   # machine-readable output
```

Exit code `0` means clean; `1` means external URLs were found; `2` means the file could not be parsed.

---

## Contributing

Found a bug or want a new template? Open an issue or pull request on [GitHub](https://github.com/vertex-ai-automations/badgeshield/issues/new).
