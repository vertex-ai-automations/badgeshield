# FAQ

## General

### What badge templates are available?

Three templates are included:

| Template | Shape | Notes |
|----------|-------|-------|
| `DEFAULT` | Rectangular, two-part | Width is calculated from text; supports logos, links |
| `CIRCLE` | Circle | Font size shrinks for longer text |
| `CIRCLE_FRAME` | Circle with decorative frame | Requires a `FrameType` (FRAME1–FRAME11) |

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

### Why did the flags change from `--left_text` to `--left-text`?

BadgeShield's CLI was rewritten with [Typer](https://typer.tiangolo.com/), which automatically converts Python parameter names (using underscores) to POSIX-style CLI flags (using hyphens). This is standard CLI convention.

**Old (argparse):** `--left_text "build"`
**New (Typer):** `--left-text "build"`

---

### The CLI exits with code 1 — what happened?

An error panel is printed to stdout describing the cause. Common reasons:

- **Invalid color**: unrecognized `BadgeColor` name or malformed hex string.
- **Missing `.svg` suffix**: `--badge-name` must end with `.svg`.
- **Invalid template**: must be `DEFAULT`, `CIRCLE`, or `CIRCLE_FRAME`.
- **Missing `--frame`**: required when `--template CIRCLE_FRAME` is used.
- **Output path not found**: the `--output-path` directory must already exist.

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

### Can I get the SVG as a string without writing a file?

Yes — use `render_badge()` instead of `generate_badge()`. It returns a `BadgeSVG` string with no file I/O:

```python
from badgeshield import BadgeGenerator, BadgeSVG, BadgeTemplate

gen = BadgeGenerator(template=BadgeTemplate.DEFAULT)
svg: BadgeSVG = gen.render_badge(
    left_text="build",
    left_color="#555555",
    right_text="passing",
    right_color="#44cc11",
)

# Use anywhere a string is accepted
print(len(svg))          # character count
assert "<svg" in svg     # plain string checks work

# Built-in conversions
raw_bytes = svg.to_bytes()
data_uri  = svg.to_data_uri()   # "data:image/svg+xml;base64,..."
svg.save("./badges/build.svg")  # write to disk when ready
```

---

### When should I use `render_badge()` vs `generate_badge()`?

| Use case | Method |
|----------|--------|
| Writing a badge to a file (CI pipeline, batch) | `generate_badge()` |
| Serving a badge over HTTP | `render_badge()` + `.to_bytes()` |
| Embedding a badge inline in HTML | `render_badge()` + `.to_data_uri()` |
| Testing badge content without touching the filesystem | `render_badge()` |
| Generating many badges and deciding later where to store them | `render_badge()` |

---

## Contributing

Found a bug or want a new template? Open an issue or pull request on [GitHub](https://github.com/vertex-ai-automations/badgeshield/issues/new).
