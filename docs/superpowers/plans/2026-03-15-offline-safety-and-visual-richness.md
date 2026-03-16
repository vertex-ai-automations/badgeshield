# Offline Safety & Visual Richness Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make badgeshield verifiably air-gapped safe, add 4 style presets (FLAT/ROUNDED/GRADIENT/SHADOWED), a new `audit` CLI subcommand, and two new badge templates (PILL, BANNER).

**Architecture:** Phase 1 audits and eliminates all network calls and external SVG resource references, bundling the font and adding an `audit` CLI tool. Phase 2 adds a `BadgeStyle` enum that threads through the existing `_RENDERERS` dispatch, injecting SVG `<defs>` blocks conditionally in Jinja2 templates. New templates follow the exact same renderer registration pattern as existing ones.

**Tech Stack:** Python 3.8–3.12, Jinja2, Typer + Rich, Pillow (optional), stdlib `colorsys`, `xml.etree.ElementTree`, `importlib.resources`.

**Spec:** `docs/superpowers/specs/2026-03-15-badgeshield-offline-and-visual-design.md`

---

## File Map

| File | Role |
|------|------|
| `tests/conftest.py` | Add `block_network` fixture |
| `tests/fixtures/test_logo.png` | 1×1 transparent PNG for tests |
| `tests/snapshots/` | Committed baseline SVG snapshots |
| `tests/test_badge_generator.py` | New generation, style, font, snapshot tests |
| `tests/test_generate_badge_cli.py` | `TestAuditCommand` class, `--style` tests |
| `src/badgeshield/_logging.py` | stdlib logging wrapper (if pylogshield offends) |
| `src/badgeshield/fonts/DejaVuSans.ttf` | Bundled font |
| `src/badgeshield/utils.py` | Add `BadgeStyle` enum; add PILL/BANNER to `BadgeTemplate` |
| `src/badgeshield/badge_generator.py` | Font fix, style param, `_lighten_hex`, new renderers |
| `src/badgeshield/generate_badge_cli.py` | `audit` subcommand, `--style` on single/batch |
| `src/badgeshield/__init__.py` | Export `BadgeStyle` |
| `src/badgeshield/templates/label.svg` | Conditional gradient/shadow defs, `rx` variable |
| `src/badgeshield/templates/circle.svg` | Conditional radial gradient/shadow defs |
| `src/badgeshield/templates/circle_frame.svg` | Conditional shadow defs |
| `src/badgeshield/templates/pill.svg` | New — fully-rounded capsule |
| `src/badgeshield/templates/banner.svg` | New — 28px strip with icon zone |
| `pyproject.toml` | `package-data` for fonts |
| `requirements.txt` | Remove pylogshield if replaced |

---

## Chunk 1: Air-Gapped Safety

### Task 1: Offline Test Infrastructure

**Files:**
- Modify: `tests/conftest.py`
- Create: `tests/fixtures/test_logo.png`
- Modify: `tests/test_badge_generator.py`

- [ ] **Step 1: Add `block_network` fixture to conftest**

  Open `tests/conftest.py` and add:

  ```python
  @pytest.fixture
  def block_network(monkeypatch):
      import socket
      def blocked(*args, **kwargs):
          raise OSError("Network blocked by test fixture")
      monkeypatch.setattr(socket, "socket", blocked)
  ```

- [ ] **Step 2: Create the 1×1 transparent PNG fixture**

  Run this once to generate the file (requires Python with Pillow, or use raw bytes):

  ```python
  # Run in Python REPL or a one-off script
  import struct, zlib

  def make_1x1_png():
      # Minimal valid 1×1 RGBA PNG
      def chunk(name, data):
          c = struct.pack('>I', len(data)) + name + data
          return c + struct.pack('>I', zlib.crc32(name + data) & 0xffffffff)

      sig = b'\x89PNG\r\n\x1a\n'
      ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0))
      idat = chunk(b'IDAT', zlib.compress(b'\x00\x00\x00\x00\x00'))
      iend = chunk(b'IEND', b'')
      return sig + ihdr + idat + iend

  import os
  os.makedirs('tests/fixtures', exist_ok=True)
  with open('tests/fixtures/test_logo.png', 'wb') as f:
      f.write(make_1x1_png())
  ```

  Or more simply, in `tests/conftest.py` add a session-scoped fixture that writes it:

  ```python
  import struct, zlib
  from pathlib import Path

  @pytest.fixture(scope="session", autouse=True)
  def test_logo_fixture():
      """Create tests/fixtures/test_logo.png if it doesn't exist."""
      path = Path("tests/fixtures/test_logo.png")
      path.parent.mkdir(exist_ok=True)
      if not path.exists():
          def chunk(name, data):
              c = struct.pack('>I', len(data)) + name + data
              return c + struct.pack('>I', zlib.crc32(name + data) & 0xffffffff)
          sig = b'\x89PNG\r\n\x1a\n'
          ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0))
          idat = chunk(b'IDAT', zlib.compress(b'\x00\x00\x00\x00\x00'))
          iend = chunk(b'IEND', b'')
          path.write_bytes(sig + ihdr + idat + iend)
  ```

- [ ] **Step 3: Write failing SVG external-URL audit tests**

  Add to `tests/test_badge_generator.py`:

  ```python
  import re
  import pytest
  from badgeshield import BadgeGenerator, BadgeTemplate
  from badgeshield.utils import BadgeColor, FrameType

  LOGO_PATH = "tests/fixtures/test_logo.png"

  _SVG_AUDIT_PARAMS = [
      (
          BadgeTemplate.DEFAULT,
          dict(left_text="build", left_color=BadgeColor.GREEN,
               right_text="passing", right_color=BadgeColor.BLUE,
               logo=LOGO_PATH, left_link="#left", right_link="#right",
               badge_name="test.svg"),
      ),
      (
          BadgeTemplate.CIRCLE,
          dict(left_text="OK", left_color=BadgeColor.GREEN,
               logo=LOGO_PATH, left_link="#link", badge_name="test.svg"),
      ),
      (
          BadgeTemplate.CIRCLE_FRAME,
          dict(left_text="OK", left_color=BadgeColor.GREEN,
               frame=FrameType.FRAME1, logo=LOGO_PATH, badge_name="test.svg"),
      ),
  ]

  @pytest.mark.parametrize("template,kwargs", _SVG_AUDIT_PARAMS,
                           ids=["DEFAULT", "CIRCLE", "CIRCLE_FRAME"])
  def test_generated_svg_has_no_external_urls(template, kwargs, tmp_path):
      gen = BadgeGenerator(template=template)
      gen.generate_badge(output_path=str(tmp_path), **kwargs)
      svg_content = (tmp_path / "test.svg").read_text(encoding="utf-8")
      assert not re.search(r'https?://', svg_content), \
          f"Template {template} generated SVG with external URLs"
  ```

- [ ] **Step 4: Run tests to confirm they pass (they should — templates are clean)**

  ```bash
  pytest tests/test_badge_generator.py::test_generated_svg_has_no_external_urls -v
  ```

  Expected: 3 PASSED (templates have no external URLs). If any fail, inspect the offending URL before proceeding.

- [ ] **Step 5: Commit**

  ```bash
  git add tests/conftest.py tests/test_badge_generator.py
  git commit -m "test: add block_network fixture and SVG external-URL audit tests"
  ```

---

### Task 2: Network Audit & pylogshield Replacement

**Files:**
- Modify: `tests/test_badge_generator.py` (apply `block_network` fixture)
- Conditionally create: `src/badgeshield/_logging.py`
- Conditionally modify: `src/badgeshield/badge_generator.py`, `src/badgeshield/generate_badge_cli.py`, `src/badgeshield/__init__.py`, `requirements.txt`

- [ ] **Step 1: Apply `block_network` fixture to all generation tests**

  In `tests/test_badge_generator.py`, add at module level (applies to all test functions in the file):

  ```python
  pytestmark = pytest.mark.usefixtures("block_network")
  ```

  In `tests/test_generate_badge_cli.py`, add the same `pytestmark` line — but it will need to be scoped to exclude `TestAuditCommand` (see Task 4). For now, just add the module-level mark:

  ```python
  pytestmark = pytest.mark.usefixtures("block_network")
  ```

- [ ] **Step 2: Run the full test suite with the fixture applied**

  ```bash
  pytest tests/ -v --tb=short
  ```

  **Interpret results:**

  - **All pass** → no dependency makes network calls. Add this comment to `tests/conftest.py` (update the date):
    ```python
    # Network audit performed 2026-03-15: no dependency makes outbound calls.
    ```
    Skip to Task 3.

  - **Tests fail with "Network blocked by test fixture"** → record which tests and which import triggers the failure. If the traceback shows `pylogshield`, proceed with Step 3. If it's a different package, stop and review manually before continuing.

- [ ] **Step 3 (conditional — only if pylogshield offends): Identify ALL pylogshield import sites**

  Run:
  ```bash
  grep -rn "from pylogshield" src/
  ```

  You will find at minimum **two** files:
  - `src/badgeshield/badge_generator.py` — `from pylogshield import LogLevel, get_logger`
  - `src/badgeshield/generate_badge_cli.py` — `from pylogshield import LogLevel`

  Update **every** result. For `badge_generator.py`: `from ._logging import LogLevel, get_logger`. For `generate_badge_cli.py`: `from ._logging import LogLevel`.

- [ ] **Step 5 (conditional — only if pylogshield offends): Create `src/badgeshield/_logging.py`**

  ```python
  # src/badgeshield/_logging.py
  """stdlib logging wrapper — drop-in replacement for pylogshield."""
  import logging
  from enum import Enum
  from typing import Union


  class LogLevel(str, Enum):
      DEBUG = "DEBUG"
      INFO = "INFO"
      WARNING = "WARNING"
      ERROR = "ERROR"
      CRITICAL = "CRITICAL"


  def get_logger(name: str, log_level: Union[LogLevel, str]) -> logging.Logger:
      logger = logging.getLogger(name)
      level = log_level.value if isinstance(log_level, LogLevel) else log_level
      logger.setLevel(getattr(logging, level, logging.INFO))
      if not logger.handlers:
          handler = logging.StreamHandler()
          handler.setLevel(getattr(logging, level, logging.INFO))
          logger.addHandler(handler)
      return logger
  ```

- [ ] **Step 6 (conditional): Remove pylogshield from requirements.txt**

  Open `requirements.txt`, delete the `pylogshield` line.

- [ ] **Step 7: Run full test suite — all must pass**

  ```bash
  pytest tests/ -v --tb=short
  ```

  Expected: all tests PASS with no "Network blocked" failures.

- [ ] **Step 8: Commit**

  ```bash
  git add src/badgeshield/ requirements.txt tests/
  git commit -m "feat: audit network calls; replace pylogshield with stdlib logging wrapper"
  ```

  (If nothing was replaced, commit message: `"test: apply block_network fixture; confirm no outbound network calls"`)

---

### Task 3: Bundle DejaVuSans Font

**Files:**
- Create: `src/badgeshield/fonts/DejaVuSans.ttf`
- Modify: `src/badgeshield/badge_generator.py` — `_get_font()` method
- Modify: `pyproject.toml`
- Modify: `tests/test_badge_generator.py`

- [ ] **Step 1: Write a failing test for bundled font loading**

  Add to `tests/test_badge_generator.py`:

  ```python
  def test_get_font_uses_bundled_font(monkeypatch):
      """_get_font() must return the bundled DejaVuSans, not fall back to the default bitmap font."""
      from badgeshield.badge_generator import BadgeGenerator, ImageFont
      if ImageFont is None:
          pytest.skip("Pillow not installed")

      original_truetype = ImageFont.truetype

      def patched_truetype(path, size):
          import os
          # Allow only the bundled path; block all system paths
          if "badgeshield" in path and "fonts" in path:
              return original_truetype(path, size)
          raise OSError(f"Blocked system font path: {path}")

      monkeypatch.setattr(ImageFont, "truetype", patched_truetype)

      gen = BadgeGenerator()
      # Clear cached font to force a fresh load
      if hasattr(gen, "_badge_font"):
          del gen._badge_font

      font = gen._get_font()
      assert font is not None
      default_font = ImageFont.load_default()
      assert type(font) != type(default_font), \
          "_get_font() returned the fallback bitmap font instead of the bundled TrueType font"
  ```

- [ ] **Step 2: Run test to confirm it fails (font not bundled yet)**

  ```bash
  pytest tests/test_badge_generator.py::test_get_font_uses_bundled_font -v
  ```

  Expected: FAIL — OSError because DejaVuSans.ttf is not in `src/badgeshield/fonts/`.

- [ ] **Step 3: Copy the font file into the package**

  Try these in order until one succeeds:

  **Option A — via Pillow (most reliable):**
  ```bash
  python -c "
  from PIL import ImageFont
  import shutil, os
  try:
      f = ImageFont.truetype('DejaVuSans.ttf', 12)
      print(f.path)
  except OSError:
      # Pillow bundles fonts in its package directory
      import PIL
      pil_dir = os.path.dirname(PIL.__file__)
      candidates = []
      for root, dirs, files in os.walk(pil_dir):
          for fn in files:
              if fn == 'DejaVuSans.ttf':
                  candidates.append(os.path.join(root, fn))
      print(candidates)
  "
  ```

  **Option B — system font search (Linux/macOS):**
  ```bash
  find /usr -name "DejaVuSans.ttf" 2>/dev/null | head -1
  # or on macOS:
  find /Library -name "DejaVuSans.ttf" 2>/dev/null | head -1
  ```

  **Option C — download directly:**
  ```bash
  pip download DejaVu --no-deps -d /tmp/dejavu
  # Or obtain from https://dejavu-fonts.github.io/ and extract DejaVuSans.ttf
  ```

  Once you have the path, copy it:
  ```bash
  mkdir -p src/badgeshield/fonts
  cp <path-to-DejaVuSans.ttf> src/badgeshield/fonts/DejaVuSans.ttf
  ```

- [ ] **Step 4: Add `package-data` to `pyproject.toml`**

  Open `pyproject.toml`. After the existing `[tool.setuptools_scm]` section, add:

  ```toml
  [tool.setuptools.package-data]
  badgeshield = ["fonts/*.ttf"]
  ```

- [ ] **Step 5: Update `_get_font()` in `badge_generator.py`**

  Replace the existing `_get_font` method (currently around line 260) with:

  ```python
  def _get_font(self) -> Optional["ImageFont.ImageFont"]:
      """Return a lazily instantiated font object, preferring the bundled DejaVuSans."""
      if ImageFont is None:
          return None

      if not hasattr(self, "_badge_font"):
          try:
              import sys
              from pathlib import Path as _Path
              if sys.version_info >= (3, 9):
                  from importlib.resources import files
                  font_path = str(files("badgeshield") / "fonts" / "DejaVuSans.ttf")
              else:
                  font_path = str(_Path(__file__).parent / "fonts" / "DejaVuSans.ttf")
              self._badge_font = ImageFont.truetype(font_path, 110)
          except OSError:
              self._badge_font = ImageFont.load_default()
      return self._badge_font
  ```

- [ ] **Step 6: Run the font test — must pass**

  ```bash
  pytest tests/test_badge_generator.py::test_get_font_uses_bundled_font -v
  ```

  Expected: PASS.

- [ ] **Step 7: Run the full suite to confirm no regressions**

  ```bash
  pytest tests/ -v --tb=short
  ```

  Expected: all PASS.

- [ ] **Step 8: Commit**

  ```bash
  git add src/badgeshield/fonts/ src/badgeshield/badge_generator.py pyproject.toml tests/test_badge_generator.py
  git commit -m "feat: bundle DejaVuSans.ttf and load via importlib.resources"
  ```

---

### Task 4: `badgeshield audit` CLI Subcommand

**Files:**
- Modify: `src/badgeshield/generate_badge_cli.py`
- Modify: `tests/test_generate_badge_cli.py`

- [ ] **Step 1: Write failing tests for the `audit` subcommand**

  Open `tests/test_generate_badge_cli.py`. Remove the module-level `pytestmark` applied in Task 2 and instead apply it only to non-audit tests. Restructure the file so audit tests live in `TestAuditCommand`:

  At the top of `tests/test_generate_badge_cli.py`, change:

  ```python
  pytestmark = pytest.mark.usefixtures("block_network")
  ```

  To apply it per-class instead. Audit tests go in a class that does NOT use `block_network`:

  ```python
  # Apply block_network to all non-audit tests only (not TestAuditCommand)
  # Each non-audit test function should use @pytest.mark.usefixtures("block_network")
  # OR wrap non-audit tests in a class with pytestmark.
  ```

  The approach: wrap all existing CLI tests (single, batch, coverage) in a class named `TestCLICommands` with `pytestmark = pytest.mark.usefixtures("block_network")`. Move the existing `runner = CliRunner(mix_stderr=False)` inside that class as a class attribute. `conftest.py` fixtures (`badge_generator`, `output_dir`) remain accessible as method parameters — pytest finds them the same way whether tests are class-based or module-level.

  Then add `TestAuditCommand` without that mark. Audit tests use a plain `CliRunner()` (no `mix_stderr=False` needed — audit writes to stdout only):

  ```python
  from typer.testing import CliRunner
  from badgeshield.generate_badge_cli import app

  class TestCLICommands:
      """CLI tests for single, batch, coverage — network blocked."""
      pytestmark = pytest.mark.usefixtures("block_network")
      runner = CliRunner(mix_stderr=False)
      # ... all existing test methods moved here ...

  class TestAuditCommand:
      """audit subcommand tests — no block_network fixture (filesystem I/O only)."""

      runner = CliRunner()  # plain runner, no mix_stderr needed

      def test_audit_clean_svg(self, tmp_path):
          """A clean SVG (no external URLs) exits 0."""
          from badgeshield import BadgeGenerator, BadgeTemplate
          from badgeshield.utils import BadgeColor
          gen = BadgeGenerator(template=BadgeTemplate.DEFAULT)
          gen.generate_badge(
              left_text="build", left_color=BadgeColor.GREEN,
              badge_name="clean.svg", output_path=str(tmp_path),
          )
          result = self.runner.invoke(app, ["audit", str(tmp_path / "clean.svg")])
          assert result.exit_code == 0

      def test_audit_dirty_svg_exits_1(self, tmp_path):
          """An SVG with an external href exits 1 and reports the violation."""
          dirty = tmp_path / "dirty.svg"
          dirty.write_text(
              '<svg xmlns="http://www.w3.org/2000/svg">'
              '<image href="https://cdn.example.com/img.png"/>'
              '</svg>',
              encoding="utf-8",
          )
          result = self.runner.invoke(app, ["audit", str(dirty)])
          assert result.exit_code == 1
          assert "https://cdn.example.com/img.png" in result.output

      def test_audit_dirty_svg_json_output(self, tmp_path):
          """--json flag outputs machine-readable JSON."""
          import json
          dirty = tmp_path / "dirty.svg"
          dirty.write_text(
              '<svg xmlns="http://www.w3.org/2000/svg">'
              '<image href="https://cdn.example.com/img.png"/>'
              '</svg>',
              encoding="utf-8",
          )
          result = self.runner.invoke(app, ["audit", str(dirty), "--json"])
          assert result.exit_code == 1
          data = json.loads(result.output)
          assert data["clean"] is False
          assert len(data["violations"]) == 1
          assert data["violations"][0]["url"] == "https://cdn.example.com/img.png"

      def test_audit_nonexistent_file_exits_2(self, tmp_path):
          result = self.runner.invoke(app, ["audit", str(tmp_path / "nope.svg")])
          assert result.exit_code == 2

      def test_audit_malformed_xml_exits_2(self, tmp_path):
          bad = tmp_path / "bad.svg"
          bad.write_text("<not valid xml<<<", encoding="utf-8")
          result = self.runner.invoke(app, ["audit", str(bad)])
          assert result.exit_code == 2

      def test_audit_non_svg_root_exits_2(self, tmp_path):
          not_svg = tmp_path / "foo.xml"
          not_svg.write_text("<foo><bar/></foo>", encoding="utf-8")
          result = self.runner.invoke(app, ["audit", str(not_svg)])
          assert result.exit_code == 2

      def test_audit_style_url_violation(self, tmp_path):
          """External URL inside a style attribute url() is detected."""
          svg = tmp_path / "style_url.svg"
          svg.write_text(
              '<svg xmlns="http://www.w3.org/2000/svg">'
              '<rect style="fill:url(\'https://evil.com/grad\')"/>'
              '</svg>',
              encoding="utf-8",
          )
          result = self.runner.invoke(app, ["audit", str(svg)])
          assert result.exit_code == 1
  ```

- [ ] **Step 2: Run tests to confirm they fail (command doesn't exist yet)**

  ```bash
  pytest tests/test_generate_badge_cli.py::TestAuditCommand -v
  ```

  Expected: all FAIL with exit code mismatch or attribute errors.

- [ ] **Step 3: Implement the `audit` subcommand in `generate_badge_cli.py`**

  First, add `import re` to the top of `generate_badge_cli.py` (it is not currently imported). `json` and `xml.etree.ElementTree` are already imported (lines 2 and 4). Add near the other stdlib imports:

  ```python
  import re
  ```

  Then add the `audit` subcommand after the `coverage` subcommand. Use the already-imported names (`json`, `ET`, `Path`) — no new aliases needed:

  ```python
  @app.command()
  def audit(
      svg_file: Path = typer.Argument(..., help="Path to SVG file to audit"),
      json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
  ) -> None:
      """Audit an SVG file for external resource references."""
      try:
          tree = ET.parse(svg_file)
      except FileNotFoundError:
          _error(f"File not found: {svg_file}")
          raise typer.Exit(2)
      except ET.ParseError as exc:
          _error(f"XML parse error: {exc}")
          raise typer.Exit(2)

      root = tree.getroot()
      tag = root.tag
      if not (tag == "svg" or tag.endswith("}svg")):
          _error(f"Root element is <{tag}>, not <svg>. Not an SVG file.")
          raise typer.Exit(2)

      violations = []
      for elem in root.iter():
          for attr_name, attr_value in elem.attrib.items():
              if attr_value.startswith("http://") or attr_value.startswith("https://"):
                  violations.append({
                      "element": elem.tag,
                      "attribute": attr_name,
                      "url": attr_value,
                  })
              if attr_name == "style":
                  for match in re.findall(
                      r'url\(["\']?(https?://[^"\')\s]+)', attr_value
                  ):
                      violations.append({
                          "element": elem.tag,
                          "attribute": "style[url]",
                          "url": match,
                      })

      if json_output:
          typer.echo(json.dumps({"clean": len(violations) == 0, "violations": violations}))
      else:
          if not violations:
              rprint("[green]✓ Clean — no external resource references found.[/green]")
          else:
              table = Table(title="External URL Violations", show_lines=True)
              table.add_column("Element", style="cyan")
              table.add_column("Attribute", style="yellow")
              table.add_column("URL", style="red")
              for v in violations:
                  table.add_row(v["element"], v["attribute"], v["url"])
              rprint(table)

      if violations:
          raise typer.Exit(1)
  ```

- [ ] **Step 4: Run audit tests — all must pass**

  ```bash
  pytest tests/test_generate_badge_cli.py::TestAuditCommand -v
  ```

  Expected: all 7 PASS.

- [ ] **Step 5: Run the full suite**

  ```bash
  pytest tests/ -v --tb=short
  ```

  Expected: all PASS.

- [ ] **Step 6: Commit**

  ```bash
  git add src/badgeshield/generate_badge_cli.py tests/test_generate_badge_cli.py
  git commit -m "feat: add badgeshield audit CLI subcommand for SVG external-URL scanning"
  ```

---

## Chunk 2: Visual Richness

### Task 5: `BadgeStyle` Enum, `BadgeTemplate` Extensions, and `_lighten_hex`

**Files:**
- Modify: `src/badgeshield/utils.py`
- Modify: `src/badgeshield/badge_generator.py`
- Modify: `src/badgeshield/__init__.py`
- Modify: `tests/test_badge_generator.py`

- [ ] **Step 1: Write failing tests for `BadgeStyle`, new `BadgeTemplate` values, and `_lighten_hex`**

  Add to `tests/test_badge_generator.py`:

  ```python
  from badgeshield.utils import BadgeStyle

  class TestBadgeStyle:
      def test_badge_style_values_exist(self):
          assert BadgeStyle.FLAT.value == "flat"
          assert BadgeStyle.ROUNDED.value == "rounded"
          assert BadgeStyle.GRADIENT.value == "gradient"
          assert BadgeStyle.SHADOWED.value == "shadowed"

      def test_badge_style_exported_from_package(self):
          import badgeshield
          assert hasattr(badgeshield, "BadgeStyle")

      def test_pill_and_banner_in_badge_template(self):
          assert BadgeTemplate.PILL.value == "templates/pill.svg"
          assert BadgeTemplate.BANNER.value == "templates/banner.svg"


  class TestLightenHex:
      def test_black_lightens(self):
          from badgeshield.badge_generator import _lighten_hex
          assert _lighten_hex("#000000") == "#333333"

      def test_white_unchanged(self):
          from badgeshield.badge_generator import _lighten_hex
          assert _lighten_hex("#ffffff") == "#FFFFFF"

      def test_mid_tone(self):
          from badgeshield.badge_generator import _lighten_hex
          # Run once with UPDATE_SNAPSHOTS=1 to establish canonical value
          import os
          result = _lighten_hex("#4c1d95")
          if os.environ.get("UPDATE_SNAPSHOTS"):
              snapshot_path = "tests/snapshots/_lighten_hex_4c1d95.txt"
              os.makedirs("tests/snapshots", exist_ok=True)
              open(snapshot_path, "w").write(result)
          else:
              snapshot_path = "tests/snapshots/_lighten_hex_4c1d95.txt"
              if not os.path.exists(snapshot_path):
                  pytest.fail(
                      f"Snapshot missing: {snapshot_path}. "
                      "Run UPDATE_SNAPSHOTS=1 pytest to generate it."
                  )
              expected = open(snapshot_path).read().strip()
              assert result == expected
  ```

- [ ] **Step 2: Run to confirm failures**

  ```bash
  pytest tests/test_badge_generator.py::TestBadgeStyle tests/test_badge_generator.py::TestLightenHex -v
  ```

  Expected: all FAIL.

- [ ] **Step 3: Add `BadgeStyle` to `utils.py`**

  Open `src/badgeshield/utils.py`. After the `BadgeTemplate` class, add:

  ```python
  class BadgeStyle(str, Enum):
      """Visual style preset for badge rendering."""
      FLAT     = "flat"      # default — no visual change
      ROUNDED  = "rounded"   # 8px border-radius on rectangular corners
      GRADIENT = "gradient"  # gradient: left section lighter → base color
      SHADOWED = "shadowed"  # SVG feDropShadow filter
  ```

  Also add `PILL` and `BANNER` to `BadgeTemplate`. **Note:** `BadgeTemplate` is already `class BadgeTemplate(Enum)` (plain Enum, not `str, Enum`) in the existing code — no base-class change needed, just add the two new members:

  ```python
  class BadgeTemplate(Enum):
      DEFAULT      = "templates/label.svg"
      CIRCLE_FRAME = "templates/circle_frame.svg"
      CIRCLE       = "templates/circle.svg"
      PILL         = "templates/pill.svg"    # NEW
      BANNER       = "templates/banner.svg"  # NEW

      def __str__(self) -> str:
          return self.value
  ```

- [ ] **Step 4: Add `_lighten_hex` to `badge_generator.py`**

  At the top of `badge_generator.py`, add `import colorsys` to the stdlib imports. Then add this function just before the `BadgeBatchGenerator` class:

  ```python
  import colorsys

  def _lighten_hex(hex_color: str, factor: float = 0.2) -> str:
      """Return a lighter version of a hex color by increasing HSL lightness."""
      h = hex_color.lstrip("#")
      r, g, b = int(h[0:2], 16)/255, int(h[2:4], 16)/255, int(h[4:6], 16)/255
      hue, light, sat = colorsys.rgb_to_hls(r, g, b)  # colorsys uses HLS order
      light = min(1.0, light + factor * (1.0 - light))
      r2, g2, b2 = colorsys.hls_to_rgb(hue, light, sat)
      return "#{:02X}{:02X}{:02X}".format(round(r2 * 255), round(g2 * 255), round(b2 * 255))
  ```

- [ ] **Step 5: Export `BadgeStyle` from `__init__.py`**

  Open `src/badgeshield/__init__.py`. Add `BadgeStyle` to the import and `__all__`:

  ```python
  from .utils import BadgeColor, BadgeTemplate, FrameType, BadgeStyle

  __all__ = [
      "BadgeGenerator",
      "BadgeBatchGenerator",
      "BadgeColor",
      "BadgeTemplate",
      "BadgeStyle",       # NEW
      "FrameType",
      "LogLevel",
      "__version__",
      "coverage_color",
      "parse_coverage_xml",
  ]
  ```

- [ ] **Step 6: Generate the `_lighten_hex` snapshot for `#4c1d95`**

  ```bash
  UPDATE_SNAPSHOTS=1 pytest tests/test_badge_generator.py::TestLightenHex::test_mid_tone -v
  ```

  Then verify the value written to `tests/snapshots/_lighten_hex_4c1d95.txt` looks reasonable (should be a purple slightly lighter than `#4c1d95`).

- [ ] **Step 7: Run the tests — all must pass**

  ```bash
  pytest tests/test_badge_generator.py::TestBadgeStyle tests/test_badge_generator.py::TestLightenHex -v
  ```

  Expected: all PASS.

- [ ] **Step 8: Run full suite**

  ```bash
  pytest tests/ -v --tb=short
  ```

  Expected: all PASS.

- [ ] **Step 9: Commit**

  ```bash
  git add src/badgeshield/utils.py src/badgeshield/badge_generator.py src/badgeshield/__init__.py \
          tests/test_badge_generator.py tests/snapshots/
  git commit -m "feat: add BadgeStyle enum, PILL/BANNER to BadgeTemplate, and _lighten_hex helper"
  ```

---

### Task 6: Style Context Variables & Template Updates

**Files:**
- Modify: `src/badgeshield/badge_generator.py` — `_render_badge_content`, all `_render_*` methods
- Modify: `src/badgeshield/templates/label.svg`
- Modify: `src/badgeshield/templates/circle.svg`
- Modify: `src/badgeshield/templates/circle_frame.svg`
- Modify: `tests/test_badge_generator.py`

- [ ] **Step 1: Write failing style preset tests**

  Add to `tests/test_badge_generator.py`:

  ```python
  class TestBadgeStyleRendering:
      """Tests for ROUNDED, GRADIENT, SHADOWED style presets on existing templates."""

      def _generate_svg(self, template, style, tmp_path, **extra):
          gen = BadgeGenerator(template=template, style=style)
          gen.generate_badge(
              left_text="build", left_color=BadgeColor.GREEN,
              badge_name="test.svg", output_path=str(tmp_path), **extra
          )
          return (tmp_path / "test.svg").read_text(encoding="utf-8")

      def test_rounded_label_has_rx8(self, tmp_path):
          svg = self._generate_svg(BadgeTemplate.DEFAULT, BadgeStyle.ROUNDED, tmp_path)
          assert 'rx="8"' in svg

      def test_gradient_label_has_linear_gradient(self, tmp_path):
          svg = self._generate_svg(BadgeTemplate.DEFAULT, BadgeStyle.GRADIENT, tmp_path)
          assert "<linearGradient" in svg

      def test_gradient_circle_has_radial_gradient(self, tmp_path):
          svg = self._generate_svg(BadgeTemplate.CIRCLE, BadgeStyle.GRADIENT, tmp_path)
          assert "<radialGradient" in svg

      def test_shadowed_label_has_drop_shadow(self, tmp_path):
          svg = self._generate_svg(BadgeTemplate.DEFAULT, BadgeStyle.SHADOWED, tmp_path)
          assert "<feDropShadow" in svg

      def test_flat_style_no_gradient_no_shadow(self, tmp_path):
          svg = self._generate_svg(BadgeTemplate.DEFAULT, BadgeStyle.FLAT, tmp_path)
          assert "<linearGradient" not in svg
          assert "<feDropShadow" not in svg
          assert 'rx="8"' not in svg

      def test_style_defaults_to_flat(self, tmp_path):
          """BadgeGenerator without explicit style behaves like FLAT."""
          gen = BadgeGenerator(template=BadgeTemplate.DEFAULT)
          gen.generate_badge(
              left_text="x", left_color=BadgeColor.GREEN,
              badge_name="test.svg", output_path=str(tmp_path)
          )
          svg = (tmp_path / "test.svg").read_text(encoding="utf-8")
          assert "<linearGradient" not in svg
          assert "<feDropShadow" not in svg
  ```

- [ ] **Step 2: Run to confirm failures**

  ```bash
  pytest tests/test_badge_generator.py::TestBadgeStyleRendering -v
  ```

  Expected: all FAIL (style param doesn't exist yet).

- [ ] **Step 3: Update `BadgeGenerator.__init__` to accept `style`**

  In `badge_generator.py`, update `__init__`:

  ```python
  from .utils import BadgeColor, BadgeTemplate, FrameType, BadgeStyle  # add BadgeStyle

  def __init__(
      self,
      template: BadgeTemplate = BadgeTemplate.DEFAULT,
      log_level: Union[LogLevel, str] = LogLevel.WARNING,
      style: Optional["BadgeStyle"] = None,
  ) -> None:
      self.template_name = str(template)
      self.template_enum = template
      self._last_render_context: Optional[dict] = None
      self.style = style if style is not None else BadgeStyle.FLAT  # NEW
      self._setup_jinja2_env()
      self.logger = get_logger(name="badgeshield", log_level=log_level)
  ```

- [ ] **Step 4: Add `style` parameter to `_render_badge_content` and all `_render_*` methods**

  Update `_render_badge_content` signature to accept `style` as the last param and pass it to each renderer:

  ```python
  def _render_badge_content(
      self,
      left_text, left_color, right_text, right_color, logo, frame,
      left_link, right_link, id_suffix, left_title, right_title, logo_tint,
      style: "BadgeStyle",  # NEW — last param
  ) -> str:
      renderer = BadgeGenerator._RENDERERS.get(self.template_enum)
      if renderer is None:
          raise ValueError(f"No renderer registered for template {self.template_enum}")
      return renderer(
          self,
          left_text, left_color, right_text, right_color, logo, frame,
          left_link, right_link, id_suffix, left_title, right_title, logo_tint,
          style,  # NEW
      )
  ```

  Update `generate_badge` to pass `self.style`:

  ```python
  badge_content = self._render_badge_content(
      left_text, left_color_value, right_text, right_color_value,
      logo, frame, left_link, right_link, id_suffix,
      left_title, right_title, logo_tint,
      self.style,  # NEW
  )
  ```

  Add a helper method to compute style context variables (call from each renderer):

  ```python
  def _style_context(self, style: "BadgeStyle", left_color_hex: str, id_suffix: str) -> dict:
      """Compute Jinja2 context variables for the active style."""
      if style == BadgeStyle.ROUNDED:
          return dict(rx="8", gradient_id=None, gradient_stop=None,
                      gradient_base=None, shadow_id=None)
      if style == BadgeStyle.GRADIENT:
          return dict(rx="3",
                      gradient_id=f"grad{id_suffix}",
                      gradient_stop=_lighten_hex(left_color_hex),
                      gradient_base=left_color_hex,
                      shadow_id=None)
      if style == BadgeStyle.SHADOWED:
          return dict(rx="3", gradient_id=None, gradient_stop=None,
                      gradient_base=None, shadow_id=f"shadow{id_suffix}")
      # FLAT (default)
      return dict(rx="3", gradient_id=None, gradient_stop=None,
                  gradient_base=None, shadow_id=None)
  ```

  Update all three existing `_render_*` signatures to accept `style` as the last param and call `_style_context`:

  ```python
  def _render_default(self, left_text, left_color, right_text, right_color,
                      logo, frame, left_link, right_link, id_suffix,
                      left_title, right_title, logo_tint, style) -> str:
      style_ctx = self._style_context(style, left_color, id_suffix)
      # ... existing width/logo calculations ...
      context = dict(
          # ... existing keys ...
          **style_ctx,  # inject rx, gradient_id, gradient_stop, gradient_base, shadow_id
      )
      # ... rest of existing code ...
  ```

  Do the same for `_render_circle` and `_render_circle_frame`.

- [ ] **Step 5: Update `label.svg` to use style context variables**

  Open `src/badgeshield/templates/label.svg`. Add a `<defs>` section after the existing `<defs>` block (which currently only has `<clipPath>`). The complete updated `<defs>` section:

  ```svg
  <defs>
    <clipPath id="{{ id_round }}">
      <rect width="{{ total_width }}" height="20" rx="{{ rx }}" fill="#fff"/>
    </clipPath>
    {% if gradient_id %}
    <linearGradient id="{{ gradient_id }}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{{ gradient_stop }}"/>
      <stop offset="100%" stop-color="{{ gradient_base }}"/>
    </linearGradient>
    {% endif %}
    {% if shadow_id %}
    <filter id="{{ shadow_id }}">
      <feDropShadow dx="1" dy="1" stdDeviation="1" flood-opacity="0.3"/>
    </filter>
    {% endif %}
  </defs>
  ```

  Change the existing left rect fill and the outer clipPath rect's `rx` to use the `rx` variable. The left `<rect>`:

  ```svg
  <rect width="{{ left_width if right_text else total_width }}" height="20"
        fill="{% if gradient_id %}url(#{{ gradient_id }}){% else %}{{ left_color }}{% endif %}"
        {% if shadow_id %}filter="url(#{{ shadow_id }})"{% endif %}>
  ```

  Also change the clipPath `rx="3"` to `rx="{{ rx }}"`.

- [ ] **Step 6: Update `circle.svg` to use style context variables**

  Open `src/badgeshield/templates/circle.svg`. In the `<defs>` section, add after the existing `<clipPath>`:

  ```svg
  {% if gradient_id %}
  <radialGradient id="{{ gradient_id }}" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="{{ gradient_stop }}"/>
    <stop offset="100%" stop-color="{{ gradient_base }}"/>
  </radialGradient>
  {% endif %}
  {% if shadow_id %}
  <filter id="{{ shadow_id }}">
    <feDropShadow dx="1" dy="1" stdDeviation="1" flood-opacity="0.3"/>
  </filter>
  {% endif %}
  ```

  Update the main `<circle>` fill:

  ```svg
  <circle cx="50" cy="50" r="45"
    fill="{% if gradient_id %}url(#{{ gradient_id }}){% else %}{{ left_color }}{% endif %}"
    {% if shadow_id %}filter="url(#{{ shadow_id }})"{% endif %}/>
  ```

- [ ] **Step 7: Update `circle_frame.svg` to use shadow context variable**

  Open `src/badgeshield/templates/circle_frame.svg`. In the `<defs>` block, add the same conditional filter as `circle.svg`:

  ```svg
  {% if shadow_id %}
  <filter id="{{ shadow_id }}" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="2" dy="2" stdDeviation="2" flood-opacity="0.4"/>
  </filter>
  {% endif %}
  ```

  Add `{% if shadow_id %}filter="url(#{{ shadow_id }})"{% endif %}` to the main `<circle>` element (the background circle, not the frame `<image>`).

- [ ] **Step 8: Run style rendering tests — all must pass**

  ```bash
  pytest tests/test_badge_generator.py::TestBadgeStyleRendering -v
  ```

  Expected: all PASS.

- [ ] **Step 9: Run full suite**

  ```bash
  pytest tests/ -v --tb=short
  ```

  Expected: all PASS.

- [ ] **Step 10: Commit**

  ```bash
  git add src/badgeshield/badge_generator.py src/badgeshield/templates/ tests/test_badge_generator.py
  git commit -m "feat: add BadgeStyle rendering — ROUNDED, GRADIENT, SHADOWED presets on all templates"
  ```

---

### Task 7: Batch & CLI Style Integration

**Files:**
- Modify: `src/badgeshield/badge_generator.py` — `BadgeBatchGenerator._generate_single_badge`
- Modify: `src/badgeshield/generate_badge_cli.py` — `single` and `batch` subcommands
- Modify: `tests/test_generate_badge_cli.py`

- [ ] **Step 1: Write failing CLI style tests**

  In `tests/test_generate_badge_cli.py`, inside the non-audit test class, add:

  ```python
  def test_single_style_rounded(self, tmp_path):
      """--style ROUNDED produces rx="8" in output SVG."""
      result = self.runner.invoke(app, [
          "single", "--left_text", "x", "--left_color", "GREEN",
          "--badge_name", "out.svg", "--output_path", str(tmp_path),
          "--style", "ROUNDED",
      ])
      assert result.exit_code == 0
      svg = (tmp_path / "out.svg").read_text()
      assert 'rx="8"' in svg

  def test_single_style_invalid(self, tmp_path):
      """Invalid --style exits 1."""
      result = self.runner.invoke(app, [
          "single", "--left_text", "x", "--left_color", "GREEN",
          "--badge_name", "out.svg", "--output_path", str(tmp_path),
          "--style", "NEON",
      ])
      assert result.exit_code == 1

  def test_batch_per_entry_style_override(self, tmp_path):
      """Batch JSON 'style' key per-entry overrides the CLI --style default."""
      import json as _json
      config = tmp_path / "badges.json"
      config.write_text(_json.dumps([{
          "left_text": "x", "left_color": "GREEN",
          "badge_name": "out.svg", "style": "ROUNDED",
      }]))
      result = self.runner.invoke(app, [
          "batch", str(config), "--output_path", str(tmp_path),
          "--style", "FLAT",
      ])
      assert result.exit_code == 0
      svg = (tmp_path / "out.svg").read_text()
      assert 'rx="8"' in svg  # ROUNDED wins over FLAT default

  def test_batch_per_entry_invalid_style(self, tmp_path):
      """Batch JSON entry with invalid 'style' value exits 1 and reports error."""
      import json as _json
      config = tmp_path / "badges.json"
      config.write_text(_json.dumps([{
          "left_text": "x", "left_color": "GREEN",
          "badge_name": "out.svg", "style": "NEON",
      }]))
      result = self.runner.invoke(app, [
          "batch", str(config), "--output_path", str(tmp_path),
      ])
      assert result.exit_code == 1
  ```

- [ ] **Step 2: Run to confirm failures**

  ```bash
  pytest tests/test_generate_badge_cli.py -k "style" -v
  ```

  Expected: FAIL.

- [ ] **Step 3: Add `--style` to the `single` subcommand in `generate_badge_cli.py`**

  In the `single` function, add this parameter alongside the others:

  ```python
  style: str = typer.Option("FLAT", help="FLAT | ROUNDED | GRADIENT | SHADOWED"),
  ```

  Add validation — uses `.upper()` normalisation, consistent with all other enum CLI params (`template`, `frame`, `log_level`):

  ```python
  try:
      style_enum = BadgeStyle[style.upper()]
  except KeyError:
      _error(
          f"Invalid style '{style}'. "
          f"Choose from: {', '.join(s.name for s in BadgeStyle)}"
      )
      raise typer.Exit(1)
  ```

  Pass to `BadgeGenerator`:

  ```python
  generator = BadgeGenerator(template=template_enum, log_level=log_level_enum, style=style_enum)
  ```

- [ ] **Step 4: Add `--style` to the `batch` subcommand and per-entry style injection**

  In the `batch` function, add:

  ```python
  style: str = typer.Option("FLAT", help="FLAT | ROUNDED | GRADIENT | SHADOWED"),
  ```

  Validate the CLI-level style (same pattern as `single`). Then, after injecting `template` into each badge dict, inject style:

  ```python
  for badge in badge_configs:
      badge["template"] = template_enum
      if output_path is not None:
          badge["output_path"] = output_path
      # Per-entry style overrides CLI default
      if "style" in badge:
          try:
              badge["style"] = BadgeStyle[badge["style"].upper()]
          except KeyError:
              raise ValueError(f"Invalid style '{badge['style']}' in badge entry")
      else:
          badge["style"] = style_enum
  ```

- [ ] **Step 5: Add `style` param to `BadgeBatchGenerator._generate_single_badge`**

  In `badge_generator.py`, update `_generate_single_badge`:

  ```python
  def _generate_single_badge(
      self,
      left_text: str,
      left_color: BadgeColor,
      badge_name: str,
      template: Optional[BadgeTemplate] = BadgeTemplate.DEFAULT,
      output_path: Optional[str] = None,
      right_text: Optional[str] = None,
      right_color: Optional[BadgeColor] = None,
      logo: Optional[str] = None,
      frame: Optional[Union[FrameType, str]] = None,
      left_link: Optional[str] = None,
      right_link: Optional[str] = None,
      id_suffix: str = "",
      left_title: Optional[str] = None,
      right_title: Optional[str] = None,
      logo_tint: Optional[Union[str, BadgeColor]] = None,
      style: Optional["BadgeStyle"] = None,  # NEW
  ) -> None:
      generator = BadgeGenerator(template=template, log_level=self.log_level, style=style)
      generator.generate_badge(...)
  ```

- [ ] **Step 6: Also import `BadgeStyle` in `generate_badge_cli.py`**

  ```python
  from .utils import BadgeColor, BadgeTemplate, FrameType, BadgeStyle  # add BadgeStyle
  ```

- [ ] **Step 7: Run CLI style tests**

  ```bash
  pytest tests/test_generate_badge_cli.py -k "style" -v
  ```

  Expected: all PASS.

- [ ] **Step 8: Run full suite**

  ```bash
  pytest tests/ -v --tb=short
  ```

  Expected: all PASS.

- [ ] **Step 9: Commit**

  ```bash
  git add src/badgeshield/badge_generator.py src/badgeshield/generate_badge_cli.py \
          tests/test_generate_badge_cli.py
  git commit -m "feat: add --style option to single/batch CLI and batch per-entry style support"
  ```

---

### Task 8: PILL Template

**Files:**
- Create: `src/badgeshield/templates/pill.svg`
- Modify: `src/badgeshield/badge_generator.py` — add `_render_pill`, register in `_RENDERERS`
- Modify: `tests/test_badge_generator.py` — pill tests + snapshot

- [ ] **Step 1: Write failing pill tests**

  Add to `tests/test_badge_generator.py`:

  ```python
  import os

  class TestPillTemplate:
      def _generate_pill_svg(self, tmp_path, **kwargs):
          gen = BadgeGenerator(template=BadgeTemplate.PILL)
          defaults = dict(left_text="stable", left_color=BadgeColor.GREEN,
                          badge_name="pill.svg", output_path=str(tmp_path))
          defaults.update(kwargs)
          gen.generate_badge(**defaults)
          return (tmp_path / "pill.svg").read_text(encoding="utf-8")

      def test_pill_renders_without_error(self, tmp_path):
          svg = self._generate_pill_svg(tmp_path)
          assert "<svg" in svg

      def test_pill_height_is_20(self, tmp_path):
          svg = self._generate_pill_svg(tmp_path)
          assert 'height="20"' in svg

      def test_pill_has_rx_10(self, tmp_path):
          svg = self._generate_pill_svg(tmp_path)
          assert 'rx="10"' in svg

      def test_pill_rounded_style_is_noop(self, tmp_path):
          """ROUNDED style doesn't override pill's built-in rx=10."""
          gen = BadgeGenerator(template=BadgeTemplate.PILL, style=BadgeStyle.ROUNDED)
          gen.generate_badge(left_text="x", left_color=BadgeColor.GREEN,
                             badge_name="pill.svg", output_path=str(tmp_path))
          svg = (tmp_path / "pill.svg").read_text(encoding="utf-8")
          assert 'rx="10"' in svg
          assert 'rx="8"' not in svg

      def test_pill_gradient_style_applies(self, tmp_path):
          gen = BadgeGenerator(template=BadgeTemplate.PILL, style=BadgeStyle.GRADIENT)
          gen.generate_badge(left_text="x", left_color=BadgeColor.GREEN,
                             badge_name="pill.svg", output_path=str(tmp_path))
          svg = (tmp_path / "pill.svg").read_text(encoding="utf-8")
          assert "<linearGradient" in svg

      def test_pill_snapshot(self, tmp_path):
          svg = self._generate_pill_svg(tmp_path)
          snapshot_path = "tests/snapshots/pill_basic.svg"
          if os.environ.get("UPDATE_SNAPSHOTS"):
              os.makedirs("tests/snapshots", exist_ok=True)
              open(snapshot_path, "w", encoding="utf-8").write(svg)
          else:
              if not os.path.exists(snapshot_path):
                  pytest.fail(
                      f"Snapshot missing: {snapshot_path}. "
                      "Run UPDATE_SNAPSHOTS=1 pytest to generate it."
                  )
              assert svg == open(snapshot_path, encoding="utf-8").read()

      def test_pill_no_external_urls(self, tmp_path):
          import re
          svg = self._generate_pill_svg(tmp_path)
          assert not re.search(r'https?://', svg)
  ```

- [ ] **Step 2: Run to confirm failures**

  ```bash
  pytest tests/test_badge_generator.py::TestPillTemplate -v
  ```

  Expected: all FAIL.

- [ ] **Step 3: Create `src/badgeshield/templates/pill.svg`**

  ```svg
  {% set text_padding = 10 %}
  {% set id_round = 'pillround' + id_suffix %}
  <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
       width="{{ width }}" height="20"
       aria-label="{{ left_text }}" role="img">
    <title>{{ left_title if left_title else left_text }}</title>

    <defs>
      <clipPath id="{{ id_round }}">
        <rect width="{{ width }}" height="20" rx="10" fill="#fff"/>
      </clipPath>
      {% if gradient_id %}
      <linearGradient id="{{ gradient_id }}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="{{ gradient_stop }}"/>
        <stop offset="100%" stop-color="{{ gradient_base }}"/>
      </linearGradient>
      {% endif %}
      {% if shadow_id %}
      <filter id="{{ shadow_id }}">
        <feDropShadow dx="1" dy="1" stdDeviation="1" flood-opacity="0.3"/>
      </filter>
      {% endif %}
    </defs>

    <g clip-path="url(#{{ id_round }})">
      <rect width="{{ width }}" height="20"
            fill="{% if gradient_id %}url(#{{ gradient_id }}){% else %}{{ left_color }}{% endif %}"
            {% if shadow_id %}filter="url(#{{ shadow_id }})"{% endif %}/>
    </g>

    <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="110">
      {% if logo %}
      <image x="5" y="3" width="{{ logo_width }}" height="14"
             xlink:href="data:application/octet-stream;base64,{{ logo }}" alt="Logo"/>
      {% endif %}
      <text x="{{ (logo_width + logo_padding + (left_text_width / 2) + text_padding / 2) * 10 }}"
            y="150" fill="#010101" fill-opacity=".3" transform="scale(0.1)"
            textLength="{{ left_text_width * 10 }}" lengthAdjust="spacing">{{ left_text }}</text>
      <text x="{{ (logo_width + logo_padding + (left_text_width / 2) + text_padding / 2) * 10 }}"
            y="140" transform="scale(0.1)"
            textLength="{{ left_text_width * 10 }}" lengthAdjust="spacing">{{ left_text }}</text>
    </g>

    {% if left_link %}
    <a xlink:href="{{ left_link }}">
      <rect width="{{ width }}" height="20" fill="rgba(0,0,0,0)"/>
    </a>
    {% endif %}
  </svg>
  ```

- [ ] **Step 4: Add `_render_pill` to `badge_generator.py` and register it**

  Add after `_render_circle_frame`. **Arity note:** `_render_pill` must accept `style` as its 13th positional parameter after `self` — matching the dispatch convention established in Task 6 and consistent with all other `_render_*` methods.

  ```python
  def _render_pill(
      self, left_text, left_color, right_text, right_color, logo, frame,
      left_link, right_link, id_suffix, left_title, right_title, logo_tint,
      style,
  ) -> str:
      logo_data = self._load_logo_image(logo, logo_tint) if logo else None
      logo_width = 14 if logo else 0
      logo_padding = 3 if logo else 0
      text_padding = 10
      left_text_width = self._calculate_text_width(left_text)
      width = left_text_width + 2 * text_padding + logo_width + logo_padding

      style_ctx = self._style_context(style, left_color, id_suffix)
      # Pill always uses rx=10 — override rx from style context
      style_ctx["rx"] = "10"
      # gradient_id/shadow_id still apply; rx is not used in the pill template
      # (pill.svg hardcodes rx="10" on clipPath; style_ctx is injected for gradient/shadow)

      context = dict(
          left_text=left_text,
          left_color=left_color,
          left_text_width=left_text_width,
          logo=logo_data,
          logo_width=logo_width,
          logo_padding=logo_padding,
          left_link=left_link,
          left_title=left_title,
          width=width,
          id_suffix=id_suffix,
          **style_ctx,
      )
      self._last_render_context = context
      return self._get_template(self.template_name).render(**context)
  ```

  At the bottom of the file, update `_RENDERERS` — **add PILL only** (BANNER is added in Task 9 after `_render_banner` exists):

  ```python
  BadgeGenerator._RENDERERS = {
      BadgeTemplate.DEFAULT:      BadgeGenerator._render_default,
      BadgeTemplate.CIRCLE:       BadgeGenerator._render_circle,
      BadgeTemplate.CIRCLE_FRAME: BadgeGenerator._render_circle_frame,
      BadgeTemplate.PILL:         BadgeGenerator._render_pill,    # NEW
  }
  ```

- [ ] **Step 5: Run pill tests**

  ```bash
  pytest tests/test_badge_generator.py::TestPillTemplate -v
  ```

  Expected: all PASS except snapshot (missing file).

- [ ] **Step 6: Generate the pill snapshot**

  ```bash
  UPDATE_SNAPSHOTS=1 pytest tests/test_badge_generator.py::TestPillTemplate::test_pill_snapshot -v
  ```

  Verify `tests/snapshots/pill_basic.svg` was written and looks correct.

- [ ] **Step 7: Run pill tests again — all must pass**

  ```bash
  pytest tests/test_badge_generator.py::TestPillTemplate -v
  ```

  Expected: all PASS.

- [ ] **Step 8: Run full suite**

  ```bash
  pytest tests/ -v --tb=short
  ```

  Expected: all PASS.

- [ ] **Step 9: Commit**

  ```bash
  git add src/badgeshield/templates/pill.svg src/badgeshield/badge_generator.py \
          tests/test_badge_generator.py tests/snapshots/
  git commit -m "feat: add PILL template and _render_pill renderer"
  ```

---

### Task 9: BANNER Template

**Files:**
- Create: `src/badgeshield/templates/banner.svg`
- Modify: `src/badgeshield/badge_generator.py` — add `_render_banner`, finalize `_RENDERERS`
- Modify: `tests/test_badge_generator.py` — banner tests + snapshots

- [ ] **Step 1: Write failing banner tests**

  Add to `tests/test_badge_generator.py`:

  ```python
  class TestBannerTemplate:
      def _gen(self, tmp_path, **kwargs):
          gen = BadgeGenerator(template=BadgeTemplate.BANNER)
          defaults = dict(left_text="badgeshield", left_color=BadgeColor.BLUE,
                          badge_name="banner.svg", output_path=str(tmp_path))
          defaults.update(kwargs)
          gen.generate_badge(**defaults)
          return (tmp_path / "banner.svg").read_text(encoding="utf-8")

      def test_banner_renders(self, tmp_path):
          assert "<svg" in self._gen(tmp_path)

      def test_banner_height_28(self, tmp_path):
          svg = self._gen(tmp_path)
          assert 'height="28"' in svg

      def test_banner_right_text_no_rect(self, tmp_path):
          """right_text is rendered as text-only, no additional colored rect."""
          svg = self._gen(tmp_path, right_text="v1.0", right_color="#aaaaaa")
          # Should contain the right_text string somewhere
          assert "v1.0" in svg
          # Should NOT have a second rect element for the right section
          # (label.svg has 2 rects; banner should have only 1 background rect)
          import re
          rects = re.findall(r'<rect', svg)
          assert len(rects) == 1, "banner should have exactly 1 background rect"

      def test_banner_logo_clippath(self, tmp_path):
          """Logo zone includes a clipBanner clipPath."""
          svg = self._gen(tmp_path, logo=LOGO_PATH)
          assert "clipBanner" in svg
          assert "<clipPath" in svg

      def test_banner_shadow_style(self, tmp_path):
          gen = BadgeGenerator(template=BadgeTemplate.BANNER, style=BadgeStyle.SHADOWED)
          gen.generate_badge(left_text="x", left_color=BadgeColor.GREEN,
                             badge_name="banner.svg", output_path=str(tmp_path))
          svg = (tmp_path / "banner.svg").read_text(encoding="utf-8")
          assert "<feDropShadow" in svg

      def test_banner_snapshot_basic(self, tmp_path):
          svg = self._gen(tmp_path)
          snapshot_path = "tests/snapshots/banner_basic.svg"
          if os.environ.get("UPDATE_SNAPSHOTS"):
              os.makedirs("tests/snapshots", exist_ok=True)
              open(snapshot_path, "w", encoding="utf-8").write(svg)
          else:
              if not os.path.exists(snapshot_path):
                  pytest.fail(f"Snapshot missing: {snapshot_path}. Run UPDATE_SNAPSHOTS=1 pytest.")
              assert svg == open(snapshot_path, encoding="utf-8").read()

      def test_banner_snapshot_with_sublabel(self, tmp_path):
          svg = self._gen(tmp_path, right_text="v1.0", logo=LOGO_PATH)
          snapshot_path = "tests/snapshots/banner_with_sublabel.svg"
          if os.environ.get("UPDATE_SNAPSHOTS"):
              os.makedirs("tests/snapshots", exist_ok=True)
              open(snapshot_path, "w", encoding="utf-8").write(svg)
          else:
              if not os.path.exists(snapshot_path):
                  pytest.fail(f"Snapshot missing: {snapshot_path}. Run UPDATE_SNAPSHOTS=1 pytest.")
              assert svg == open(snapshot_path, encoding="utf-8").read()

      def test_banner_no_external_urls(self, tmp_path):
          import re
          svg = self._gen(tmp_path, logo=LOGO_PATH, right_text="v1.0")
          assert not re.search(r'https?://', svg)
  ```

- [ ] **Step 2: Run to confirm failures**

  ```bash
  pytest tests/test_badge_generator.py::TestBannerTemplate -v
  ```

  Expected: all FAIL.

- [ ] **Step 3: Create `src/badgeshield/templates/banner.svg`**

  ```svg
  {% set text_padding = 10 %}
  {% set effective_right_color = right_color if right_color else '#ffffff' %}
  {% set id_clip = 'clipBanner' + id_suffix %}

  <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
       width="{{ total_width }}" height="28"
       aria-label="{{ left_text }}" role="img">
    <title>{{ left_title if left_title else left_text }}</title>

    <defs>
      {% if logo %}
      <clipPath id="{{ id_clip }}">
        <circle cx="14" cy="14" r="10"/>
      </clipPath>
      {% endif %}
      {% if gradient_id %}
      <linearGradient id="{{ gradient_id }}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="{{ gradient_stop }}"/>
        <stop offset="100%" stop-color="{{ gradient_base }}"/>
      </linearGradient>
      {% endif %}
      {% if shadow_id %}
      <filter id="{{ shadow_id }}">
        <feDropShadow dx="1" dy="1" stdDeviation="1" flood-opacity="0.3"/>
      </filter>
      {% endif %}
    </defs>

    <!-- Background strip -->
    <rect width="{{ total_width }}" height="28" rx="{{ rx }}"
          fill="{% if gradient_id %}url(#{{ gradient_id }}){% else %}{{ left_color }}{% endif %}"
          {% if shadow_id %}filter="url(#{{ shadow_id }})"{% endif %}/>

    <!-- Optional logo in icon zone -->
    {% if logo %}
    <image x="4" y="4" width="20" height="20"
           xlink:href="data:application/octet-stream;base64,{{ logo }}"
           clip-path="url(#{{ id_clip }})"
           preserveAspectRatio="xMidYMid slice"/>
    {% endif %}

    <!-- Primary text -->
    <text x="{{ icon_zone_width + text_padding + left_text_width // 2 }}" y="18"
          font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="13"
          font-weight="bold" fill="#ffffff" text-anchor="middle">{{ left_text }}</text>

    <!-- Optional right sub-label (text color only, no rect) -->
    {% if right_text %}
    <text x="{{ icon_zone_width + left_text_width + 2 * text_padding + right_text_width // 2 }}" y="18"
          font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11"
          fill="{{ effective_right_color }}" text-anchor="middle">{{ right_text }}</text>
    {% endif %}

    {% if left_link %}
    <a xlink:href="{{ left_link }}">
      <rect width="{{ total_width }}" height="28" fill="rgba(0,0,0,0)"/>
    </a>
    {% endif %}
  </svg>
  ```

- [ ] **Step 4: Add `_render_banner` to `badge_generator.py` and finalize `_RENDERERS`**

  ```python
  def _render_banner(
      self, left_text, left_color, right_text, right_color, logo, frame,
      left_link, right_link, id_suffix, left_title, right_title, logo_tint,
      style,
  ) -> str:
      logo_data = self._load_logo_image(logo, logo_tint) if logo else None
      text_padding = 10
      icon_zone_width = 28 if logo else 0
      left_text_width = self._calculate_text_width(left_text)
      right_text_width = self._calculate_text_width(right_text) if right_text else 0
      total_width = (
          icon_zone_width
          + left_text_width
          + 2 * text_padding
          + right_text_width
          + (text_padding if right_text else 0)
      )
      style_ctx = self._style_context(style, left_color, id_suffix)
      context = dict(
          left_text=left_text,
          left_color=left_color,
          right_text=right_text,
          right_color=right_color,
          left_text_width=left_text_width,
          right_text_width=right_text_width,
          logo=logo_data,
          left_link=left_link,
          left_title=left_title,
          icon_zone_width=icon_zone_width,
          total_width=total_width,
          id_suffix=id_suffix,
          **style_ctx,
      )
      self._last_render_context = context
      return self._get_template(self.template_name).render(**context)
  ```

  Update `_RENDERERS` at the bottom of the file to include BANNER:

  ```python
  BadgeGenerator._RENDERERS = {
      BadgeTemplate.DEFAULT:      BadgeGenerator._render_default,
      BadgeTemplate.CIRCLE:       BadgeGenerator._render_circle,
      BadgeTemplate.CIRCLE_FRAME: BadgeGenerator._render_circle_frame,
      BadgeTemplate.PILL:         BadgeGenerator._render_pill,
      BadgeTemplate.BANNER:       BadgeGenerator._render_banner,
  }
  ```

- [ ] **Step 5: Run banner tests**

  ```bash
  pytest tests/test_badge_generator.py::TestBannerTemplate -v
  ```

  Expected: all pass except snapshots.

- [ ] **Step 6: Generate banner snapshots**

  ```bash
  UPDATE_SNAPSHOTS=1 pytest tests/test_badge_generator.py::TestBannerTemplate -k "snapshot" -v
  ```

  Verify both `tests/snapshots/banner_basic.svg` and `tests/snapshots/banner_with_sublabel.svg` are written.

- [ ] **Step 7: Run banner tests — all must pass**

  ```bash
  pytest tests/test_badge_generator.py::TestBannerTemplate -v
  ```

  Expected: all PASS.

- [ ] **Step 8: Extend the SVG external-URL parametrized test to include PILL and BANNER**

  In `tests/test_badge_generator.py`, add to `_SVG_AUDIT_PARAMS`:

  ```python
  _SVG_AUDIT_PARAMS = [
      # ... existing 3 entries ...
      (
          BadgeTemplate.PILL,
          dict(left_text="stable", left_color=BadgeColor.GREEN, badge_name="test.svg"),
      ),
      (
          BadgeTemplate.BANNER,
          dict(left_text="badgeshield", left_color=BadgeColor.BLUE,
               right_text="v1.0", badge_name="test.svg"),
      ),
  ]
  ```

  Update the `ids` list in `@pytest.mark.parametrize` to include `"PILL"` and `"BANNER"`.

- [ ] **Step 9: Run the full test suite — all must pass**

  ```bash
  pytest tests/ -v --tb=short
  ```

  Expected: all PASS.

- [ ] **Step 10: Commit**

  ```bash
  git add src/badgeshield/templates/banner.svg src/badgeshield/badge_generator.py \
          tests/test_badge_generator.py tests/snapshots/
  git commit -m "feat: add BANNER template and _render_banner renderer; extend audit tests to PILL/BANNER"
  ```

---

### Final Verification

- [ ] **Run the complete test suite one last time**

  ```bash
  pytest tests/ -v --tb=short
  ```

  Expected: all PASS, no warnings about external URLs.

- [ ] **Smoke-test the CLI**

  ```bash
  badgeshield single --left_text "Build" --left_color GREEN --right_text "passing" \
    --badge_name build.svg --style GRADIENT
  badgeshield single --left_text "stable" --left_color GREEN --badge_name pill.svg \
    --template PILL
  badgeshield audit build.svg
  ```

  Expected: badges generated without error, `audit` exits 0.

- [ ] **Final commit**

  ```bash
  git add .
  git commit -m "chore: final cleanup — offline safety and visual richness complete"
  ```
