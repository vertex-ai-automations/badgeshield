# badgeshield CLI Modernization & Code Remediation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all critical/high/medium bugs in badgeshield and replace the argparse CLI with Typer + Rich.

**Architecture:** Fix test infrastructure first (import renames + conftest), then harden the core library (path traversal, template registry, thread-safe cache), then add the progress_callback hook to BadgeBatchGenerator, then rewrite the CLI as a thin Typer layer over the existing library API.

**Tech Stack:** Python 3.8+, pytest, Typer ≥0.12, Rich ≥13.0, Jinja2, Pillow (optional)

**Spec:** `docs/superpowers/specs/2026-03-15-badgeshield-cli-modernization-design.md`

---

## Chunk 1: Test Foundation

### Task 1: Fix test imports — `test_badge_generator.py`

**Files:**
- Modify: `tests/test_badge_generator.py`

These tests import from the old package name `custom_badges`. Fix all three import sites.

- [ ] **Step 1: Replace the two top-level imports**

In `tests/test_badge_generator.py` replace lines 3–4:
```python
# OLD
from custom_badges.badge_generator import BadgeBatchGenerator, BadgeGenerator
from custom_badges.utils import BadgeColor, BadgeTemplate, FrameType

# NEW
from badgeshield.badge_generator import BadgeBatchGenerator, BadgeGenerator
from badgeshield.utils import BadgeColor, BadgeTemplate, FrameType
```

- [ ] **Step 2: Replace the in-function import (line 145)**

In `test_text_width_fallback_handles_wide_characters`, replace:
```python
# OLD
from custom_badges import badge_generator as badge_module

# NEW
from badgeshield import badge_generator as badge_module
```

- [ ] **Step 3: Commit**
```bash
git add tests/test_badge_generator.py
git commit -m "fix: update test imports from custom_badges to badgeshield"
```

---

### Task 2: Fix test imports — `test_generate_badge_cli.py`

**Files:**
- Modify: `tests/test_generate_badge_cli.py`

- [ ] **Step 1: Replace top-level imports**

Replace lines 7–11:
```python
# OLD
from custom_badges.generate_badge_cli import (
    validate_batch_badge_args,
    validate_single_badge_args,
)
from custom_badges.utils import BadgeTemplate

# NEW — temporarily keep until CLI rewrite; just fix package name
from badgeshield.generate_badge_cli import (
    validate_batch_badge_args,
    validate_single_badge_args,
)
from badgeshield.utils import BadgeTemplate
```

- [ ] **Step 2: Commit**
```bash
git add tests/test_generate_badge_cli.py
git commit -m "fix: update CLI test imports from custom_badges to badgeshield"
```

---

### Task 3: Create `tests/conftest.py`

**Files:**
- Create: `tests/conftest.py`

- [ ] **Step 1: Create the file**

```python
import pytest

from badgeshield import BadgeGenerator, BadgeTemplate


@pytest.fixture
def badge_generator():
    return BadgeGenerator(template=BadgeTemplate.DEFAULT)


@pytest.fixture
def output_dir(tmp_path):
    # Return Path (not str) — existing tests use path division: output_dir / BADGE_NAME
    return tmp_path
```

- [ ] **Step 2: Run the full test suite and record baseline**

```bash
pytest tests/ -v --tb=short 2>&1 | head -80
```

Expected: Most fixture-using tests now run. Still expect failures on:
- `test_generate_badge_without_gradients_or_shadows` — `AttributeError: _last_render_context` (fixed in Task 7)
- `test_circle_badge_renders_flat_colors` — same
- `test_circle_frame_badge_renders_without_effects` — same
- `test_invalid_log_level` — may pass or fail depending on pylogshield behaviour
- `test_generate_badge_cli.py` tests — still use deleted functions (fixed in Task 10)

Record this output. Any test not in the list above should be passing.

- [ ] **Step 3: Commit**
```bash
git add tests/conftest.py
git commit -m "test: add conftest.py with badge_generator and output_dir fixtures"
```

---

## Chunk 2: Core Library Fixes

### Task 4: Fix CLI imports in `generate_badge_cli.py`

**Files:**
- Modify: `src/badgeshield/generate_badge_cli.py` lines 5–11

- [ ] **Step 1: Fix the imports**

Replace lines 5–11:
```python
# OLD
from .badge_generator import (
    BadgeBatchGenerator,
    BadgeGenerator,
    BadgeTemplate,
    FrameType,
    LogLevel,
)

# NEW
from pylogshield import LogLevel

from .badge_generator import BadgeBatchGenerator, BadgeGenerator
from .utils import BadgeColor, BadgeTemplate, FrameType
```

- [ ] **Step 2: Verify CLI still works**
```bash
python -m badgeshield.generate_badge_cli --help
```
Expected: help text prints without ImportError.

- [ ] **Step 3: Run tests**
```bash
pytest tests/test_generate_badge_cli.py -v --tb=short
```
Expected: same pass/fail as before (tests still use deleted functions, but no new failures).

- [ ] **Step 4: Commit**
```bash
git add src/badgeshield/generate_badge_cli.py
git commit -m "fix: correct CLI imports — enums from utils, LogLevel from pylogshield"
```

---

### Task 5: Path traversal protection (TDD)

**Files:**
- Modify: `tests/test_badge_generator.py` (add tests)
- Modify: `src/badgeshield/badge_generator.py` (add validation)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_badge_generator.py`:
```python
def test_path_traversal_rejected(badge_generator, output_dir):
    """badge_name with directory traversal must raise ValueError."""
    with pytest.raises(ValueError, match="traversal"):
        badge_generator.generate_badge(
            left_text="test",
            left_color="#44cc11",
            badge_name="../escape.svg",
            output_path=str(output_dir),
        )


def test_absolute_badge_name_rejected(badge_generator, output_dir):
    """Absolute paths in badge_name must raise ValueError."""
    with pytest.raises(ValueError):
        badge_generator.generate_badge(
            left_text="test",
            left_color="#44cc11",
            badge_name="/tmp/evil.svg",
            output_path=str(output_dir),
        )
```

- [ ] **Step 2: Run to confirm FAIL**
```bash
pytest tests/test_badge_generator.py::test_path_traversal_rejected tests/test_badge_generator.py::test_absolute_badge_name_rejected -v
```
Expected: FAIL — no traversal check exists yet.

- [ ] **Step 3: Implement the protection**

In `src/badgeshield/badge_generator.py`, locate `validate_inputs`. Find the block that validates `.svg` suffix (currently at the end of the method). Add the traversal check **immediately after** it:

```python
# Ensure badge_name is valid
if not badge_name.endswith(".svg"):
    raise ValueError(
        f"badge_name {badge_name} is not valid, must end with '.svg' (e.g., 'badge.svg')."
    )

# Prevent path traversal
badge_path = Path(badge_name)
if any(part in ("..", ".") for part in badge_path.parts[:-1]):
    raise ValueError(
        f"badge_name '{badge_name}' must not contain directory traversal."
    )
if badge_path.is_absolute():
    raise ValueError(
        f"badge_name '{badge_name}' must be a plain filename, not an absolute path."
    )
```

Note: `Path` is already imported at the top of `badge_generator.py`.

- [ ] **Step 4: Run tests to confirm PASS**
```bash
pytest tests/test_badge_generator.py::test_path_traversal_rejected tests/test_badge_generator.py::test_absolute_badge_name_rejected -v
```
Expected: PASS.

- [ ] **Step 5: Run full suite to check for regressions**
```bash
pytest tests/test_badge_generator.py -v --tb=short
```
Expected: same pass/fail baseline as after Task 3.

- [ ] **Step 6: Commit**
```bash
git add tests/test_badge_generator.py src/badgeshield/badge_generator.py
git commit -m "fix: add path traversal protection to badge_name validation"
```

---

### Task 6: Update `typing` import + add `ClassVar`

**Files:**
- Modify: `src/badgeshield/badge_generator.py` line 8

This is a prerequisite for Task 7 (registry) and Task 8 (thread-safe cache).

- [ ] **Step 1: Update the typing import**

Replace line 8:
```python
# OLD
from typing import Dict, List, Optional, Tuple, Union

# NEW
from typing import Callable, ClassVar, Dict, List, Optional, Tuple, Union
```

(`Callable` is needed for the `progress_callback` in Task 11.)

- [ ] **Step 2: Add `import threading`** after the existing imports block (after line 6 `import re`):
```python
import threading
```

- [ ] **Step 3: Run tests — no change expected**
```bash
pytest tests/test_badge_generator.py -v --tb=short
```

- [ ] **Step 4: Commit**
```bash
git add src/badgeshield/badge_generator.py
git commit -m "chore: add ClassVar, Callable, threading imports to badge_generator"
```

---

### Task 7: Template rendering registry + `_last_render_context`

**Files:**
- Modify: `src/badgeshield/badge_generator.py`

The three existing `_last_render_context` tests currently fail with `AttributeError`. Implementing this task fixes them — they serve as the TDD oracle.

- [ ] **Step 1: Run the three oracle tests to confirm they FAIL**
```bash
pytest tests/test_badge_generator.py::test_generate_badge_without_gradients_or_shadows tests/test_badge_generator.py::test_circle_badge_renders_flat_colors tests/test_badge_generator.py::test_circle_frame_badge_renders_without_effects -v
```
Expected: FAIL with `AttributeError: 'BadgeGenerator' object has no attribute '_last_render_context'`.

- [ ] **Step 2: Store `template_enum` in `BadgeGenerator.__init__`**

In the `__init__` method, after `self.template_name = str(template)`, add:
```python
self.template_enum = template  # kept for registry dispatch
```

- [ ] **Step 3: Add the `_RENDERERS` class variable**

After `_template_cache = {}` (line 193), add:
```python
_RENDERERS: ClassVar[dict] = {}  # populated after class body
```

- [ ] **Step 4: Extract `_render_default` method**

Add this private method to `BadgeGenerator`, extracting from the existing `if self.template_name == BadgeTemplate.DEFAULT.value:` block in `_render_badge_content`:

```python
def _render_default(
    self,
    left_text: str,
    left_color: str,
    right_text: Optional[str],
    right_color: Optional[str],
    logo: Optional[str],
    frame: Optional[str],
    left_link: Optional[str],
    right_link: Optional[str],
    id_suffix: str,
    left_title: Optional[str],
    right_title: Optional[str],
    logo_tint: Optional[Union[str, "BadgeColor"]],
) -> str:
    logo_data = self._load_logo_image(logo, logo_tint) if logo else None
    left_text_width = self._calculate_text_width(left_text)
    right_text_width = self._calculate_text_width(right_text) if right_text else 0
    logo_width = 14 if logo else 0
    logo_padding = 3 if logo else 0
    text_padding = 10
    left_width = left_text_width + text_padding + logo_width + logo_padding
    right_width = right_text_width + text_padding if right_text else 0
    total_width = left_width + right_width + (text_padding if right_text else 0)
    context = dict(
        left_text=left_text,
        right_text=right_text,
        left_color=left_color,
        right_color=right_color if right_text else left_color,
        left_text_width=left_text_width,
        right_text_width=right_text_width,
        logo=logo_data,
        left_link=left_link,
        right_link=right_link,
        id_suffix=id_suffix,
        left_width=left_width,
        right_width=right_width,
        logo_width=logo_width,
        logo_padding=logo_padding,
        text_padding=text_padding,
        total_width=total_width,
        left_title=left_title,
        right_title=right_title,
    )
    self._last_render_context = context
    return self._get_template(self.template_name).render(**context)
```

- [ ] **Step 5: Extract `_render_circle` method**

```python
def _render_circle(
    self,
    left_text: str,
    left_color: str,
    right_text: Optional[str],
    right_color: Optional[str],
    logo: Optional[str],
    frame: Optional[str],
    left_link: Optional[str],
    right_link: Optional[str],
    id_suffix: str,
    left_title: Optional[str],
    right_title: Optional[str],
    logo_tint: Optional[Union[str, "BadgeColor"]],
) -> str:
    logo_data = self._load_logo_image(logo, logo_tint) if logo else None
    font_size = self._calculate_font_size(left_text)
    context = dict(
        left_text=left_text,
        right_text=right_text,
        left_color=left_color,
        id_suffix=id_suffix,
        logo=logo_data,
        left_link=left_link,
        left_title=left_title,
        font_size=font_size,
    )
    self._last_render_context = context
    return self._get_template(self.template_name).render(**context)
```

- [ ] **Step 6: Extract `_render_circle_frame` method**

```python
def _render_circle_frame(
    self,
    left_text: str,
    left_color: str,
    right_text: Optional[str],
    right_color: Optional[str],
    logo: Optional[str],
    frame: Optional[str],
    left_link: Optional[str],
    right_link: Optional[str],
    id_suffix: str,
    left_title: Optional[str],
    right_title: Optional[str],
    logo_tint: Optional[Union[str, "BadgeColor"]],
) -> str:
    logo_data = self._load_logo_image(logo, logo_tint) if logo else None
    circle_radius = 35
    logo_width, logo_height = self._calculate_logo_size(circle_radius)
    font_size = self._calculate_font_size(left_text, circle_diameter=circle_radius * 2)
    frame_data = self.get_base64_content(frame) if frame else None
    context = dict(
        left_text=left_text,
        left_color=left_color,
        logo=logo_data,
        frame=frame_data,
        left_link=left_link,
        left_title=left_title,
        font_size=font_size,
        logo_width=logo_width,
        logo_height=logo_height,
        id_suffix=id_suffix,
    )
    self._last_render_context = context
    return self._get_template(self.template_name).render(**context)
```

- [ ] **Step 7: Rewrite `_render_badge_content` as a dispatcher**

Replace the entire existing `_render_badge_content` method body with:
```python
def _render_badge_content(
    self,
    left_text: str,
    left_color: str,
    right_text: Optional[str],
    right_color: Optional[str],
    logo: Optional[str],
    frame: Optional[str],
    left_link: Optional[str],
    right_link: Optional[str],
    id_suffix: str,
    left_title: Optional[str],
    right_title: Optional[str],
    logo_tint: Optional[Union[str, "BadgeColor"]],
) -> str:
    renderer = BadgeGenerator._RENDERERS.get(self.template_enum)
    if renderer is None:
        raise ValueError(f"No renderer registered for template {self.template_enum}")
    return renderer(
        self,
        left_text, left_color, right_text, right_color, logo, frame,
        left_link, right_link, id_suffix, left_title, right_title, logo_tint,
    )
```

- [ ] **Step 8: Register the renderers after the class body**

After the closing of the `BadgeGenerator` class definition, add:
```python
BadgeGenerator._RENDERERS = {
    BadgeTemplate.DEFAULT: BadgeGenerator._render_default,
    BadgeTemplate.CIRCLE: BadgeGenerator._render_circle,
    BadgeTemplate.CIRCLE_FRAME: BadgeGenerator._render_circle_frame,
}
```

- [ ] **Step 9: Add `_cache_lock` class variable**

Below `_template_cache = {}` (and the newly added `_RENDERERS`), add:
```python
_cache_lock: ClassVar[threading.Lock] = threading.Lock()
```

- [ ] **Step 10: Update `_get_template` to use the lock**

Replace the body of `_get_template`:
```python
def _get_template(self, template_name: str) -> Optional[Template]:
    try:
        with BadgeGenerator._cache_lock:
            if template_name not in self._template_cache:
                self._template_cache[template_name] = self._jinja2_env.get_template(
                    template_name
                )
            return self._template_cache[template_name]
    except TemplateNotFound:
        self.logger.error(
            f"Template {template_name} not found in package 'badgeshield'"
        )
        return None
```

- [ ] **Step 11: Run the three oracle tests to confirm they PASS**
```bash
pytest tests/test_badge_generator.py::test_generate_badge_without_gradients_or_shadows tests/test_badge_generator.py::test_circle_badge_renders_flat_colors tests/test_badge_generator.py::test_circle_frame_badge_renders_without_effects -v
```
Expected: PASS.

- [ ] **Step 12: Run the full generator test suite**
```bash
pytest tests/test_badge_generator.py -v --tb=short
```
Expected: all tests that were passing before still pass; the 3 oracle tests now also pass.

- [ ] **Step 13: Commit**
```bash
git add src/badgeshield/badge_generator.py
git commit -m "refactor: add template registry, _last_render_context, thread-safe template cache"
```

---

### Task 8: Circle font sizing, dead code, type annotation fixes

**Files:**
- Modify: `src/badgeshield/badge_generator.py`

- [ ] **Step 1: Write the font sizing test**

Append to `tests/test_badge_generator.py`:
```python
def test_circle_font_size_stays_in_range(badge_generator):
    """Font size for circle badges must remain in the 8-35pt range."""
    generator = BadgeGenerator(template=BadgeTemplate.CIRCLE)
    # Short text — should be near max size
    assert 8 <= generator._calculate_font_size("Hi") <= 35
    # Longer text — should shrink but stay above minimum
    assert 8 <= generator._calculate_font_size("A longer badge label") <= 35
```

- [ ] **Step 2: Run to confirm it PASSES already (baseline)**
```bash
pytest tests/test_badge_generator.py::test_circle_font_size_stays_in_range -v
```
This should PASS with the current `len(text)` implementation. If it fails, record the output.

- [ ] **Step 3: Fix `_calculate_font_size` to use text width**

In `_calculate_font_size`, replace:
```python
text_length = len(text)
```
with:
```python
text_length = max(1, self._calculate_text_width(text) // 8)
```

The `// 8` normalises pixel-width back to a character-count magnitude (avg 8px/char for DejaVuSans at badge sizes), preserving the formula's output range.

- [ ] **Step 4: Run the font sizing test to confirm it still PASSES**
```bash
pytest tests/test_badge_generator.py::test_circle_font_size_stays_in_range -v
```
Expected: PASS. If fails, the divisor `8` needs adjustment — try `6` or `10` until in-range.

- [ ] **Step 5: Remove dead code in `_calculate_logo_size`**

Replace the method body:
```python
def _calculate_logo_size(self, circle_radius: int) -> Tuple[int, int]:
    logo_diameter = circle_radius * 2
    return (logo_diameter, logo_diameter)
```

- [ ] **Step 6: Fix `frame` type annotations**

In `generate_badge` signature (around line 698), change:
```python
frame: Optional[FrameType] = None,
```
to:
```python
frame: Optional[Union[FrameType, str]] = None,
```

In `validate_inputs` signature (around line 313), make the same change.

- [ ] **Step 7: Run the full test suite**
```bash
pytest tests/test_badge_generator.py -v --tb=short
```
Expected: all tests pass (same as Task 7 baseline plus the new font sizing test).

- [ ] **Step 8: Commit**
```bash
git add tests/test_badge_generator.py src/badgeshield/badge_generator.py
git commit -m "fix: circle font sizing uses text width, remove dead code, fix frame type hints"
```

---

## Chunk 3: Packaging Changes

### Task 9: Update `requirements.txt` and `pyproject.toml`

**Files:**
- Modify: `requirements.txt`
- Modify: `pyproject.toml`

- [ ] **Step 1: Add new CLI dependencies to `requirements.txt`**

Append to `requirements.txt`:
```
typer>=0.12
rich>=13.0
```

- [ ] **Step 2: Add optional Pillow dep to `pyproject.toml`**

In `pyproject.toml`, add after `[project]` section (after the existing `dynamic` line):
```toml
[project.optional-dependencies]
image = ["Pillow>=9.0"]
```

- [ ] **Step 3: Install the new dependencies**
```bash
pip install -r requirements.txt
```
Expected: typer and rich install without error.

- [ ] **Step 4: Commit**
```bash
git add requirements.txt pyproject.toml
git commit -m "deps: add typer and rich as required deps, declare Pillow as optional"
```

---

## Chunk 4: CLI Rewrite

### Task 10: Add `progress_callback` and `_failures` to `BadgeBatchGenerator` (TDD)

**Files:**
- Modify: `tests/test_badge_generator.py` (add tests)
- Modify: `src/badgeshield/badge_generator.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_badge_generator.py`:
```python
def test_batch_progress_callback_called_for_each_badge(output_dir):
    """progress_callback must be called once per badge regardless of success/failure."""
    called_with = []

    batch_generator = BadgeBatchGenerator(max_workers=1)
    badges = [
        {
            "left_text": "badge1",
            "left_color": "#44cc11",
            "badge_name": "one.svg",
            "output_path": str(output_dir),
            "template": BadgeTemplate.DEFAULT,
        },
        {
            "left_text": "badge2",
            "left_color": "#0000ff",
            "badge_name": "two.svg",
            "output_path": str(output_dir),
            "template": BadgeTemplate.DEFAULT,
        },
    ]

    batch_generator.generate_batch(badges, progress_callback=lambda name: called_with.append(name))

    assert len(called_with) == 2
    assert set(called_with) == {"one.svg", "two.svg"}


def test_batch_failures_stored_on_instance(output_dir):
    """_failures must contain (badge_name, error_str) tuples for each failed badge."""
    batch_generator = BadgeBatchGenerator(max_workers=1)
    badges = [
        {
            "left_text": "",  # empty text triggers ValueError
            "left_color": "#ffffff",
            "badge_name": "bad.svg",
            "output_path": str(output_dir),
            "template": BadgeTemplate.DEFAULT,
        }
    ]

    with pytest.raises(RuntimeError):
        batch_generator.generate_batch(badges)

    assert len(batch_generator._failures) == 1
    assert batch_generator._failures[0][0] == "bad.svg"
```

- [ ] **Step 2: Run to confirm FAIL**
```bash
pytest tests/test_badge_generator.py::test_batch_progress_callback_called_for_each_badge tests/test_badge_generator.py::test_batch_failures_stored_on_instance -v
```
Expected: FAIL — `generate_batch` does not accept `progress_callback` yet.

- [ ] **Step 3: Update `BadgeBatchGenerator.generate_batch`**

Update the `__init__` to initialise `_failures`:
```python
def __init__(
    self, max_workers: int = 5, log_level: Union[LogLevel, str] = LogLevel.INFO
):
    self.max_workers = max_workers
    self.log_level = log_level
    self.logger = get_logger(name="badgeshield.batch", log_level=log_level)
    self._failures: List[Tuple[str, str]] = []
```

Update `generate_batch` signature and body:
```python
def generate_batch(
    self,
    badges: List[Dict],
    progress_callback: Optional[Callable[[str], None]] = None,
) -> None:
    self._failures = []  # reset on each call
    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
        future_to_badge = {
            executor.submit(self._generate_single_badge, **badge): badge
            for badge in badges
        }
        errors: List[Tuple[Dict, Exception]] = []

        for future in as_completed(future_to_badge):
            badge = future_to_badge[future]
            badge_name = badge.get("badge_name", "unknown")
            try:
                future.result()
            except Exception as exc:
                self.logger.error(
                    "Failed to generate badge",
                    extra={"badge": badge_name, "error": str(exc)},
                )
                errors.append((badge, exc))
                self._failures.append((badge_name, str(exc)))
            else:
                self.logger.info(
                    "Successfully generated badge",
                    extra={"badge": badge_name},
                )
            finally:
                if progress_callback is not None:
                    progress_callback(badge_name)

        if errors:
            failure_summaries = ", ".join(
                f"{name}: {err}" for name, err in self._failures
            )
            raise RuntimeError(
                f"Failed to generate {len(errors)} badge(s): {failure_summaries}"
            )
```

- [ ] **Step 4: Run failing tests to confirm PASS**
```bash
pytest tests/test_badge_generator.py::test_batch_progress_callback_called_for_each_badge tests/test_badge_generator.py::test_batch_failures_stored_on_instance -v
```
Expected: PASS.

- [ ] **Step 5: Run full test suite**
```bash
pytest tests/test_badge_generator.py -v --tb=short
```
Expected: all tests pass.

- [ ] **Step 6: Commit**
```bash
git add tests/test_badge_generator.py src/badgeshield/badge_generator.py
git commit -m "feat: add progress_callback and _failures tracking to BadgeBatchGenerator"
```

---

### Task 11: Write new CLI tests (TDD — write before CLI rewrite)

**Files:**
- Modify: `tests/test_generate_badge_cli.py`

- [ ] **Step 1: Replace the file entirely**

The old tests import `validate_single_badge_args` and `validate_batch_badge_args`, which the Typer rewrite deletes. Replace the entire file:

```python
import json

import pytest
from typer.testing import CliRunner

from badgeshield.generate_badge_cli import app

runner = CliRunner(mix_stderr=False)


# ---------------------------------------------------------------------------
# single command
# ---------------------------------------------------------------------------

def test_single_happy_path(tmp_path):
    """Single badge generation with valid args should create the SVG file."""
    result = runner.invoke(app, [
        "single",
        "--left-text", "Build",
        "--left-color", "GREEN",
        "--badge-name", "build.svg",
        "--output-path", str(tmp_path),
    ])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "build.svg").exists()


def test_single_invalid_color(tmp_path):
    """An unrecognised color name should print an Error panel and exit 1."""
    result = runner.invoke(app, [
        "single",
        "--left-text", "Build",
        "--left-color", "NOTACOLOR",
        "--badge-name", "build.svg",
        "--output-path", str(tmp_path),
    ])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_single_missing_svg_suffix(tmp_path):
    """badge-name without .svg suffix must exit 1."""
    result = runner.invoke(app, [
        "single",
        "--left-text", "Build",
        "--left-color", "GREEN",
        "--badge-name", "no_suffix",
        "--output-path", str(tmp_path),
    ])
    assert result.exit_code == 1


def test_single_invalid_template(tmp_path):
    """An invalid template name must exit 1."""
    result = runner.invoke(app, [
        "single",
        "--left-text", "Build",
        "--left-color", "GREEN",
        "--badge-name", "build.svg",
        "--template", "BOGUS",
        "--output-path", str(tmp_path),
    ])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_single_invalid_frame(tmp_path):
    """An invalid frame name must exit 1."""
    result = runner.invoke(app, [
        "single",
        "--left-text", "Build",
        "--left-color", "GREEN",
        "--badge-name", "build.svg",
        "--template", "CIRCLE_FRAME",
        "--frame", "BADFRAME",
        "--output-path", str(tmp_path),
    ])
    assert result.exit_code == 1
    assert "Error" in result.output


# ---------------------------------------------------------------------------
# batch command
# ---------------------------------------------------------------------------

def test_batch_happy_path(tmp_path):
    """Batch with valid config JSON should create all SVG files."""
    config = [
        {"badge_name": "a.svg", "left_text": "alpha", "left_color": "#001122"},
        {"badge_name": "b.svg", "left_text": "beta", "left_color": "BLUE"},
    ]
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config))
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    result = runner.invoke(app, [
        "batch",
        str(config_file),
        "--output-path", str(out_dir),
    ])
    assert result.exit_code == 0, result.output
    assert (out_dir / "a.svg").exists()
    assert (out_dir / "b.svg").exists()


def test_batch_malformed_json(tmp_path):
    """Malformed JSON config must exit 1 with an error message."""
    config_file = tmp_path / "bad.json"
    config_file.write_text("{broken")

    result = runner.invoke(app, [
        "batch",
        str(config_file),
    ])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_batch_missing_config_file(tmp_path):
    """Non-existent config file path must exit 1 (Typer exists=True)."""
    result = runner.invoke(app, [
        "batch",
        str(tmp_path / "nonexistent.json"),
    ])
    assert result.exit_code != 0


def test_batch_circle_frame_without_frame(tmp_path):
    """CIRCLE_FRAME template without frame key in config must exit 1."""
    config = [
        {"badge_name": "f.svg", "left_text": "framed", "left_color": "#abcdef"},
    ]
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config))
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    result = runner.invoke(app, [
        "batch",
        str(config_file),
        "--template", "CIRCLE_FRAME",
        "--output-path", str(out_dir),
    ])
    assert result.exit_code == 1
```

- [ ] **Step 2: Run to confirm all tests FAIL (CLI still uses argparse)**
```bash
pytest tests/test_generate_badge_cli.py -v --tb=short
```
Expected: all new tests FAIL — `app` does not exist yet.

- [ ] **Step 3: Commit the failing tests**
```bash
git add tests/test_generate_badge_cli.py
git commit -m "test: add Typer CLI tests (failing — implementation pending)"
```

---

### Task 12: Rewrite `generate_badge_cli.py` with Typer + Rich

**Files:**
- Modify: `src/badgeshield/generate_badge_cli.py`

- [ ] **Step 1: Replace the entire file**

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table

from pylogshield import LogLevel

from .badge_generator import BadgeBatchGenerator, BadgeGenerator
from .utils import BadgeColor, BadgeTemplate, FrameType

app = typer.Typer(
    name="badgeshield",
    help="Generate customizable SVG badges.",
    add_completion=False,
)


def _error(message: str) -> None:
    """Print a Rich error panel to stdout."""
    rprint(Panel(message, title="Error", border_style="red"))


@app.command()
def single(
    left_text: str = typer.Option(..., help="Text for the left section"),
    left_color: str = typer.Option(
        ..., help="Hex (#RRGGBB) or BadgeColor name e.g. GREEN"
    ),
    badge_name: str = typer.Option(
        ..., help="Output filename, must end with .svg"
    ),
    template: str = typer.Option("DEFAULT", help="DEFAULT | CIRCLE | CIRCLE_FRAME"),
    output_path: Optional[str] = typer.Option(
        None, help="Output directory; defaults to current directory"
    ),
    right_text: Optional[str] = typer.Option(None),
    right_color: Optional[str] = typer.Option(None),
    logo: Optional[str] = typer.Option(None, help="Path to a logo image"),
    logo_tint: Optional[str] = typer.Option(
        None, help="Hex or BadgeColor name to tint the logo"
    ),
    frame: Optional[str] = typer.Option(
        None, help="Frame type — required for CIRCLE_FRAME template"
    ),
    left_link: Optional[str] = typer.Option(None),
    right_link: Optional[str] = typer.Option(None),
    id_suffix: str = typer.Option(""),
    left_title: Optional[str] = typer.Option(None),
    right_title: Optional[str] = typer.Option(None),
    log_level: str = typer.Option(
        "INFO", help="DEBUG | INFO | WARNING | ERROR | CRITICAL"
    ),
) -> None:
    """Generate a single SVG badge."""
    try:
        log_level_enum = LogLevel[log_level.upper()]
    except KeyError:
        _error(
            f"Invalid log_level '{log_level}'. "
            f"Choose from: {', '.join(l.name for l in LogLevel)}"
        )
        raise typer.Exit(1)

    try:
        template_enum = BadgeTemplate[template.upper()]
    except KeyError:
        _error(
            f"Invalid template '{template}'. "
            f"Choose from: {', '.join(t.name for t in BadgeTemplate)}"
        )
        raise typer.Exit(1)

    try:
        frame_enum = FrameType[frame.upper()] if frame else None
    except KeyError:
        _error(
            f"Invalid frame '{frame}'. "
            f"Choose from: {', '.join(f.name for f in FrameType)}"
        )
        raise typer.Exit(1)

    try:
        generator = BadgeGenerator(template=template_enum, log_level=log_level_enum)
        generator.generate_badge(
            left_text=left_text,
            left_color=left_color,
            badge_name=badge_name,
            output_path=output_path,
            right_text=right_text,
            right_color=right_color,
            logo=logo,
            frame=frame_enum,
            left_link=left_link,
            right_link=right_link,
            id_suffix=id_suffix,
            left_title=left_title,
            right_title=right_title,
            logo_tint=logo_tint,
        )
    except (ValueError, TypeError) as exc:
        _error(str(exc))
        raise typer.Exit(1)


@app.command()
def batch(
    config_file: Path = typer.Argument(
        ...,
        exists=True,
        help="Path to JSON config file containing badge definitions",
    ),
    output_path: Optional[str] = typer.Option(
        None, help="Output directory; defaults to current directory"
    ),
    template: str = typer.Option("DEFAULT", help="DEFAULT | CIRCLE | CIRCLE_FRAME"),
    log_level: str = typer.Option("INFO"),
    max_workers: int = typer.Option(4, help="Parallel worker threads"),
) -> None:
    """Batch-generate SVG badges from a JSON config file."""
    # --- Validate template ---
    try:
        template_enum = BadgeTemplate[template.upper()]
    except KeyError:
        _error(
            f"Invalid template '{template}'. "
            f"Choose from: {', '.join(t.name for t in BadgeTemplate)}"
        )
        raise typer.Exit(1)

    # --- Parse config ---
    try:
        badge_configs = json.loads(config_file.read_text(encoding="utf-8"))
        if not isinstance(badge_configs, list):
            _error("Config file must contain a JSON array of badge objects.")
            raise typer.Exit(1)
    except json.JSONDecodeError as exc:
        _error(f"Invalid JSON in config file: {exc}")
        raise typer.Exit(1)

    # --- Validate each badge entry has badge_name ---
    for entry in badge_configs:
        if "badge_name" not in entry or not entry["badge_name"].endswith(".svg"):
            _error(
                "Each badge entry must include a 'badge_name' ending with '.svg'."
            )
            raise typer.Exit(1)

    # --- Inject CLI-level template and output_path ---
    for badge in badge_configs:
        badge["template"] = template_enum
        if output_path is not None:
            badge["output_path"] = output_path

    # --- Run with Rich progress ---
    batch_gen = BadgeBatchGenerator(max_workers=max_workers, log_level=log_level)
    total = len(badge_configs)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
    ) as progress:
        task = progress.add_task("Generating badges...", total=total)

        try:
            batch_gen.generate_batch(
                badge_configs,
                progress_callback=lambda name: progress.advance(task),
            )
        except RuntimeError:
            pass  # failures surfaced via summary table

    # --- Print summary table ---
    table = Table(title="Batch Results", show_lines=True)
    table.add_column("Badge", style="cyan")
    table.add_column("Status")
    table.add_column("Error", style="red")

    failure_map = {name: err for name, err in batch_gen._failures}
    for badge in badge_configs:
        name = badge["badge_name"]
        if name in failure_map:
            table.add_row(name, "[red]✗ FAIL[/red]", failure_map[name])
        else:
            table.add_row(name, "[green]✓ OK[/green]", "")

    rprint(table)

    if batch_gen._failures:
        raise typer.Exit(1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the CLI tests**
```bash
pytest tests/test_generate_badge_cli.py -v --tb=short
```
Expected: all tests PASS.

- [ ] **Step 3: Smoke test the CLI manually**
```bash
python -m badgeshield single --help
python -m badgeshield batch --help
```
Expected: help text displays correctly with hyphenated flags.

- [ ] **Step 4: Run the full test suite**
```bash
pytest tests/ -v --tb=short
```
Expected: all tests pass.

- [ ] **Step 5: Commit**
```bash
git add src/badgeshield/generate_badge_cli.py
git commit -m "feat: rewrite CLI with Typer + Rich (progress bar, error panels, summary table)"
```

---

## Chunk 5: Additional Tests

### Task 13: Additional `test_badge_generator.py` coverage

**Files:**
- Modify: `tests/test_badge_generator.py`

- [ ] **Step 1: Add batch and template tests**

Append to `tests/test_badge_generator.py`:
```python
def test_batch_happy_path(output_dir):
    """Batch generation should create all submitted badge files."""
    batch_generator = BadgeBatchGenerator(max_workers=2)
    badges = [
        {
            "left_text": f"badge{i}",
            "left_color": "#44cc11",
            "badge_name": f"badge{i}.svg",
            "output_path": str(output_dir),
            "template": BadgeTemplate.DEFAULT,
        }
        for i in range(3)
    ]
    batch_generator.generate_batch(badges)
    for i in range(3):
        assert (output_dir / f"badge{i}.svg").exists()


def test_concurrent_batch_no_corruption(output_dir):
    """Concurrent batch with multiple workers must produce non-empty files."""
    batch_generator = BadgeBatchGenerator(max_workers=3)
    badges = [
        {
            "left_text": f"t{i}",
            "left_color": "#0000ff",
            "badge_name": f"t{i}.svg",
            "output_path": str(output_dir),
            "template": BadgeTemplate.DEFAULT,
        }
        for i in range(6)
    ]
    batch_generator.generate_batch(badges)
    for i in range(6):
        path = output_dir / f"t{i}.svg"
        assert path.exists()
        assert path.stat().st_size > 0


def test_circle_template_creates_svg_with_circle(output_dir):
    """CIRCLE template SVG must contain a <circle element."""
    generator = BadgeGenerator(template=BadgeTemplate.CIRCLE)
    generator.generate_badge(
        left_text="test",
        left_color="#123456",
        badge_name="circle.svg",
        output_path=str(output_dir),
    )
    content = (output_dir / "circle.svg").read_text()
    assert "<circle" in content


def test_circle_frame_with_valid_frame(output_dir):
    """CIRCLE_FRAME template with a valid FrameType must create the SVG."""
    generator = BadgeGenerator(template=BadgeTemplate.CIRCLE_FRAME)
    generator.generate_badge(
        left_text="framed",
        left_color="#abcdef",
        badge_name="framed.svg",
        output_path=str(output_dir),
        frame=FrameType.FRAME1,
    )
    assert (output_dir / "framed.svg").exists()


def test_circle_frame_without_frame_raises(output_dir):
    """CIRCLE_FRAME template without frame parameter must raise ValueError."""
    generator = BadgeGenerator(template=BadgeTemplate.CIRCLE_FRAME)
    with pytest.raises(ValueError, match="frame"):
        generator.generate_badge(
            left_text="framed",
            left_color="#abcdef",
            badge_name="framed.svg",
            output_path=str(output_dir),
        )


def test_badge_name_missing_svg_suffix(badge_generator, output_dir):
    """badge_name without .svg extension must raise ValueError."""
    with pytest.raises(ValueError, match=".svg"):
        badge_generator.generate_badge(
            left_text="test",
            left_color="#44cc11",
            badge_name="no_extension",
            output_path=str(output_dir),
        )


def test_get_base64_content_missing_file(badge_generator):
    """get_base64_content with a nonexistent file must raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        badge_generator.get_base64_content("/nonexistent/path/logo.png")


def test_logo_tinting_fallback_without_pillow(monkeypatch, output_dir):
    """Without Pillow, _load_logo_image returns plain base64 without error."""
    import badgeshield.badge_generator as badge_module

    logo_path = output_dir / "logo.png"
    # Write minimal valid PNG bytes
    logo_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82")

    monkeypatch.setattr(badge_module, "Image", None)

    generator = BadgeGenerator()
    result = generator._load_logo_image(str(logo_path), tint="#ff0000")
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0
```

- [ ] **Step 2: Run the new tests**
```bash
pytest tests/test_badge_generator.py -v --tb=short -k "test_batch_happy_path or test_concurrent or test_circle_template or test_circle_frame or test_badge_name or test_get_base64 or test_logo_tinting"
```
Expected: all PASS.

- [ ] **Step 3: Run the complete test suite**
```bash
pytest tests/ -v --tb=short
```
Expected: all tests pass.

- [ ] **Step 4: Commit**
```bash
git add tests/test_badge_generator.py
git commit -m "test: add batch, template, path traversal, logo tinting coverage"
```

---

## Final Verification

- [ ] **Run the full test suite one last time**
```bash
pytest tests/ -v
```
Expected: all tests pass, zero failures.

- [ ] **Verify the CLI end-to-end**
```bash
# Single badge
badgeshield single --left-text "Build" --left-color GREEN --badge-name build.svg --output-path /tmp

# Batch badge
echo '[{"badge_name":"a.svg","left_text":"alpha","left_color":"#001122"}]' > /tmp/cfg.json
badgeshield batch /tmp/cfg.json --output-path /tmp
```

- [ ] **Final commit**
```bash
git add .
git commit -m "chore: complete CLI modernization and code remediation"
```
