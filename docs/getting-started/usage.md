# Python API

## Basic badge

```python
from badgeshield import BadgeGenerator, BadgeTemplate

generator = BadgeGenerator(template=BadgeTemplate.DEFAULT)
generator.generate_badge(
    left_text="build",
    left_color="#555555",
    right_text="passing",
    right_color="#44cc11",
    badge_name="build.svg",
)
```

The file is written to the current working directory by default. Use `output_path` to specify a directory.

## Parameters

| Parameter | Required | Type | Description |
|-----------|:--------:|------|-------------|
| `left_text` | ✅ | `str` | Text on the left segment |
| `left_color` | ✅ | `BadgeColor` or `str` | Hex `#RRGGBB` or `BadgeColor` enum name |
| `badge_name` | ✅ | `str` | Output filename — must end with `.svg` |
| `output_path` | | `str` | Output directory; defaults to CWD |
| `right_text` | | `str` | Text on the right segment |
| `right_color` | | `BadgeColor` or `str` | Color for the right segment |
| `template` | | `BadgeTemplate` | `DEFAULT`, `CIRCLE`, or `CIRCLE_FRAME` |
| `frame` | | `FrameType` | Required when using `CIRCLE_FRAME` |
| `logo` | | `str` | Path to an image to embed in the badge |
| `logo_tint` | | `BadgeColor` or `str` | Hex/enum color applied to the logo silhouette |
| `left_link` | | `str` | Hyperlink for the left segment |
| `right_link` | | `str` | Hyperlink for the right segment |
| `id_suffix` | | `str` | Appended to SVG element IDs (useful for embedding multiple badges) |
| `left_title` | | `str` | Accessible `<title>` for the left segment |
| `right_title` | | `str` | Accessible `<title>` for the right segment |
| `log_level` | | `LogLevel` | Logging verbosity; passed to `BadgeGenerator.__init__` |

## Templates

=== "DEFAULT"

    Standard two-part horizontal badge. Width is calculated dynamically from text length.

    ```python
    from badgeshield import BadgeGenerator, BadgeTemplate

    gen = BadgeGenerator(template=BadgeTemplate.DEFAULT)
    gen.generate_badge(
        left_text="status",
        left_color="#555",
        right_text="passing",
        right_color="#44cc11",
        badge_name="status.svg",
    )
    ```

=== "CIRCLE"

    Circular badge with font size that shrinks for longer text.

    ```python
    from badgeshield import BadgeGenerator, BadgeTemplate

    gen = BadgeGenerator(template=BadgeTemplate.CIRCLE)
    gen.generate_badge(
        left_text="v2.1",
        left_color="#673ab7",
        badge_name="version.svg",
    )
    ```

=== "CIRCLE_FRAME"

    Circle badge with a decorative PNG frame overlay. The `frame` parameter is required.

    ```python
    from badgeshield import BadgeGenerator, BadgeTemplate, FrameType

    gen = BadgeGenerator(template=BadgeTemplate.CIRCLE_FRAME)
    gen.generate_badge(
        left_text="MH",
        left_color="#FF0000",
        badge_name="initials.svg",
        frame=FrameType.FRAME1,
    )
    ```

    Available frames: `FRAME1` through `FRAME11`.

## Colors

Use a `BadgeColor` enum name or any hex string:

```python
from badgeshield.utils import BadgeColor

# Enum
generator.generate_badge(left_color=BadgeColor.DARK_GREEN, ...)

# Hex string
generator.generate_badge(left_color="#4caf50", ...)

# Enum name string (also accepted)
generator.generate_badge(left_color="DARK_GREEN", ...)
```

51 colors are available across standard, light, dark, pastel, and neon families. See [Utilities](../reference/utils.md) for the full list.

## Logo tinting

Embed a monochrome logo and recolor it to match your badge:

```python
generator.generate_badge(
    left_text="shield",
    left_color="#673ab7",
    badge_name="shield.svg",
    logo="path/to/icon.png",
    logo_tint="#ffffff",   # tint logo white
)
```

!!! note "Pillow required"
    Logo tinting requires `pip install "badgeshield[image]"`. Without Pillow the logo is embedded as-is.

## Batch generation

Generate many badges concurrently from a list of dicts:

```python
from badgeshield import BadgeBatchGenerator, BadgeTemplate

batch = BadgeBatchGenerator(max_workers=4)
badges = [
    {"badge_name": "build.svg",    "left_text": "build",    "left_color": "GREEN",   "output_path": "./out", "template": BadgeTemplate.DEFAULT},
    {"badge_name": "coverage.svg", "left_text": "coverage", "left_color": "#555",    "right_text": "94%", "right_color": "#44cc11", "output_path": "./out", "template": BadgeTemplate.DEFAULT},
    {"badge_name": "version.svg",  "left_text": "v2.1.0",   "left_color": "#673ab7", "output_path": "./out", "template": BadgeTemplate.DEFAULT},
]

def on_progress(badge_name: str) -> None:
    print(f"  ✓ {badge_name}")

batch.generate_batch(badges, progress_callback=on_progress)
```

If any badge fails, `generate_batch` raises `RuntimeError` with a summary. Inspect `batch._failures` (a list of `(badge_name, error_str)` tuples) for details.

## In-memory rendering

Use `render_badge()` to get the SVG as a string — no file written:

```python
from badgeshield import BadgeGenerator, BadgeSVG, BadgeTemplate

gen = BadgeGenerator(template=BadgeTemplate.DEFAULT)
svg: BadgeSVG = gen.render_badge(
    left_text="build",
    left_color="#555555",
    right_text="passing",
    right_color="#44cc11",
)
```

`BadgeSVG` is a `str` subclass so it works anywhere a string is expected. It also ships three helpers:

| Method | Returns | Description |
|--------|---------|-------------|
| `.to_bytes(encoding="utf-8")` | `bytes` | SVG encoded as bytes |
| `.to_data_uri()` | `str` | Base64-encoded `data:image/svg+xml` URI |
| `.save(path)` | `None` | Write to a file path |

**Typical uses:**

```python
# Serve over HTTP
response_body = svg.to_bytes()

# Inline in HTML without a separate file
data_uri = svg.to_data_uri()
html = f'<img src="{data_uri}" alt="build status">'

# Inspect SVG content in tests
assert "<svg" in svg
assert "passing" in svg

# Write to disk when you're ready
svg.save("./badges/build.svg")
```

All parameters accepted by `generate_badge()` (except `badge_name` and `output_path`) are also accepted by `render_badge()`.

---

## Coverage badge

`parse_coverage_xml()` reads a `coverage.xml` report and returns a percentage. `coverage_color()` maps it to the appropriate color.

```python
from badgeshield import parse_coverage_xml, coverage_color
from badgeshield import BadgeGenerator, BadgeTemplate

# Read coverage.xml produced by `coverage run`
pct = parse_coverage_xml("coverage.xml")           # e.g. 94.3
color = coverage_color(pct)                         # "#44cc11"

gen = BadgeGenerator(template=BadgeTemplate.DEFAULT)
gen.generate_badge(
    left_text="coverage",
    left_color="#555555",
    right_text=f"{pct:.0f}%",
    right_color=color,
    badge_name="coverage.svg",
    output_path="./badges",
)
```

Use `metric="branch"` to badge on branch coverage instead:

```python
pct = parse_coverage_xml("coverage.xml", metric="branch")
```

### Color thresholds

| Coverage | Hex | Appearance |
|----------|-----|------------|
| ≥ 90% | `#44cc11` | green |
| ≥ 80% | `#97ca00` | yellow-green |
| ≥ 70% | `#a4a61d` | yellow |
| ≥ 60% | `#dfb317` | orange |
| < 60%  | `#e05d44` | red |

---

## Embedding in HTML or GitLab Markdown

```html
<a href="https://example.com/build">
  <img alt="Build Status" src="./badges/build.svg" />
</a>
```

```markdown
[![Build Status](./badges/build.svg)](https://example.com/build)
```

!!! warning "GitLab SVG links"
    GitLab's Markdown renderer does not follow hyperlinks embedded inside SVG files when the SVG is linked directly. Wrap the `<img>` in an `<a>` tag in HTML, or use Markdown image syntax with a surrounding link.
