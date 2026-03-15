# badgeshield: Offline-First Safety & Visual Richness

**Date:** 2026-03-15
**Status:** Approved

---

## Problem Statement

badgeshield targets three audiences equally: CI/CD pipeline users, Python library consumers, and standalone CLI users. Two gaps prevent it from standing out against alternatives like shields.io and pybadges:

1. **Air-gapped environments are broken.** One or more runtime dependencies may make outbound network calls, and generated SVGs may embed external resource references.
2. **Visual output is dated.** The three existing templates produce flat, boxy badges with no path to gradients, rounded corners, shadows, or non-rectangular shapes.

---

## Goals

- Make badgeshield verifiably safe in environments with no outbound internet access.
- Ship named style presets and two new templates that improve visual output without breaking any existing API.
- Give CI pipelines a machine-readable way to verify generated SVGs contain no external resource references.

## Non-Goals

- CSS animations or `@keyframes`.
- Variable or downloadable web fonts.
- Multi-column (3+) templates.
- Zero-dependency stdlib-only core.
- Combining multiple `BadgeStyle` values on a single badge.

---

## Phase 1: Air-Gapped Safety

### 1.1 Dependency Network Audit

**Step 1 — Audit:** Run the full pytest suite with `socket.socket` monkeypatched to raise `OSError("Network blocked")`. Record every offending package.

**Step 2 — Fix by offender:**

- **If `pylogshield` is the offender:** Replace it unconditionally. Create `src/badgeshield/_logging.py`:

  ```python
  import logging
  from enum import Enum
  from typing import Union

  class LogLevel(str, Enum):
      DEBUG = "DEBUG"; INFO = "INFO"; WARNING = "WARNING"
      ERROR = "ERROR"; CRITICAL = "CRITICAL"

  def get_logger(name: str, log_level: Union[LogLevel, str]) -> logging.Logger:
      logger = logging.getLogger(name)
      level = log_level.value if isinstance(log_level, LogLevel) else log_level
      logger.setLevel(getattr(logging, level, logging.INFO))
      if not logger.handlers:
          logger.addHandler(logging.StreamHandler())
      return logger
  ```

  Must support `logger.info("msg", extra={"key": "val"})` — all existing call sites use `extra={}`. Remove `pylogshield` from `requirements.txt`. Update all `from pylogshield import ...` to `from ._logging import ...`. `LogLevel` stays exported from `__init__.py`.

- **If a different required dependency is the offender:** Identify the call site; if avoidable by changing how badgeshield calls it, do so. If not, escalate as a separate spec.

- **If Pillow is the offender:** Remove from `[image]` extras, document removal, rely on fallback. Separate spec for further action.

- **If nothing offends:** Keep `pylogshield`; add comment to `tests/conftest.py`: `# Network audit performed YYYY-MM-DD: no dependency makes outbound calls.`

**Acceptance:** Full test suite passes with all sockets blocked.

### 1.2 Bundled Font

Copy `DejaVuSans.ttf` into `src/badgeshield/fonts/`. Update `_get_font()` in `badge_generator.py`:

```python
import sys
from pathlib import Path

def _get_font(self):
    if ImageFont is None:
        return None
    if not hasattr(self, "_badge_font"):
        try:
            if sys.version_info >= (3, 9):
                from importlib.resources import files
                font_path = str(files("badgeshield") / "fonts" / "DejaVuSans.ttf")
            else:
                font_path = str(Path(__file__).parent / "fonts" / "DejaVuSans.ttf")
            self._badge_font = ImageFont.truetype(font_path, 110)
        except OSError:
            self._badge_font = ImageFont.load_default()
    return self._badge_font
```

No new dependency. Add to `pyproject.toml`:

```toml
[tool.setuptools.package-data]
badgeshield = ["fonts/*.ttf"]
```

**Acceptance:** `_get_font()` returns a non-`None`, non-default `ImageFont` on a fresh virtualenv with no system fonts, on Python 3.8 and 3.9+.

### 1.3 SVG Template Audit

Parametrized test using these exact fixture params (create `tests/fixtures/test_logo.png` — a 1×1 transparent PNG):

| Template | Parameters |
|----------|-----------|
| `DEFAULT` | `left_text="build"`, `left_color=BadgeColor.GREEN`, `right_text="passing"`, `right_color=BadgeColor.BLUE`, `logo="tests/fixtures/test_logo.png"`, `left_link="#left"`, `right_link="#right"`, `badge_name="test.svg"` |
| `CIRCLE` | `left_text="OK"`, `left_color=BadgeColor.GREEN`, `logo="tests/fixtures/test_logo.png"`, `left_link="#link"`, `badge_name="test.svg"` |
| `CIRCLE_FRAME` | `left_text="OK"`, `left_color=BadgeColor.GREEN`, `frame=FrameType.FRAME1`, `logo="tests/fixtures/test_logo.png"`, `badge_name="test.svg"` |

Links use fragment identifiers (`#...`) — not absolute URLs — so they do not trigger the assertion.

Assert the SVG string contains no substring matching `r'https?://'`. Protocol-relative `//` is not checked.

When `PILL` and `BANNER` templates are implemented in Phase 2, extend this parametrized test with:

| Template | Parameters |
|----------|-----------|
| `PILL` | `left_text="stable"`, `left_color=BadgeColor.GREEN`, `badge_name="test.svg"` |
| `BANNER` | `left_text="badgeshield"`, `left_color=BadgeColor.BLUE`, `right_text="v1.0"`, `badge_name="test.svg"` |

### 1.4 Offline Test Fixture

Add to `tests/conftest.py`:

```python
@pytest.fixture
def block_network(monkeypatch):
    import socket
    def blocked(*args, **kwargs):
        raise OSError("Network blocked by test fixture")
    monkeypatch.setattr(socket, "socket", blocked)
```

**Scope:** `function`. **Application:** opt-in — apply `@pytest.mark.usefixtures("block_network")` to:
- All badge generation test classes/functions in `tests/test_badge_generator.py`.
- Non-audit test classes/functions in `tests/test_generate_badge_cli.py`.

The audit tests in `tests/test_generate_badge_cli.py` must be placed in a clearly named class `TestAuditCommand`. Do **not** apply `block_network` to `TestAuditCommand` (audit uses only filesystem I/O).

### 1.5 `badgeshield audit` CLI Subcommand

New `@app.command()` in `generate_badge_cli.py`. Exit mechanism: `raise typer.Exit(N)` for all non-zero exits, consistent with the existing CLI pattern (`raise typer.Exit(1)` for errors). Normal completion (exit 0) returns implicitly.

```
badgeshield audit <svg_file>
badgeshield audit <svg_file> --json
```

**Detection algorithm:**

1. Attempt `ET.parse(svg_file)`. If `FileNotFoundError` → print Rich error panel, `raise typer.Exit(2)`. If `ET.ParseError` → same.
2. Check `tree.getroot().tag`. If it does not end with `}svg` and is not exactly `"svg"` → print Rich error panel, `raise typer.Exit(2)`.
3. Walk all elements via `root.iter()`. For each attribute `(name, value)`:
   - If `value` starts with `http://` or `https://` → append `(element.tag, name, value)` to violations list.
   - If `name == "style"`: apply `re.findall(r'url\(["\']?(https?://[^"\')\s]+)', value)` → each match appended as `(element.tag, "style[url]", match)`.
4. `data:` URIs and relative paths are not violations.

**Output (human-readable):** Rich table with columns `Element`, `Attribute`, `URL`.

**Output (`--json`):**
```json
{"clean": true, "violations": []}
{"clean": false, "violations": [{"element": "image", "attribute": "href", "url": "https://..."}]}
```

**Exit codes:** `0` = clean (implicit return), `raise typer.Exit(1)` = violations, `raise typer.Exit(2)` = file/parse/not-SVG error.

**Implementation:** stdlib only (`xml.etree.ElementTree`, `re`, `json`). No new dependencies.

---

## Phase 2: Visual Richness

### 2.1 `BadgeStyle` Enum

Add to `src/badgeshield/utils.py`:

```python
class BadgeStyle(str, Enum):
    FLAT      = "flat"
    ROUNDED   = "rounded"
    GRADIENT  = "gradient"
    SHADOWED  = "shadowed"
```

Also add `PILL` and `BANNER` to the existing `BadgeTemplate` enum in the same file. Their values are the Jinja2 template filenames used verbatim by `_get_template()` via `self.template_name = str(template)`:

```python
class BadgeTemplate(str, Enum):
    DEFAULT      = "templates/label.svg"       # existing
    CIRCLE       = "templates/circle.svg"      # existing
    CIRCLE_FRAME = "templates/circle_frame.svg" # existing
    PILL         = "templates/pill.svg"         # NEW
    BANNER       = "templates/banner.svg"       # NEW
```

Export from `__init__.py`; add to `__all__`. One active style per badge.

### 2.2 `_lighten_hex` Helper

Module-level private function in `badge_generator.py`. Uses `import colorsys` (stdlib, no new dependency):

```python
def _lighten_hex(hex_color: str, factor: float = 0.2) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16)/255, int(h[2:4], 16)/255, int(h[4:6], 16)/255
    hue, light, sat = colorsys.rgb_to_hls(r, g, b)  # colorsys uses HLS order
    light = min(1.0, light + factor * (1.0 - light))
    r2, g2, b2 = colorsys.hls_to_rgb(hue, light, sat)
    return "#{:02X}{:02X}{:02X}".format(round(r2*255), round(g2*255), round(b2*255))
```

`hex_color` is always a resolved hex string (`#RRGGBB`) — it is called after `validate_inputs` has converted `left_color` to a hex value via `validate_color`, so enum inputs are never passed to `_lighten_hex`.

**Known edge case (intended):** `_lighten_hex("#ffffff")` → `"#FFFFFF"` (no change; white stays white).

**Unit test expected values:**
- `_lighten_hex("#000000")` → `"#333333"`
- `_lighten_hex("#ffffff")` → `"#FFFFFF"`
- `_lighten_hex("#4c1d95")`: run once, commit the result as the canonical expected value for the test.

### 2.3 Style Context Variables

`_render_badge_content` (existing method) gains `style: BadgeStyle` as its **last** parameter. The dispatch call inside `_render_badge_content` appends `style` as the last positional argument to the renderer:

```python
return renderer(
    self,
    left_text, left_color, right_text, right_color, logo, frame,
    left_link, right_link, id_suffix, left_title, right_title, logo_tint,
    style,   # NEW — appended last
)
```

All `_render_*` methods (existing and new) gain `style: BadgeStyle` as their last parameter, matching this call order.

`generate_badge` calls `_render_badge_content(..., style=self.style)` — passing `self.style` (set in `__init__`) to the renderer.

Each `_render_*` method computes these variables from `style` and `id_suffix` (existing parameter, already present in all renderers):

| Variable | FLAT | ROUNDED | GRADIENT | SHADOWED |
|---|---|---|---|---|
| `rx` | `"3"` | `"8"` | `"3"` | `"3"` |
| `gradient_id` | `None` | `None` | `"grad" + id_suffix` | `None` |
| `gradient_stop` | `None` | `None` | `_lighten_hex(left_color_hex)` | `None` |
| `gradient_base` | `None` | `None` | `left_color_hex` | `None` |
| `shadow_id` | `None` | `None` | `None` | `"shadow" + id_suffix` |

Where `left_color_hex` is the resolved hex string (already computed by `validate_inputs` before `_render_badge_content` is called).

**GRADIENT scope:** Gradient applies to the left section fill only. `right_color` is used as-is. No gradient on the right section.

**Template `<defs>` blocks (conditional on non-None):**

```svg
{% if gradient_id %}
{# label/pill/banner: linear; circle/circle_frame: radial #}
<linearGradient id="{{ gradient_id }}" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0%" stop-color="{{ gradient_stop }}"/>
  <stop offset="100%" stop-color="{{ gradient_base }}"/>
</linearGradient>
{% endif %}

{# circle.svg and circle_frame.svg use radialGradient instead: #}
<radialGradient id="{{ gradient_id }}" cx="50%" cy="50%" r="50%">
  <stop offset="0%" stop-color="{{ gradient_stop }}"/>
  <stop offset="100%" stop-color="{{ gradient_base }}"/>
</radialGradient>

{% if shadow_id %}
<filter id="{{ shadow_id }}">
  <feDropShadow dx="1" dy="1" stdDeviation="1" flood-opacity="0.3"/>
</filter>
{% endif %}
```

**Fill/filter on main shapes:**
- `gradient_id` set → main left shape uses `fill="url(#{{ gradient_id }})"`.
- `shadow_id` set → main shape gains `filter="url(#{{ shadow_id }})"`.

**ROUNDED on circle/circle_frame:** `rx` is injected but those templates have no rect element; they ignore it silently.

### 2.4 `BadgeGenerator.__init__` Change

```python
from typing import Optional

def __init__(
    self,
    template: BadgeTemplate = BadgeTemplate.DEFAULT,
    log_level: Union[LogLevel, str] = LogLevel.WARNING,
    style: Optional["BadgeStyle"] = None,
) -> None:
    ...
    self.style = style if style is not None else BadgeStyle.FLAT
```

`self.style` is always a `BadgeStyle` instance after construction. `generate_badge` does **not** gain a `style` parameter — style is set at construction time via `__init__`.

### 2.5 Batch Integration

`BadgeBatchGenerator._generate_single_badge` already creates a fresh `BadgeGenerator(template=template, ...)` per badge. Add `style: BadgeStyle = BadgeStyle.FLAT` to `_generate_single_badge`'s parameter list and pass it to `BadgeGenerator.__init__`:

```python
def _generate_single_badge(self, ..., style: BadgeStyle = BadgeStyle.FLAT, ...) -> None:
    generator = BadgeGenerator(template=template, log_level=self.log_level, style=style)
    generator.generate_badge(...)
```

The batch CLI command injects the resolved `BadgeStyle` enum into each badge dict before calling `generate_batch`, so it is passed through as a kwarg to `_generate_single_badge`.

### 2.6 CLI Changes

**`single` subcommand:** Add:
```python
style: str = typer.Option("FLAT", help="FLAT | ROUNDED | GRADIENT | SHADOWED")
```
Validate via `BadgeStyle[style.upper()]` — on `KeyError`, print Rich error panel and `raise typer.Exit(1)`. Pass `style=style_enum` to `BadgeGenerator.__init__`.

**`batch` subcommand:** Add `--style` with same signature. Per-entry logic:
- If entry has a `"style"` key: parse `BadgeStyle[entry["style"].upper()]`. On `KeyError`, raise `ValueError(f"Invalid style '{entry['style']}'")` — propagates through `_generate_single_badge` into `BadgeBatchGenerator` error aggregation (existing pattern).
- If entry lacks `"style"`: inject the CLI `--style` enum value into the badge dict.

### 2.7 New Templates

#### `pill.svg` — `BadgeTemplate.PILL`

**Input:**
- `left_text` (required), `left_color` (required), `logo` (optional), `left_link` (optional), `left_title` (optional), `style` (applied).
- `rx` is **not injected** — pill template hardcodes `rx="10"` on its outer rect.
- `gradient_id`, `gradient_stop`, `gradient_base`, `shadow_id` injected normally.
- `right_text`, `right_color`, `right_link`, `right_title`, `frame`: silently ignored.

**Dimensions:**
```
text_padding = 10
logo_width = 14 if logo else 0
logo_padding = 3 if logo else 0
width = _calculate_text_width(left_text) + 2*text_padding + logo_width + logo_padding
height = 20
```

**Renderer:** `_render_pill`, registered as `_RENDERERS[BadgeTemplate.PILL]`.

---

#### `banner.svg` — `BadgeTemplate.BANNER`

**Input:**
- `left_text` (required, rendered bold at `font-size="13"`).
- `left_color` (required, full strip background).
- `right_text` (optional, text-only sub-label — no background rect; rendered on `left_color`).
- `right_color` (optional, text color of `right_text`; defaults to `"#ffffff"` when `right_text` is present and `right_color` is `None`).
- `logo` (optional, 28px icon zone).
- `left_link` (optional), `left_title` (optional), `style` (applied; `rx` used on outer background rect).
- `right_link`, `right_title`, `frame`: silently ignored.

**Logo SVG structure (when logo present):**
```svg
<defs>
  <clipPath id="clipBanner{{ id_suffix }}">
    <circle cx="14" cy="14" r="10"/>
  </clipPath>
</defs>
<image x="4" y="4" width="20" height="20"
       href="data:...base64..."
       clip-path="url(#clipBanner{{ id_suffix }})"
       preserveAspectRatio="xMidYMid slice"/>
```
`<image>` top-left at `(4,4)`; clipPath circle at `cx=14, cy=14, r=10` — same coordinate space, clips the image to a 20px-diameter circle centered within the 28px zone.

**Dimensions:**
```
text_padding = 10
icon_zone_width = 28 if logo else 0
left_text_width = _calculate_text_width(left_text)
right_text_width = _calculate_text_width(right_text) if right_text else 0
width = icon_zone_width + left_text_width + 2*text_padding + right_text_width + (text_padding if right_text else 0)
height = 28
```

**Renderer:** `_render_banner`, registered as `_RENDERERS[BadgeTemplate.BANNER]`.

---

## Data Flow

```
CLI / API call
    → BadgeGenerator(template, log_level, style=None)
        → self.style = style or BadgeStyle.FLAT
    → generate_badge(left_text, left_color, ...)
        → validate_inputs() → left_color_hex, right_color_hex, output_path, frame
        → _render_badge_content(..., style=self.style)
            → _render_<template>(..., style, id_suffix, left_color_hex, ...)
                → compute rx, gradient_id, gradient_stop, gradient_base, shadow_id
                → build Jinja2 context
                → template emits conditional <defs>; shapes use url(#...) refs
        → write SVG to disk

badgeshield audit <svg_file> [--json]
    → ET.parse() or FileNotFoundError → raise typer.Exit(2)
    → check root tag → raise typer.Exit(2) if not SVG
    → walk elements; collect http:// / https:// violations
    → raise typer.Exit(1) if violations; else return (exit 0)
```

---

## Testing

| Area | Approach |
|------|----------|
| Offline | `@pytest.mark.usefixtures("block_network")` opt-in on all generation tests; **not** on `TestAuditCommand` |
| SVG external refs | Parametrized as §1.3 (3 existing templates); extended in Phase 2 to include PILL and BANNER |
| Bundled font | Monkeypatch `ImageFont.truetype` to raise `OSError` for non-bundled paths; assert returned object is not `ImageFont.load_default()` |
| `audit` — clean | Generate badge, run via Typer `CliRunner`, assert exit 0 |
| `audit` — dirty | Write SVG with `href="https://cdn.example.com/img.png"`, assert exit 1 |
| `audit` — bad inputs | Non-existent file → exit 2; malformed XML → exit 2; `<foo>` root → exit 2 |
| `ROUNDED` | Assert label SVG contains `rx="8"` |
| `GRADIENT` label | Assert SVG contains `<linearGradient` |
| `GRADIENT` circle | Assert SVG contains `<radialGradient` |
| `SHADOWED` | Assert SVG contains `<feDropShadow` |
| `_lighten_hex` | `#000000`→`#333333`; `#ffffff`→`#FFFFFF`; `#4c1d95`→committed value |
| PILL snapshot | `tests/snapshots/pill_basic.svg` |
| BANNER snapshots | `tests/snapshots/banner_basic.svg`; `tests/snapshots/banner_with_sublabel.svg` |
| Backwards compat | All existing tests pass; `style` always optional |

**Snapshot strategy:**
- Files committed in `tests/snapshots/`.
- Regenerate: `UPDATE_SNAPSHOTS=1 pytest -k snapshot`.
- Absent file: test calls `pytest.fail(f"Snapshot missing: {path}. Run UPDATE_SNAPSHOTS=1 pytest to generate.")` — explicit failure, not `FileNotFoundError`.
- No third-party library.

---

## File Changelist

| File | Change |
|------|--------|
| `src/badgeshield/fonts/DejaVuSans.ttf` | New — bundled font |
| `src/badgeshield/_logging.py` | New — stdlib wrapper (conditional on audit result) |
| `src/badgeshield/utils.py` | Add `BadgeStyle` enum; add `PILL`, `BANNER` to `BadgeTemplate` |
| `src/badgeshield/badge_generator.py` | `_get_font()` bundled path; `style` on `__init__` (resolved in body); `_render_badge_content` + all `_render_*` gain `style`; `_render_pill`, `_render_banner`; `_RENDERERS` updated; `_lighten_hex()`; `import colorsys` |
| `src/badgeshield/generate_badge_cli.py` | `--style` on `single`/`batch`; per-entry style in `batch`; new `audit` subcommand |
| `src/badgeshield/__init__.py` | Export `BadgeStyle` |
| `src/badgeshield/templates/label.svg` | Conditional `<defs>` (linear gradient, shadow); `rx` variable |
| `src/badgeshield/templates/circle.svg` | Conditional `<defs>` (radial gradient, shadow) |
| `src/badgeshield/templates/circle_frame.svg` | Conditional `<defs>` (shadow) |
| `src/badgeshield/templates/pill.svg` | New — hardcoded `rx="10"` |
| `src/badgeshield/templates/banner.svg` | New — `clipBanner` clipPath; bold 13px primary text |
| `tests/conftest.py` | `block_network` fixture |
| `tests/fixtures/test_logo.png` | New — 1×1 transparent PNG |
| `tests/snapshots/` | New directory; baseline SVGs committed |
| `tests/test_badge_generator.py` | All Phase 1/2 generation tests |
| `tests/test_generate_badge_cli.py` | `TestAuditCommand` class; `--style` tests |
| `pyproject.toml` | `[tool.setuptools.package-data]` |
| `requirements.txt` | Remove `pylogshield` if replaced |
