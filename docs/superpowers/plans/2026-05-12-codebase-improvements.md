# Codebase Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix six correctness bugs, one performance regression, and one code-duplication issue across `badge_generator.py` and `generate_badge_cli.py`, with new tests for every change.

**Architecture:** All changes are backwards-compatible. `badge_generator.py` gets corrected fallback colours, a class-level font cache, an updated `validate_frame` type annotation, a fixed `_generate_single_badge` parameter type, and `generate_badge` now returns the written path. `generate_badge_cli.py` gets a shared `_validate_format` helper that replaces four identical inline validation blocks.

**Tech Stack:** Python 3.8+, pytest, Jinja2, Typer, Pillow (optional)

---

## File Map

| File | Change |
|---|---|
| `src/badgeshield/badge_generator.py` | Fix PILL/BANNER fallback colour · promote font to class cache · fix `validate_frame` annotation · fix `_generate_single_badge` template type · `generate_badge` returns `str` |
| `src/badgeshield/generate_badge_cli.py` | Add `_validate_format()` helper · replace four inline validation blocks |
| `tests/test_badge_generator.py` | New tests for fallback colour, return value, font cache; update `test_get_font_uses_bundled_font` |
| `tests/test_generate_badge_cli.py` | New test for `_validate_format` via CLI |

---

## Task 1 — Fix PILL/BANNER hardcoded fallback right_color

**Files:**
- Modify: `src/badgeshield/badge_generator.py` (lines ~837, ~880)
- Test: `tests/test_badge_generator.py`

### Background
`_render_pill` defaults `right_color` to `"#44cc11"` (hardcoded green) and `_render_banner` defaults to `"#555555"` (hardcoded gray) when none is supplied. All other renderers fall back to `left_color`. This means omitting `right_color` gives inconsistent results depending on template.

- [ ] **Step 1: Write the two failing tests**

Add to `tests/test_badge_generator.py`:

```python
def test_pill_right_color_falls_back_to_left_color(tmp_path):
    """When right_color is omitted, PILL must fall back to left_color, not hardcoded green."""
    gen = BadgeGenerator(template=BadgeTemplate.PILL)
    gen.generate_badge(
        left_text="build",
        left_color="#abcdef",
        right_text="passing",
        badge_name="pill.svg",
        output_path=str(tmp_path),
    )
    assert gen._last_render_context["right_color"] == "#abcdef"


def test_banner_right_color_falls_back_to_left_color(tmp_path):
    """When right_color is omitted, BANNER must fall back to left_color, not hardcoded gray."""
    gen = BadgeGenerator(template=BadgeTemplate.BANNER)
    gen.generate_badge(
        left_text="badgeshield",
        left_color="#1a1a2e",
        right_text="v1.0",
        badge_name="banner.svg",
        output_path=str(tmp_path),
    )
    assert gen._last_render_context["right_color"] == "#1a1a2e"
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_badge_generator.py::test_pill_right_color_falls_back_to_left_color tests/test_badge_generator.py::test_banner_right_color_falls_back_to_left_color -v
```

Expected: both FAIL — context shows hardcoded colours, not `left_color`.

- [ ] **Step 3: Fix `_render_pill` in `badge_generator.py`**

Find the line:
```python
"right_color": right_color or "#44cc11",
```

Replace with:
```python
"right_color": right_color or left_color,
```

- [ ] **Step 4: Fix `_render_banner` in `badge_generator.py`**

Find the line:
```python
"right_color": right_color or "#555555",
```

Replace with:
```python
"right_color": right_color or left_color,
```

- [ ] **Step 5: Run the two new tests**

```
pytest tests/test_badge_generator.py::test_pill_right_color_falls_back_to_left_color tests/test_badge_generator.py::test_banner_right_color_falls_back_to_left_color -v
```

Expected: both PASS.

- [ ] **Step 6: Run the full suite to check for regressions**

```
pytest tests/ -q
```

Expected: 155 passed (153 existing + 2 new).

- [ ] **Step 7: Commit**

```bash
git add src/badgeshield/badge_generator.py tests/test_badge_generator.py
git commit -m "fix: PILL and BANNER right_color falls back to left_color, not hardcoded value"
```

---

## Task 2 — `generate_badge` returns the output path

**Files:**
- Modify: `src/badgeshield/badge_generator.py` (`generate_badge` method)
- Test: `tests/test_badge_generator.py`

### Background
`generate_badge` writes the SVG to disk and returns `None`. Callers that need the path must reconstruct it manually. Returning the path is a non-breaking addition (callers that ignore the return value are unaffected).

- [ ] **Step 1: Write the failing test**

Add to `tests/test_badge_generator.py`:

```python
def test_generate_badge_returns_output_path(output_dir):
    """generate_badge must return the full path of the written SVG file."""
    gen = BadgeGenerator()
    result = gen.generate_badge(
        left_text="build",
        left_color="#44cc11",
        badge_name="ret.svg",
        output_path=str(output_dir),
    )
    assert isinstance(result, str)
    assert result == str(output_dir / "ret.svg")
    assert Path(result).exists()
```

- [ ] **Step 2: Run test to confirm it fails**

```
pytest tests/test_badge_generator.py::test_generate_badge_returns_output_path -v
```

Expected: FAIL — `result` is `None`, so `isinstance(None, str)` is False.

- [ ] **Step 3: Update `generate_badge` signature and body**

In `badge_generator.py`, change the method signature from:
```python
def generate_badge(
    self,
    ...
) -> None:
```
to:
```python
def generate_badge(
    self,
    ...
) -> str:
```

At the end of the `try` block, change:
```python
            with open(full_path, "w", encoding="utf-8") as file:
                file.write(badge_content)
            self.logger.info(f"Badge generated and saved to {full_path}")
```
to:
```python
            with open(full_path, "w", encoding="utf-8") as file:
                file.write(badge_content)
            self.logger.info(f"Badge generated and saved to {full_path}")
            return full_path
```

- [ ] **Step 4: Run the new test**

```
pytest tests/test_badge_generator.py::test_generate_badge_returns_output_path -v
```

Expected: PASS.

- [ ] **Step 5: Run the full suite**

```
pytest tests/ -q
```

Expected: 156 passed.

- [ ] **Step 6: Commit**

```bash
git add src/badgeshield/badge_generator.py tests/test_badge_generator.py
git commit -m "feat: generate_badge returns the full output path instead of None"
```

---

## Task 3 — Class-level font cache (performance)

**Files:**
- Modify: `src/badgeshield/badge_generator.py` (`_get_font`, class body)
- Test: `tests/test_badge_generator.py` (new test + update `test_get_font_uses_bundled_font`)

### Background
`_badge_font` is stored on the instance via `hasattr(self, "_badge_font")`. `BadgeBatchGenerator` creates a fresh `BadgeGenerator` per badge, so a batch of N badges loads the font N times. Promoting the cache to class level (guarded by the existing `_cache_lock`) means the font is loaded once for the process lifetime.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_badge_generator.py`:

```python
def test_font_cache_is_shared_across_instances():
    """_get_font must return the same font object from two different BadgeGenerator instances."""
    from badgeshield.badge_generator import BadgeGenerator, ImageFont

    if ImageFont is None:
        pytest.skip("Pillow not installed")

    gen1 = BadgeGenerator()
    gen2 = BadgeGenerator()
    font1 = gen1._get_font()
    font2 = gen2._get_font()
    assert font1 is font2, "Font was loaded twice — class-level cache is not working"
```

- [ ] **Step 2: Run test to confirm it fails**

```
pytest tests/test_badge_generator.py::test_font_cache_is_shared_across_instances -v
```

Expected: FAIL — two separate instances load two separate font objects, so `font1 is font2` is False.

- [ ] **Step 3: Add class-level cache attributes**

In `badge_generator.py`, inside the `BadgeGenerator` class body (alongside the other `ClassVar` declarations near the top of the class), add:

```python
_badge_font: ClassVar[Optional["ImageFont.ImageFont"]] = None
_font_loaded: ClassVar[bool] = False
```

The `Optional` import is already present. `ClassVar` is already imported from `typing`.

- [ ] **Step 4: Replace `_get_font` with a classmethod**

Remove the existing `_get_font` method entirely and replace with:

```python
@classmethod
def _get_font(cls) -> Optional["ImageFont.ImageFont"]:
    """Return the bundled DejaVuSans font, loading it once at class level."""
    if ImageFont is None:
        return None
    with cls._cache_lock:
        if not cls._font_loaded:
            try:
                import sys
                from pathlib import Path as _Path

                if sys.version_info >= (3, 9):  # type: ignore[assignment]
                    from importlib.resources import files  # type: ignore[assignment]

                    font_path = str(files("badgeshield") / "fonts" / "DejaVuSans.ttf")
                else:
                    font_path = str(_Path(__file__).parent / "fonts" / "DejaVuSans.ttf")
                cls._badge_font = ImageFont.truetype(font_path, 110)
            except OSError:
                cls._badge_font = ImageFont.load_default()  # type: ignore[assignment]
            cls._font_loaded = True
    return cls._badge_font  # type: ignore[return-value]
```

- [ ] **Step 5: Update `test_get_font_uses_bundled_font` to use monkeypatch on class attrs**

The existing test clears the font with `del gen._badge_font` — that worked for instance attributes but won't work now. Replace the "Clear cached font" block inside `test_get_font_uses_bundled_font`:

Old block:
```python
    gen = BadgeGenerator()
    # Clear cached font to force a fresh load
    if hasattr(gen, "_badge_font"):
        del gen._badge_font
```

New block:
```python
    # Reset class-level cache so _get_font performs a fresh load under the patched truetype
    monkeypatch.setattr(BadgeGenerator, "_badge_font", None)
    monkeypatch.setattr(BadgeGenerator, "_font_loaded", False)

    gen = BadgeGenerator()
```

- [ ] **Step 6: Run the font-related tests**

```
pytest tests/test_badge_generator.py::test_font_cache_is_shared_across_instances tests/test_badge_generator.py::test_get_font_uses_bundled_font -v
```

Expected: both PASS.

- [ ] **Step 7: Run the full suite**

```
pytest tests/ -q
```

Expected: 157 passed.

- [ ] **Step 8: Commit**

```bash
git add src/badgeshield/badge_generator.py tests/test_badge_generator.py
git commit -m "perf: promote font to class-level cache so batch mode loads font once"
```

---

## Task 4 — Fix type annotations: `validate_frame` and `_generate_single_badge`

**Files:**
- Modify: `src/badgeshield/badge_generator.py` (two signatures only)

### Background
`validate_frame` is declared as `frame: Union[FrameType, str]` but its first line handles `frame is None` and raises `ValueError`. The `None` case is real (it's how the CIRCLE_FRAME-missing-frame error is surfaced) so the annotation should be `Optional[Union[FrameType, str]]`.

`_generate_single_badge` declares `template: Optional[BadgeTemplate] = BadgeTemplate.DEFAULT`. `Optional` implies `None` is valid, but passing `None` would crash the `BadgeGenerator` constructor. The correct type is `BadgeTemplate = BadgeTemplate.DEFAULT`.

These are annotation-only changes — no runtime behaviour changes — so no new tests are needed. The existing tests cover the runtime behaviour.

- [ ] **Step 1: Fix `validate_frame` annotation**

Find:
```python
    @staticmethod
    def validate_frame(frame: Union[FrameType, str]) -> str:
```

Replace with:
```python
    @staticmethod
    def validate_frame(frame: Optional[Union[FrameType, str]]) -> str:
```

- [ ] **Step 2: Fix `_generate_single_badge` template annotation**

Find:
```python
        template: Optional[BadgeTemplate] = BadgeTemplate.DEFAULT,
```

Replace with:
```python
        template: BadgeTemplate = BadgeTemplate.DEFAULT,
```

- [ ] **Step 3: Run mypy**

```
mypy src/ --ignore-missing-imports
```

Expected: no new errors introduced.

- [ ] **Step 4: Run the full suite**

```
pytest tests/ -q
```

Expected: 157 passed (count unchanged — annotation-only changes).

- [ ] **Step 5: Commit**

```bash
git add src/badgeshield/badge_generator.py
git commit -m "fix: correct Optional type annotations on validate_frame and _generate_single_badge"
```

---

## Task 5 — Extract `_validate_format` helper in CLI

**Files:**
- Modify: `src/badgeshield/generate_badge_cli.py`
- Test: `tests/test_generate_badge_cli.py`

### Background
The block:
```python
if format:
    fmt_lower = format.lower()
    if fmt_lower not in ("markdown", "rst", "html"):
        _error(f"Invalid format '{format}'. Choose from: markdown, rst, html")
        raise typer.Exit(1)
```
is copy-pasted with minor variations in `single`, `batch`, `coverage`, and `preset_cmd`. A shared helper removes the duplication and gives a single place to update if formats change.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_generate_badge_cli.py` (inside `TestCLICommands` or at module level):

```python
def test_single_invalid_format_exits_1(tmp_path):
    """An unrecognised --format value on 'single' must exit 1 with an error."""
    from typer.testing import CliRunner
    from badgeshield.generate_badge_cli import app

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "single",
            "--left-text", "build",
            "--left-color", "GREEN",
            "--badge-name", "b.svg",
            "--output-path", str(tmp_path),
            "--format", "pdf",
        ],
    )
    assert result.exit_code == 1
    assert "Error" in result.output
```

- [ ] **Step 2: Run test to confirm it fails**

```
pytest tests/test_generate_badge_cli.py::test_single_invalid_format_exits_1 -v
```

Expected: FAIL — the current code raises an unhandled `ValueError` from `_format_snippet`, which surfaces as a traceback rather than exit code 1 with an Error panel. (The inline guard only fires if `fmt_lower not in (...)`, but `_format_snippet` also raises for unknown formats — the guard is redundant but the current order exposes a path where `_error` is never printed.)

- [ ] **Step 3: Add `_validate_format` helper**

In `generate_badge_cli.py`, right after the existing `_format_snippet` function (around line 48), add:

```python
def _validate_format(fmt: Optional[str]) -> Optional[str]:
    """Normalise and validate a --format value. Returns the lower-case string or None.

    Calls _error() and raises typer.Exit(1) on unrecognised input.
    """
    if fmt is None:
        return None
    fmt_lower = fmt.lower()
    if fmt_lower not in ("markdown", "rst", "html"):
        _error(f"Invalid format '{fmt}'. Choose from: markdown, rst, html")
        raise typer.Exit(1)
    return fmt_lower
```

- [ ] **Step 4: Replace the four inline validation blocks**

**In `single`** — find:
```python
    if format:
        fmt_lower = format.lower()
        if fmt_lower not in ("markdown", "rst", "html"):
            _error(f"Invalid format '{format}'. Choose from: markdown, rst, html")
            raise typer.Exit(1)
        svg_path = str(Path(output_path or ".") / badge_name)
        typer.echo(_format_snippet(svg_path, left_text, fmt_lower))
```
Replace with:
```python
    fmt = _validate_format(format)
    if fmt:
        svg_path = str(Path(output_path or ".") / badge_name)
        typer.echo(_format_snippet(svg_path, left_text, fmt))
```

**In `batch`** — find:
```python
    if format:
        fmt_lower = format.lower()
        if fmt_lower not in ("markdown", "rst", "html"):
            _error(f"Invalid format '{format}'. Choose from: markdown, rst, html")
            raise typer.Exit(1)
        for badge in badge_configs:
            if badge["badge_name"] not in failure_map:
                svg_path = str(Path(output_path or ".") / badge["badge_name"])
                typer.echo(
                    _format_snippet(
                        svg_path, badge.get("left_text", badge["badge_name"]), fmt_lower
                    )
                )
```
Replace with:
```python
    fmt = _validate_format(format)
    if fmt:
        for badge in badge_configs:
            if badge["badge_name"] not in failure_map:
                svg_path = str(Path(output_path or ".") / badge["badge_name"])
                typer.echo(
                    _format_snippet(
                        svg_path, badge.get("left_text", badge["badge_name"]), fmt
                    )
                )
```

**In `coverage`** — find:
```python
    if format:
        fmt_lower = format.lower()
        if fmt_lower not in ("markdown", "rst", "html"):
            _error(f"Invalid format '{format}'. Choose from: markdown, rst, html")
            raise typer.Exit(1)
        svg_path = str(Path(output_path or ".") / badge_name)
        typer.echo(_format_snippet(svg_path, left_text, fmt_lower))
```
Replace with:
```python
    fmt = _validate_format(format)
    if fmt:
        svg_path = str(Path(output_path or ".") / badge_name)
        typer.echo(_format_snippet(svg_path, left_text, fmt))
```

**In `_run_all_presets`** — find:
```python
    if format:
        fmt_lower = format.lower()
        if fmt_lower not in ("markdown", "rst", "html"):
            _error(f"Invalid format '{format}'.")
            raise typer.Exit(1)
        for _, out_name, alt_text in written:
            svg_path = str(Path(output_path or ".") / out_name)
            typer.echo(_format_snippet(svg_path, alt_text, fmt_lower))
```
Replace with:
```python
    fmt = _validate_format(format)
    if fmt:
        for _, out_name, alt_text in written:
            svg_path = str(Path(output_path or ".") / out_name)
            typer.echo(_format_snippet(svg_path, alt_text, fmt))
```

**In `preset_cmd`** — find:
```python
    if format:
        fmt_lower = format.lower()
        if fmt_lower not in ("markdown", "rst", "html"):
            _error(f"Invalid format '{format}'. Choose from: markdown, rst, html")
            raise typer.Exit(1)
        svg_path = str(Path(output_path or ".") / out_name)
        typer.echo(_format_snippet(svg_path, p.label, fmt_lower))
```
Replace with:
```python
    fmt = _validate_format(format)
    if fmt:
        svg_path = str(Path(output_path or ".") / out_name)
        typer.echo(_format_snippet(svg_path, p.label, fmt))
```

- [ ] **Step 5: Run the new test**

```
pytest tests/test_generate_badge_cli.py::test_single_invalid_format_exits_1 -v
```

Expected: PASS.

- [ ] **Step 6: Run the full suite**

```
pytest tests/ -q
```

Expected: 158 passed.

- [ ] **Step 7: Commit**

```bash
git add src/badgeshield/generate_badge_cli.py tests/test_generate_badge_cli.py
git commit -m "refactor: extract _validate_format helper, remove 4x duplicated format validation"
```

---

## Self-Review

**Spec coverage:**
- PILL/BANNER hardcoded fallback colour → Task 1 ✓
- `generate_badge` returns path → Task 2 ✓
- Font class-level cache → Task 3 ✓
- `validate_frame` annotation fix → Task 4 ✓
- `_generate_single_badge` template annotation fix → Task 4 ✓
- `_validate_format` extraction → Task 5 ✓

**Placeholder scan:** No TBDs, no "similar to Task N", all code blocks complete.

**Type consistency:**
- `_badge_font: ClassVar[Optional[...]]` declared in Task 3 class body, used in `_get_font` classmethod in same task. ✓
- `_font_loaded: ClassVar[bool]` declared and used in same task. ✓
- `_validate_format` declared in Task 5 Step 3, called in Step 4. ✓
- `generate_badge` return type `str` declared and returned in Task 2. ✓
- `monkeypatch.setattr(BadgeGenerator, "_badge_font", None)` matches the attribute name declared in Task 3. ✓

**Test update not to miss:** `test_get_font_uses_bundled_font` currently clears the font via `del gen._badge_font`. That must be updated in Task 3 Step 5 or the test will no longer reset state correctly. Covered. ✓
