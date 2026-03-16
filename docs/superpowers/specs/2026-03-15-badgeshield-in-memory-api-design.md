# BadgeShield In-Memory API Design

## Goal

Add a `render_badge()` method to `BadgeGenerator` that returns the SVG as a `BadgeSVG` string subclass — no output file I/O — with `.to_bytes()`, `.to_data_uri()`, and `.save()` helpers. Refactor `generate_badge()` to call `render_badge()` internally, eliminating duplicated rendering logic.

## Architecture

Three coordinated changes inside `src/badgeshield/badge_generator.py`:

1. **`BadgeSVG(str)` result wrapper** — top of module, before `BadgeBatchGenerator`
2. **`_validate_visual_params()`** — private method extracted from `validate_inputs()`
3. **`render_badge()`** — new public method on `BadgeGenerator`
4. **`generate_badge()` refactor** — calls `render_badge()` then writes to disk

`BadgeSVG` is also exported from `src/badgeshield/__init__.py`.

**Scope boundary:** `BadgeBatchGenerator` is not changed. In-memory batch generation is out of scope.

---

## Component Specifications

### `BadgeSVG` (str subclass)

Location: `src/badgeshield/badge_generator.py`, defined before `BadgeBatchGenerator`.

```python
class BadgeSVG(str):
    """SVG badge content as a string with helper conversion methods.

    Behaves as a plain ``str`` in all string contexts. The extra methods
    provide common conversions without requiring callers to import anything
    beyond ``BadgeGenerator``.
    """

    def to_bytes(self, encoding: str = "utf-8") -> bytes:
        """Return the SVG encoded as bytes."""
        return self.encode(encoding)

    def to_data_uri(self) -> str:
        """Return a base64-encoded ``data:image/svg+xml`` URI."""
        encoded = base64.b64encode(self.to_bytes()).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"

    def save(self, path: Union[str, Path]) -> None:
        """Write the SVG to *path* (creates or overwrites the file).

        The parent directory must already exist; this method does not create it.
        Raises ``FileNotFoundError`` if the parent directory is absent.
        """
        Path(path).write_text(self, encoding="utf-8")
```

All types used by `BadgeSVG` (`base64`, `Union`, `Path`) are already imported in `badge_generator.py`. No new top-level imports required.

---

### `BadgeGenerator._validate_visual_params()`

Extracted from the first half of the existing `validate_inputs()`. Validates visual rendering parameters — text, colors, frame, and logo — with **one explicit exception**: logo file existence is checked here even though it is an I/O operation. This keeps `render_badge()` independently safe to call (a missing logo file would produce a broken SVG).

**Note on double validation in `generate_badge()`:** Because `validate_inputs()` delegates to `_validate_visual_params()`, and `generate_badge()` calls both `validate_inputs()` and `render_badge()` (which also calls `_validate_visual_params()`), colors, frame, and logo are validated twice. For `CIRCLE_FRAME` badges, `validate_frame()` also runs twice. These duplicate calls are cheap and the accepted trade-off for keeping both callers independently safe.

**Signature:**
```python
def _validate_visual_params(
    self,
    left_text: str,
    left_color: Union[BadgeColor, str],
    right_color: Optional[Union[BadgeColor, str]] = None,
    logo: Optional[str] = None,
    frame: Optional[Union[FrameType, str]] = None,
) -> Tuple[str, str, Optional[str]]:
```

**Returns:** `(left_color_hex, right_color_hex, frame_value)`

- `right_color_hex` defaults to `left_color_hex` when `right_color` is falsy (i.e., `None` or empty string `""`) — replicates the existing `if right_color` falsy check from `validate_inputs()` exactly
- `frame_value` is `None` when `frame` is `None`

**`right_text` is intentionally absent** from this signature — it was never validated in `validate_inputs()` and has no role in visual parameter validation.

**Validates (exact logic preserved from `validate_inputs()`):**

1. `left_text` not empty → `ValueError("left_text cannot be empty.")`
2. Frame normalization — three branches:
   - If `self.template_name == BadgeTemplate.CIRCLE_FRAME.value`: call `self.validate_frame(frame)` → returns validated string
   - Elif `isinstance(frame, FrameType)`: `frame_value = frame.value`
   - Else: `frame_value = frame` (covers `str`, `None`)
3. `left_color` via `self.validate_color(left_color, "left_color")`
4. If `right_color` is truthy: `right_color_hex = self.validate_color(right_color, "right_color")`; else: `right_color_hex = left_color_hex`
5. Logo existence:
   ```python
   if logo:
       logo_path = Path(logo)
       if not logo_path.is_absolute():
           logo_path = Path(self.local_path(logo))
       if not logo_path.is_file():
           raise ValueError(f"Logo file {logo} does not exist.")
   ```

**`validate_inputs()` after refactor:**
Calls `_validate_visual_params()` then adds `output_path`/`badge_name` checks. Public signature **unchanged** — `right_text` stays as accepted-but-unused parameter. Return type **unchanged**: `Tuple[str, str, str, Optional[str]]`.

---

### `BadgeGenerator.render_badge()`

New public method. Note: `render_badge()` does not write an output file, but it does perform **read** I/O — `_render_badge_content()` reads frame assets and logo files from disk.

**Signature:**
```python
def render_badge(
    self,
    left_text: str,
    left_color: Union[BadgeColor, str],
    right_text: Optional[str] = None,
    right_color: Optional[Union[BadgeColor, str]] = None,
    logo: Optional[str] = None,
    frame: Optional[Union[FrameType, str]] = None,
    left_link: Optional[str] = None,
    right_link: Optional[str] = None,
    id_suffix: str = "",
    left_title: Optional[str] = None,
    right_title: Optional[str] = None,
    logo_tint: Optional[Union[str, BadgeColor]] = None,
) -> BadgeSVG:
```

`logo_tint` only applied when Pillow is installed — same as existing `generate_badge()` behavior.

**Behaviour:**
1. `_validate_visual_params(left_text, left_color, right_color, logo, frame)` → `(left_color_hex, right_color_hex, frame_value)`
2. `_render_badge_content(left_text, left_color_hex, right_text, right_color_hex, logo, frame_value, left_link, right_link, id_suffix, left_title, right_title, logo_tint)`
3. Return `BadgeSVG(svg_string)`

No `try/except` wrapper — all exceptions propagate directly to the caller.

---

### `BadgeGenerator.generate_badge()` refactor

`generate_badge()` passes the **raw `frame` argument** (not the already-resolved value from `validate_inputs()`) to `render_badge()`, so that `render_badge()` normalizes it independently via `_validate_visual_params()`. The resulting double `validate_frame()` call for `CIRCLE_FRAME` badges is accepted (see note in `_validate_visual_params()` above).

**New body (pseudocode):**
```python
def generate_badge(self, left_text, left_color, badge_name, output_path=None, ...) -> None:
    # 1. File-system validation (output path + badge name)
    _, _, resolved_output_path, _ = self.validate_inputs(
        left_text, left_color, output_path, badge_name, right_text, right_color, logo, frame
    )
    # 2. Render and write — preserve existing try/except error-logging wrapper
    full_path = os.path.join(resolved_output_path, badge_name)
    try:
        svg = self.render_badge(
            left_text, left_color, right_text, right_color,
            logo, frame, left_link, right_link,
            id_suffix, left_title, right_title, logo_tint,
        )
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(svg)
        self.logger.info(f"Badge generated and saved to {full_path}")
    except Exception as e:
        self.logger.error(f"An error occurred while generating the badge: {e}")
        raise
```

**Important:** The file write must use the inline `open()` block shown above. Do **not** replace it with `svg.save(full_path)` — that would lose the `self.logger.info()` call and the `try/except` wrapper.

The `try/except` wraps both `render_badge()` and the file write, preserving error logging for read-I/O failures that occur inside rendering (e.g., missing frame assets).

**Public interface unchanged**: same signature, `None` return, same exceptions.

---

### `__init__.py` export

```python
from ._version import __version__
from .badge_generator import BadgeSVG, BadgeBatchGenerator, BadgeGenerator, LogLevel
from .utils import BadgeColor, BadgeTemplate, FrameType

__all__ = [
    "BadgeGenerator",
    "BadgeBatchGenerator",
    "BadgeSVG",
    "BadgeColor",
    "BadgeTemplate",
    "FrameType",
    "LogLevel",
    "__version__",
]
```

`LogLevel` must remain in both the import line and `__all__` — it is part of the existing public API.

---

## Error Handling

`render_badge()` propagates without wrapping:
- `ValueError` — empty `left_text`, invalid color, bad frame, missing logo file, or no renderer registered for the current template (from `_render_badge_content`)
- `TypeError` — wrong type for `left_color`, `right_color`, or `frame`
- `RuntimeError` — Jinja2 template file not found on disk (from `_get_template`)

---

## Testing

Ten new tests in `tests/test_badge_generator.py`. Add import: `from badgeshield.badge_generator import BadgeSVG`. All existing imports remain.

### Happy-path

```python
def test_render_badge_returns_badge_svg_instance(badge_generator):
    result = badge_generator.render_badge(left_text="build", left_color="#44cc11")
    assert isinstance(result, BadgeSVG)
    assert "<svg" in result


def test_render_badge_to_bytes(badge_generator):
    result = badge_generator.render_badge(left_text="build", left_color="#44cc11")
    b = result.to_bytes()
    assert isinstance(b, bytes)
    assert b"<svg" in b


def test_render_badge_to_data_uri(badge_generator):
    result = badge_generator.render_badge(left_text="build", left_color="#44cc11")
    uri = result.to_data_uri()
    assert uri.startswith("data:image/svg+xml;base64,")


def test_render_badge_save(badge_generator, output_dir):
    result = badge_generator.render_badge(left_text="build", left_color="#44cc11")
    dest = output_dir / "render.svg"
    result.save(dest)
    assert dest.exists()
    assert "<svg" in dest.read_text()


def test_render_badge_circle_template():
    gen = BadgeGenerator(template=BadgeTemplate.CIRCLE)
    result = gen.render_badge(left_text="v2", left_color="#673ab7")
    assert isinstance(result, BadgeSVG)
    assert "<svg" in result
```

### Error-path

```python
def test_render_badge_raises_on_empty_text(badge_generator):
    with pytest.raises(ValueError):
        badge_generator.render_badge(left_text="", left_color="#44cc11")


def test_render_badge_raises_on_invalid_color_string(badge_generator):
    # Unrecognized string → ValueError (type is str, but value is not a valid hex or BadgeColor name)
    with pytest.raises(ValueError):
        badge_generator.render_badge(left_text="build", left_color="not-a-color")


def test_render_badge_raises_on_missing_logo_absolute(badge_generator):
    # Absolute path that does not exist
    with pytest.raises(ValueError):
        badge_generator.render_badge(
            left_text="build", left_color="#44cc11", logo="/nonexistent/logo.png"
        )


def test_render_badge_raises_on_missing_logo_relative(badge_generator):
    # Relative path — exercises the local_path() resolution branch
    with pytest.raises(ValueError):
        badge_generator.render_badge(
            left_text="build", left_color="#44cc11", logo="nonexistent_relative_logo.png"
        )
```

### Regression

```python
def test_generate_badge_still_writes_file(badge_generator, output_dir):
    """generate_badge() must continue writing SVG to disk after the refactor."""
    badge_generator.generate_badge(
        left_text="build",
        left_color="#44cc11",
        badge_name="regression.svg",
        output_path=str(output_dir),
    )
    out = output_dir / "regression.svg"
    assert out.exists()
    assert "<svg" in out.read_text()
```

All existing `generate_badge()` tests must pass without modification.

---

## Files Changed

| File | Change |
|------|--------|
| `src/badgeshield/badge_generator.py` | Add `BadgeSVG`; extract `_validate_visual_params()`; add `render_badge()`; refactor `generate_badge()` |
| `src/badgeshield/__init__.py` | Add `BadgeSVG` to import and `__all__`; retain `LogLevel` |
| `tests/test_badge_generator.py` | 10 new tests (5 happy-path, 4 error-path, 1 regression); add `BadgeSVG` import |

No new dependencies. No changes to `generate_badge_cli.py`, `utils.py`, or templates.
