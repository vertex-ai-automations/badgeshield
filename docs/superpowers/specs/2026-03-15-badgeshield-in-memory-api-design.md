# BadgeShield In-Memory API Design

## Goal

Add a `render_badge()` method to `BadgeGenerator` that returns the SVG as a `BadgeSVG` string subclass — no file I/O — with `.to_bytes()`, `.to_data_uri()`, and `.save()` helpers. Refactor `generate_badge()` to call `render_badge()` internally, eliminating duplicated rendering logic.

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
        """Write the SVG to *path* (creates or overwrites the file)."""
        Path(path).write_text(self, encoding="utf-8")
```

`base64` is already imported in `badge_generator.py`. No new top-level imports required.

---

### `BadgeGenerator._validate_visual_params()`

Extracted from the first half of the existing `validate_inputs()`. Validates visual rendering parameters only — no file-system concerns.

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

**Validates:**
- `left_text` not empty → `ValueError`
- `frame` via `validate_frame()` when template is `CIRCLE_FRAME`; passthrough otherwise
- `left_color` and `right_color` via `validate_color()`
- Logo file exists on disk when `logo` is provided

**`validate_inputs()` after refactor:**

Calls `_validate_visual_params()` for the visual checks, then adds:
- `output_path` normalization and directory existence check
- `badge_name` `.svg` suffix check
- `badge_name` path traversal protection

Public signature and return type of `validate_inputs()` are **unchanged**: `Tuple[str, str, str, Optional[str]]`.

---

### `BadgeGenerator.render_badge()`

New public method. Same visual parameters as `generate_badge()` minus `output_path` and `badge_name`.

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

**Behaviour:**
1. Calls `_validate_visual_params(left_text, left_color, right_color, logo, frame)` → raises `ValueError`/`TypeError` on invalid input
2. Calls `_render_badge_content(...)` with normalized values
3. Wraps result in `BadgeSVG(svg_string)` and returns it

Nothing is written to disk.

---

### `BadgeGenerator.generate_badge()` refactor

`generate_badge()` becomes a thin wrapper: validate file-system concerns, delegate rendering to `render_badge()`, write result to disk.

**New body (pseudocode):**
```python
def generate_badge(self, left_text, left_color, badge_name, output_path=None, ...) -> None:
    # 1. File-system validation (output path + badge name)
    _, _, resolved_output_path, _ = self.validate_inputs(
        left_text, left_color, output_path, badge_name, right_text, right_color, logo, frame
    )
    # 2. Render (visual validation + rendering happens inside render_badge)
    svg = self.render_badge(
        left_text, left_color, right_text, right_color,
        logo, frame, left_link, right_link,
        id_suffix, left_title, right_title, logo_tint,
    )
    # 3. Write
    full_path = os.path.join(resolved_output_path, badge_name)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(svg)
    self.logger.info(f"Badge generated and saved to {full_path}")
```

Note: `validate_inputs()` still validates colors/frame/logo (via `_validate_visual_params()`) in addition to file-system checks. This means visual parameters are validated twice when `generate_badge()` is called (once in `validate_inputs()`, once in `render_badge()`). The duplication is cheap (no I/O) and keeps both methods independently safe to call. An alternative is to have `generate_badge()` call only file-system validation then `render_badge()`, but that would require splitting `validate_inputs()` further — unnecessary complexity for now.

**Public interface of `generate_badge()` is unchanged**: same signature, same `None` return, same exceptions.

---

### `__init__.py` export

Add `BadgeSVG` to the public API:

```python
from .badge_generator import BadgeSVG, BadgeBatchGenerator, BadgeGenerator
```

---

## Error Handling

`render_badge()` raises the same exceptions as `generate_badge()` for invalid visual inputs:
- `ValueError` — empty text, invalid color, bad frame, missing logo file
- `TypeError` — wrong type for color or frame
- `RuntimeError` — template not found (from `_get_template`)

No new exception types introduced.

---

## Testing

Four new tests added to `tests/test_badge_generator.py`. Import: `from badgeshield.badge_generator import BadgeSVG`.

```python
def test_render_badge_returns_badge_svg_instance(badge_generator):
    result = badge_generator.render_badge(left_text="build", left_color="#44cc11")
    assert isinstance(result, BadgeSVG)
    assert "<svg" in result  # works as plain str


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
```

All existing `generate_badge()` tests must continue to pass without modification.

---

## Files Changed

| File | Change |
|------|--------|
| `src/badgeshield/badge_generator.py` | Add `BadgeSVG`; extract `_validate_visual_params()`; add `render_badge()`; refactor `generate_badge()` |
| `src/badgeshield/__init__.py` | Export `BadgeSVG` |
| `tests/test_badge_generator.py` | 4 new tests; 1 new import (`BadgeSVG`) |

No new dependencies. No changes to `generate_badge_cli.py`, `utils.py`, or templates.
