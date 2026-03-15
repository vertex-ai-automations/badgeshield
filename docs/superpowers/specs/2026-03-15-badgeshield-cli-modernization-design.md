# badgeshield — CLI Modernization & Code Remediation Design

**Date:** 2026-03-15
**Scope:** Full remediation of critical/high/medium bugs + CLI rewrite with Typer + Rich

---

## 1. Critical & High Bug Fixes

### 1.1 Test Import Rename
**Files:** `tests/test_badge_generator.py`, `tests/test_generate_badge_cli.py`

Replace all occurrences of `from custom_badges.*` and `import custom_badges` with `from badgeshield.*` / `import badgeshield`. This includes:
- Top-level imports in both test files
- Any in-function imports (e.g. `from custom_badges import badge_generator as badge_module` inside a test body)

### 1.2 CLI Imports Fix
**File:** `src/badgeshield/generate_badge_cli.py`

The current file imports `BadgeTemplate`, `FrameType`, and `LogLevel` from `.badge_generator`. The correct sources are:
- `BadgeTemplate`, `FrameType` → `from .utils import ...`
- `LogLevel` → `from pylogshield import LogLevel`

Note: `LogLevel` is not broken today because `badge_generator.py` re-exports it via `from pylogshield import LogLevel`. The fix is for correctness and to eliminate reliance on an undocumented re-export. `__init__.py` also re-exports `LogLevel` via `.badge_generator` — no change is needed there since its chain remains valid.

### 1.3 Path Traversal Protection
**File:** `src/badgeshield/badge_generator.py` → `validate_inputs()`

Insert this check immediately after the `.svg` suffix validation, before writing the output path:

```python
badge_path = Path(badge_name)
if any(part in ("..", ".") for part in badge_path.parts[:-1]):
    raise ValueError(f"badge_name '{badge_name}' must not contain directory traversal.")
if badge_path.is_absolute():
    raise ValueError(f"badge_name '{badge_name}' must be a plain filename, not an absolute path.")
```

This uses `Path.parts` for component-level checking — rejecting `../escape.svg` and `/etc/passwd.svg` but accepting `my-badge.svg` and `build_2024.svg`.

### 1.4 Pillow Optional Dependency Declaration
**File:** `pyproject.toml`

`pyproject.toml` uses dynamic dependencies sourced from `requirements.txt`. Pillow is not in `requirements.txt` today (it was always an undeclared optional). Add only the optional extras table:

```toml
[project.optional-dependencies]
image = ["Pillow>=9.0"]
```

`typer` and `rich` are mandatory CLI dependencies — they go in `requirements.txt` (Section 2.1), not in optional extras. This is a declaration fix for Pillow only; no behaviour changes.

---

## 2. CLI Modernization — Typer + Rich

### 2.1 New Dependencies
**File:** `requirements.txt` — append:
```
typer>=0.12
rich>=13.0
```

These are mandatory runtime dependencies (the CLI entry point requires them). They are added to `requirements.txt` so `pyproject.toml`'s dynamic dependency loading picks them up automatically.

### 2.2 Architecture
`generate_badge_cli.py` is rewritten as a Typer application. The two existing validation functions (`validate_single_badge_args`, `validate_batch_badge_args`) are **deleted** — their responsibilities move to:
- Typer's type system for required/optional flags
- `BadgeGenerator.validate_color`, `validate_frame`, and `validate_inputs` for business validation

The CLI becomes a thin orchestration layer. All business logic stays in the core library.

**Versioning note:** The underscore-to-hyphen flag rename (Section 2.3) is a breaking change requiring a `2.0.0` git tag (since `setuptools_scm` derives version from tags — do not edit `_version.py` manually). Include a CHANGELOG entry listing every renamed flag before the release tag is created.

### 2.3 Argument Naming
Python parameter names use underscores (`left_text`). Typer converts them to `--left-text` automatically (POSIX convention). Old flags (`--left_text`) no longer work.

### 2.4 `single` Command

```python
@app.command()
def single(
    left_text: str           = typer.Option(..., help="Text for the left section"),
    left_color: str          = typer.Option(..., help="Hex (#RRGGBB) or BadgeColor name e.g. GREEN"),
    badge_name: str          = typer.Option(..., help="Output filename, must end with .svg"),
    template: str            = typer.Option("DEFAULT", help="DEFAULT | CIRCLE | CIRCLE_FRAME"),
    output_path: Optional[str] = typer.Option(None, help="Output directory; defaults to cwd"),
    right_text: Optional[str]  = typer.Option(None),
    right_color: Optional[str] = typer.Option(None),
    logo: Optional[str]        = typer.Option(None),
    logo_tint: Optional[str]   = typer.Option(None),
    frame: Optional[str]       = typer.Option(None, help="Required for CIRCLE_FRAME template"),
    left_link: Optional[str]   = typer.Option(None),
    right_link: Optional[str]  = typer.Option(None),
    id_suffix: str             = typer.Option(""),
    left_title: Optional[str]  = typer.Option(None),
    right_title: Optional[str] = typer.Option(None),
    log_level: str             = typer.Option("INFO", help="DEBUG|INFO|WARNING|ERROR|CRITICAL"),
) -> None:
    try:
        log_level_enum = LogLevel[log_level.upper()]
    except KeyError:
        _error(f"Invalid log_level '{log_level}'. Choose from: {[l.name for l in LogLevel]}")
        raise typer.Exit(1)

    try:
        template_enum = BadgeTemplate[template.upper()]
    except KeyError:
        _error(f"Invalid template '{template}'. Choose from: {[t.name for t in BadgeTemplate]}")
        raise typer.Exit(1)

    try:
        frame_enum = FrameType[frame.upper()] if frame else None
    except KeyError:
        _error(f"Invalid frame '{frame}'. Choose from: {[f.name for f in FrameType]}")
        raise typer.Exit(1)

    try:
        generator = BadgeGenerator(template=template_enum, log_level=log_level_enum)
        generator.generate_badge(
            left_text=left_text, left_color=left_color, badge_name=badge_name,
            output_path=output_path, right_text=right_text, right_color=right_color,
            logo=logo, frame=frame_enum, left_link=left_link, right_link=right_link,
            id_suffix=id_suffix, left_title=left_title, right_title=right_title,
            logo_tint=logo_tint,
        )
    except (ValueError, TypeError) as exc:
        _error(str(exc))
        raise typer.Exit(1)
```

`output_path=None` is intentionally passed through to `BadgeGenerator`, which resolves `None` → `os.getcwd()` inside `validate_inputs`. No double-defaulting.

### 2.5 `batch` Command

```python
@app.command()
def batch(
    config_file: Path      = typer.Argument(..., exists=True, help="JSON config file"),
    output_path: Optional[str] = typer.Option(None),
    template: str          = typer.Option("DEFAULT"),
    log_level: str         = typer.Option("INFO"),
    max_workers: int       = typer.Option(4),
) -> None:
```

`exists=True` on `config_file` makes Typer automatically reject missing files before the function body runs.

**Progress bar architecture:** `BadgeBatchGenerator.generate_batch()` processes badges inside a `ThreadPoolExecutor` and is not observable externally. To integrate Rich progress, `BadgeBatchGenerator` gains an optional `progress_callback: Optional[Callable[[str], None]] = None` parameter on `generate_batch`. After each badge completes (in the `as_completed` loop), call `progress_callback(badge.get("badge_name", "unknown"))` — extracting the name string from the badge dict. The CLI passes `lambda name: progress.advance(task)` as the callback. The existing API (no callback) is unaffected.

**Execution flow:**
1. Parse JSON; show Rich error panel on `json.JSONDecodeError`
2. Inject `output_path` and `template` into each badge dict. Template from CLI is a global override; per-badge `template` keys in the JSON are not supported and will be ignored (overwritten)
3. Create a `rich.progress.Progress` instance; start it; create one overall task with total = number of badges
4. Call `generate_batch(badges, progress_callback=lambda name: progress.advance(task))`
5. Catch `RuntimeError` from `generate_batch` (aggregated failures); print a Rich summary table regardless of success/failure

**Summary table columns:** Badge Name | Status (✓ / ✗) | Error message

`generate_batch` raises a `RuntimeError` with an aggregated string on partial failures. To populate the summary table with structured per-badge data, `BadgeBatchGenerator` stores failures as `self._failures: List[Tuple[str, str]]` (badge_name, error_str) populated during the `as_completed` loop. The CLI reads `batch_gen._failures` after the call (or catch) to populate the table. The `RuntimeError` is caught but not re-raised; the table serves as the user-facing output.

**Error panel vs summary table:** Rich panels are for pre-execution validation errors only (bad JSON, missing file, invalid template name). Batch runtime errors are displayed exclusively in the summary table.

### 2.6 Rich Error Helper

```python
def _error(message: str) -> None:
    from rich.panel import Panel
    from rich import print as rprint
    rprint(Panel(message, title="Error", border_style="red"))
```

Used for all pre-execution validation failures in both commands.

---

## 3. Medium Issue Fixes

### 3.1 Template Rendering Registry
**File:** `src/badgeshield/badge_generator.py`

`self.template_name` currently stores the enum's `.value` string (e.g. `"templates/label.svg"`). To use enum keys in the registry, `__init__` must also store the enum itself:

```python
self.template_enum = template          # store the BadgeTemplate enum
self.template_name = str(template)     # keep existing str for Jinja2 lookup
```

Add `ClassVar` to the `typing` import at the top of `badge_generator.py`:
```python
from typing import ClassVar, Dict, List, Optional, Tuple, Union
```

Registry definition (class-level, populated after methods are defined):
```python
_RENDERERS: ClassVar[dict] = {}  # populated below class definition
```

Dispatch in `_render_badge_content`:
```python
renderer = self._RENDERERS.get(self.template_enum)
if renderer is None:
    raise ValueError(f"No renderer for template {self.template_enum}")
return renderer(self, ...)
```

After the class body:
```python
BadgeGenerator._RENDERERS = {
    BadgeTemplate.DEFAULT:      BadgeGenerator._render_default,
    BadgeTemplate.CIRCLE:       BadgeGenerator._render_circle,
    BadgeTemplate.CIRCLE_FRAME: BadgeGenerator._render_circle_frame,
}
```

Each renderer (`_render_default`, `_render_circle`, `_render_circle_frame`) extracts from the existing `if/elif` blocks in `_render_badge_content`.

### 3.2 `_last_render_context` Attribute
**File:** `src/badgeshield/badge_generator.py`

At the end of each of the three renderer methods (`_render_default`, `_render_circle`, `_render_circle_frame`), store the dict of kwargs passed to `jinja2 .render(...)` as `self._last_render_context`. This resolves the `AttributeError` in the currently-failing tests.

**Current test failures:** All eleven existing tests using the `badge_generator` and `output_dir` fixtures are currently failing due to the missing `conftest.py` (fixed in Section 4.1). Additionally, three tests (`test_generate_badge_without_gradients_or_shadows`, `test_circle_badge_renders_flat_colors`, `test_circle_frame_badge_renders_without_effects`) fail with `AttributeError` on `_last_render_context`. Creating `conftest.py` fixes the fixture failures; implementing `_last_render_context` (this section) fixes the attribute failures. Both fixes are required for the test suite to pass.

### 3.3 Circle Font Sizing Uses Text Width
**File:** `_calculate_font_size()`

`_calculate_font_size` already has `self` as its first parameter (it is an undecorated instance method). No signature change is needed for `self`. Replace `text_length = len(text)` with `text_length = self._calculate_text_width(text)`.

**Scaling adjustment required:** `_calculate_text_width` returns a pixel-width estimate (typically 40–200), while `len(text)` returns character count (typically 3–20). The formula is `circle_diameter // text_length`. To preserve the original output range (8–35pt), scale `circle_diameter` by a factor that normalises the pixel-width back to character-count magnitude. Use:

```python
text_length = max(1, self._calculate_text_width(text) // 8)
```

The divisor `8` approximates average pixels-per-character for DejaVuSans at badge sizes, preserving the formula's behaviour. Verify with: `assert 8 <= _calculate_font_size("Hi") <= 35` in the unit test for this method.

### 3.4 Dead Code Simplification
**File:** `_calculate_logo_size()`

`adjusted_radius` is a redundant alias (assigned from `circle_radius`, used only once, never modified). Simplify to:
```python
def _calculate_logo_size(self, circle_radius: int) -> Tuple[int, int]:
    logo_diameter = circle_radius * 2
    return (logo_diameter, logo_diameter)
```

### 3.5 Thread-Safe Template Cache
**File:** `badge_generator.py`

Add `import threading` to the imports. Add as class variables:
```python
_template_cache: ClassVar[dict] = {}
_cache_lock: ClassVar[threading.Lock] = threading.Lock()
```

Wrap the cache lookup/store in `_get_template`:
```python
with BadgeGenerator._cache_lock:
    if template_name not in self._template_cache:
        self._template_cache[template_name] = self._jinja2_env.get_template(template_name)
    return self._template_cache[template_name]
```

All Jinja2 template lookups must route through `_get_template`. After the registry refactor (Section 3.1), the three renderer methods (`_render_default`, `_render_circle`, `_render_circle_frame`) each call `self._jinja2_env.get_template(self.template_name)` directly — replace each with `self._get_template(self.template_name)`. No direct calls to `self._jinja2_env.get_template` should remain in any renderer.

### 3.6 `frame` Type Annotation Fix
**Files:** `badge_generator.py` — both `generate_badge()` and `validate_inputs()` signatures

Change in both methods:
```python
frame: Optional[FrameType] = None
→
frame: Optional[Union[FrameType, str]] = None
```

---

## 4. Testing Improvements

### 4.1 `tests/conftest.py` (new file)

```python
import pytest
from badgeshield import BadgeGenerator, BadgeTemplate

@pytest.fixture
def badge_generator():
    return BadgeGenerator(template=BadgeTemplate.DEFAULT)

@pytest.fixture
def output_dir(tmp_path):
    return tmp_path  # return Path, not str — all existing tests use path division operator
```

`output_dir` returns a `Path` object. All eleven existing tests that call `output_dir / badge_name` work without modification.

### 4.2 `tests/test_badge_generator.py` — Fix + Extend

**Fixes:**
- Replace all `custom_badges` imports with `badgeshield`
- `_last_render_context` tests pass automatically once Section 3.2 is implemented

**New tests:**
- **Batch happy path:** Submit 3 badges with distinct names; assert all three `.svg` files exist in `output_dir`
- **Concurrent batch:** `max_workers=3` with 6 badges; assert all 6 output files exist and no file is empty (zero bytes) — this validates no file handle was corrupted by concurrency
- **`CIRCLE` template:** Generate badge; assert output file exists and its contents contain `<circle`
- **`CIRCLE_FRAME` with frame:** Generate with `FrameType.FRAME1`; assert output file exists
- **`CIRCLE_FRAME` without frame:** `pytest.raises(ValueError)` containing "frame"
- **Path traversal:** `badge_name="../escape.svg"` → `pytest.raises(ValueError)`
- **Path traversal absolute:** `badge_name="/tmp/evil.svg"` → `pytest.raises(ValueError)`
- **Missing `.svg` suffix:** `pytest.raises(ValueError)` containing ".svg"
- **Logo tinting with Pillow:** Create a valid 10×10 RGBA PNG using `PIL.Image.new("RGBA", (10,10), (255,0,0,255))` saved to a temp file; call `_load_logo_image` with a tint color; assert the returned base64 string differs from the untinted call result
- **Logo tinting fallback:** Patch `badgeshield.badge_generator.Image = None`; assert `_load_logo_image` returns the plain base64 content without error
- **`get_base64_content` missing file:** `pytest.raises(FileNotFoundError)`

### 4.3 `tests/test_generate_badge_cli.py` — Fix + Extend

**Fixes:**
- Replace all `custom_badges` imports with `badgeshield`
- **Delete** the two existing tests that directly call `validate_single_badge_args` and `validate_batch_badge_args` — those functions are removed in the Typer rewrite. Replace with CLI-level equivalents below.

**New tests** (all using `typer.testing.CliRunner`):
- **`single` happy path:** Invoke with required args; assert exit code 0, output `.svg` file exists
- **`single` invalid color:** Pass `--left-color NOTACOLOR`; assert exit code 1, "Error" in output
- **`single` missing `.svg` suffix:** `--badge-name foo`; assert exit code 1
- **`single` invalid template:** `--template BOGUS`; assert exit code 1
- **`batch` valid JSON:** Write JSON to temp file; invoke; assert exit code 0, all files created
- **`batch` malformed JSON:** Write `{broken` to temp file; assert exit code 1
- **`batch` missing config file:** Pass a nonexistent path; assert exit code 1 (Typer `exists=True` handles this)
- **`batch` CIRCLE_FRAME without frame in config:** Pass `--template CIRCLE_FRAME` at CLI level; JSON contains a badge without a `frame` key; assert exit code 1

---

## 5. Files Changed Summary

| File | Action |
|------|--------|
| `src/badgeshield/generate_badge_cli.py` | Rewrite (Typer + Rich) |
| `src/badgeshield/badge_generator.py` | Modify (registry, enum storage, cache lock, `_last_render_context`, path traversal, type fixes, `progress_callback`) |
| `tests/conftest.py` | Create |
| `tests/test_badge_generator.py` | Fix imports + add/replace tests |
| `tests/test_generate_badge_cli.py` | Fix imports, delete obsolete tests, add CLI tests |
| `requirements.txt` | Add `typer>=0.12`, `rich>=13.0` |
| `pyproject.toml` | Add `[project.optional-dependencies]` for Pillow |

---

## 6. Out of Scope

- `setup.py` removal (legacy compatibility, low risk, separate task)
- Font width consistency between Pillow and fallback paths (requires SVG rendering validation)
- README / MkDocs updates
- Per-badge template overrides in batch JSON (CLI `--template` is a global override)
