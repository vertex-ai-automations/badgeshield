# badgeshield: Offline-First Safety & Visual Richness

**Date:** 2026-03-15
**Status:** Approved

---

## Problem Statement

badgeshield targets three audiences equally: CI/CD pipeline users, Python library consumers, and standalone CLI users. Two gaps prevent it from standing out against alternatives like shields.io and pybadges:

1. **Air-gapped environments are broken.** One or more runtime dependencies make outbound network calls, and generated SVGs may embed external resource references. Enterprises, government agencies, and offline build environments cannot rely on the package today.
2. **Visual output is dated.** The three existing templates produce flat, boxy badges. There is no path to gradients, rounded corners, shadows, or non-rectangular shapes without forking templates manually.

---

## Goals

- Make badgeshield verifiably safe to use in environments with no outbound internet access.
- Ship named style presets and two new templates that noticeably improve visual output without breaking any existing API.
- Give CI pipelines a machine-readable way to verify that any generated SVG contains no external resource references.

## Non-Goals

- CSS animations or `@keyframes` (CDN-risk and accessibility concerns).
- Variable or downloadable web fonts.
- Multi-column (3+) templates.
- Zero-dependency stdlib-only core (premature; solve the specific network-call problems first).

---

## Phase 1: Air-Gapped Safety

### 1.1 Dependency Network Audit

Instrument `pylogshield`, `jinja2`, and `Pillow` under a network-blocked test environment (socket patched to raise `OSError`). Identify any outbound call site. If `pylogshield` makes network calls, replace it with a thin stdlib `logging` wrapper that preserves the existing `get_logger(name, log_level)` and `LogLevel` interface so no public API breaks. Jinja2 and Pillow are expected to be clean.

**Acceptance:** `pytest` badge generation suite passes with all sockets blocked.

### 1.2 Bundled Font

**Current state:** `_get_font()` calls `ImageFont.truetype("DejaVuSans.ttf", 110)`, relying on the font being present on the system font path. Falls back silently to a bitmap font when it isn't.

**Change:** Copy `DejaVuSans.ttf` into `src/badgeshield/fonts/`. Update `_get_font()` to resolve the path using `importlib.resources.files("badgeshield") / "fonts" / "DejaVuSans.ttf"` (Python ≥ 3.9) with a `Path(__file__).parent / "fonts" / "DejaVuSans.ttf"` fallback for Python 3.8. Declare the font in `MANIFEST.in` and `package_data` so it is included in the wheel.

**Acceptance:** Text width measurement uses real font metrics on a fresh virtualenv with no system fonts installed.

### 1.3 SVG Template Audit

Scan `label.svg`, `circle.svg`, and `circle_frame.svg` for any `href`, `xlink:href`, `src`, `@import`, or CSS `url()` values that point to an external URL. Current templates are expected to be clean (all image data is base64-inlined), but this must be verified and locked in via a test.

**Acceptance:** A test asserts that no generated SVG contains a URL beginning with `http://` or `https://`.

### 1.4 Offline Test Fixture

Add a `pytest` fixture `block_network` (scope `function`) in `tests/conftest.py` that patches `socket.socket` to raise `OSError("Network blocked by test fixture")`. Apply it to all badge generation tests. Any future dependency that phones home will fail CI automatically.

```python
@pytest.fixture
def block_network(monkeypatch):
    import socket
    def blocked(*a, **kw):
        raise OSError("Network blocked by test fixture")
    monkeypatch.setattr(socket, "socket", blocked)
```

### 1.5 `badgeshield audit` CLI Subcommand

A new Typer subcommand that parses an SVG file and reports every external URL found in element attributes and inline CSS.

```
badgeshield audit badge.svg
badgeshield audit badge.svg --json
```

**Detection scope:**
- XML attributes: `href`, `xlink:href`, `src`, `data`, `action`
- CSS `url(...)` values in `style` attributes and `<style>` blocks
- Any value starting with `http://`, `https://`, or `//`

**Output:**
- Human-readable: prints a Rich table of violations (element tag, attribute, URL)
- `--json`: prints `{"clean": bool, "violations": [{"element": ..., "attribute": ..., "url": ...}]}`

**Exit codes:** `0` = clean, `1` = violations found, `2` = file not found or not valid SVG.

**Implementation:** Pure stdlib (`xml.etree.ElementTree` + `re`). No new dependencies.

---

## Phase 2: Visual Richness

### 2.1 `BadgeStyle` Enum

Add to `src/badgeshield/utils.py`:

```python
class BadgeStyle(str, Enum):
    FLAT      = "flat"       # current default — no change
    ROUNDED   = "rounded"    # 8px border-radius on all corners
    GRADIENT  = "gradient"   # linear gradient: base color → 20% lighter
    SHADOWED  = "shadowed"   # drop-shadow SVG filter
```

Exported from `src/badgeshield/__init__.py` as part of the public API.

### 2.2 Style Application in Templates

Each existing template (`label.svg`, `circle.svg`, `circle_frame.svg`) gains conditional Jinja2 blocks driven by a `style` context variable (string value of `BadgeStyle`):

- **`ROUNDED`**: `rx="8"` on the outer `<rect>` (label) or increased `r` padding (circle).
- **`GRADIENT`**: A `<linearGradient>` in `<defs>` is emitted; the fill attribute references it. The lighter stop color is pre-computed in Python (`_lighten_hex(color, factor=0.2)`) before template rendering — no runtime JS.
- **`SHADOWED`**: A `<filter id="shadow">` with `<feDropShadow dx="1" dy="1" stdDeviation="1" flood-opacity="0.3"/>` is emitted in `<defs>` and applied via `filter="url(#shadow)"`.

Styles are composable only via named presets (no arbitrary CSS injection) to keep the SVG output safe and auditable.

### 2.3 `BadgeGenerator` and CLI Changes

`BadgeGenerator.__init__` gains `style: BadgeStyle = BadgeStyle.FLAT`. The `style` value is passed through `_render_badge_content` into all `_render_*` methods and injected into the Jinja2 context. The `single` CLI command gains `--style` option (`FLAT | ROUNDED | GRADIENT | SHADOWED`, default `FLAT`). No changes to `generate_badge` signature beyond the new optional `style` parameter.

### 2.4 New Templates

#### `pill.svg` — `BadgeTemplate.PILL`

A single fully-rounded capsule (border-radius = height / 2). Single text field (`left_text`) and optional logo. No left/right split — background is a single color (`left_color`). Width is dynamic (same text-width calculation as `label.svg`). Suited for simple status labels like `stable`, `wip`, `deprecated`.

**Renderer:** `_render_pill` registered in `_RENDERERS` following the exact existing pattern.

#### `banner.svg` — `BadgeTemplate.BANNER`

A wide horizontal strip with three zones:
- **Left icon zone** (fixed 28px wide): optional logo, clipped to a circle.
- **Primary text** (`left_text`): bold, larger font-size (13px vs 11px).
- **Right sub-label** (`right_text`, optional): lighter weight, right-aligned.

Total height: 28px (vs 20px for label). Background uses `left_color` for the full strip; `right_color` is applied only as text color for the sub-label (not a separate rect), keeping the visual clean.

**Renderer:** `_render_banner` registered in `_RENDERERS`.

---

## Data Flow

```
CLI / API call
    → BadgeGenerator(template, style)
    → validate_inputs() — color, path, badge_name
    → _render_badge_content()
        → _render_<template>(…, style=style)
            → Jinja2 context includes style string
            → template emits conditional <defs> blocks
    → write SVG to disk

badgeshield audit <file>
    → parse SVG with ElementTree
    → walk all elements + attributes + style values
    → collect external URL violations
    → print table or JSON, exit 0/1/2
```

---

## Testing

| Area | Test approach |
|------|--------------|
| Offline network safety | `block_network` fixture applied to all generation tests |
| No external SVG refs | Assert generated SVGs contain no `http`/`https` URLs |
| Bundled font load | Assert `_get_font()` returns non-None on clean virtualenv |
| `audit` subcommand | Unit tests with clean SVGs (exit 0) and injected-URL SVGs (exit 1) |
| `BadgeStyle` presets | Assert rendered SVG contains expected elements (`linearGradient`, `feDropShadow`, `rx="8"`) |
| New templates | Snapshot tests for `pill.svg` and `banner.svg` output |
| Backwards compatibility | All existing tests continue to pass unmodified |

---

## File Changelist

| File | Change |
|------|--------|
| `src/badgeshield/fonts/DejaVuSans.ttf` | New — bundled font |
| `src/badgeshield/utils.py` | Add `BadgeStyle` enum; add `PILL`, `BANNER` to `BadgeTemplate` |
| `src/badgeshield/badge_generator.py` | `_get_font()` uses bundled font; `style` param threaded through; `_render_pill`, `_render_banner` added; `_RENDERERS` updated; `_lighten_hex()` helper added |
| `src/badgeshield/generate_badge_cli.py` | `single` gains `--style`; new `audit` subcommand |
| `src/badgeshield/__init__.py` | Export `BadgeStyle` |
| `src/badgeshield/templates/label.svg` | Conditional style blocks |
| `src/badgeshield/templates/circle.svg` | Conditional style blocks |
| `src/badgeshield/templates/circle_frame.svg` | Conditional style blocks |
| `src/badgeshield/templates/pill.svg` | New template |
| `src/badgeshield/templates/banner.svg` | New template |
| `tests/conftest.py` | `block_network` fixture |
| `tests/test_badge_generator.py` | Offline + style + template tests |
| `tests/test_generate_badge_cli.py` | `audit` subcommand tests |
| `MANIFEST.in` | Include `src/badgeshield/fonts/` |
| `pyproject.toml` | `package_data` for fonts directory |
