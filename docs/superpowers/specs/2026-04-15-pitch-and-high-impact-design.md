# badgeshield — Pitch & High-Impact Features Design

**Date:** 2026-04-15  
**Status:** Approved  
**Scope:** Local data-aware badges, predefined presets, embed snippet output, docs pitch

---

## 1. Goal

Make badgeshield the obvious choice for Python developers who want README badges without calling shields.io. The pitch: **privacy + offline + reproducibility** — no external HTTP calls, no rate limits, no data sent to third parties, deterministic output in any CI environment.

---

## 2. Architecture

Three new modules are added. No changes to `badge_generator.py`.

```
src/badgeshield/
├── sources.py       # NEW — local data extraction
├── presets.py       # NEW — preset registry
├── badge_generator.py       (unchanged)
├── generate_badge_cli.py    (add preset subcommand, presets subcommand, --format flag)
├── coverage.py              (unchanged)
└── utils.py                 (unchanged)
```

Data flow:

```
CLI preset subcommand
  → presets.py      (looks up preset by name)
    → sources.py    (extracts value from local artifact)
      → BadgeGenerator  (renders SVG)
        → --format flag (optionally prints embed snippet to stdout)
```

---

## 3. `sources.py`

All functions are pure local operations — no network calls.

### 3.1 Version resolution chain

Tried in order, first non-empty non-`"unknown"` result wins:

1. `pyproject.toml` → `[project] version` (static) or `[tool.setuptools_scm]`
2. `setup.py` → `version=` kwarg — **regex parsed, never executed**  
   Pattern: `r'version\s*=\s*["\']([0-9][^"\']*)["\']'`  
   Only matches a quoted string literal. Dynamic forms (`version=get_version()`, `version=VERSION`) produce no match and fall through to step 3.
3. `_version.py` / `version.py` → `__version__ = "..."` — **regex parsed, never imported**  
   Pattern: `r'__version__\s*=\s*["\']([^"\']+)["\']'`
4. `git describe --tags --abbrev=0` — latest tag matching `X.Y.Z` via subprocess
5. Fallback → `"unknown"`

### 3.2 Public API

All functions accept `search_path: Path = Path(".")` and return `str`.

```python
# Package metadata (pyproject.toml → setup.py → version.py → git tag)
get_version(search_path)            # "1.2.3" or "unknown"
get_license(search_path)            # "MIT" or "unknown"
get_python_requires(search_path)    # ">=3.8" or "unknown"

# Git (subprocess, no network)
get_git_branch(search_path)         # "main"
get_git_tag(search_path)            # "v1.2.3" or "untagged"
get_git_commit_count(search_path)   # "142"
get_git_status(search_path)         # "clean" or "dirty"

# Lines of code
get_lines_of_code(
    search_path: Path = Path("."),
    extensions: tuple[str, ...] = (".py",),
) -> str  # "1,234" (comma-formatted)
# Excludes: __pycache__, .git, *.egg-info, dist, build, .tox, .venv, node_modules

# Test results (JUnit XML)
get_test_results(junit_xml: Path) -> str  # "47 passed" or "2 failed / 49"

# Coverage (wraps existing coverage.py)
get_coverage(coverage_xml: Path) -> str   # "82%" 
# Calls parse_coverage_xml(path, metric="line") and formats result as "{n}%"
```

### 3.3 Error behaviour

**Git functions:**
- Raise `RuntimeError` with a clear message if `git` is not on PATH (`FileNotFoundError` from `subprocess`).
- On any other subprocess failure (non-zero exit, not a git repo, no tags, shallow clone) — return `"unknown"` rather than raising. This ensures `preset --all` is not interrupted by a detached HEAD or a repo with no tags.
  - `get_git_tag` fallback: `"untagged"` (distinct from unknown — tag lookup ran but found nothing)
  - `get_git_status` fallback: `"unknown"` (never `"clean"` — returning `"clean"` on failure would be a false positive that bypasses the `--all` skip filter)

**Metadata functions (`get_version`, `get_license`, `get_python_requires`):**
- Return `"unknown"` on any parse failure. Never raise.

**`get_test_results`:**
- Raises `FileNotFoundError` if `junit_xml` does not exist.
- Raises `xml.etree.ElementTree.ParseError` on malformed XML.
- Raises `ValueError` if the XML root element is not a recognisable JUnit structure (no `testsuite` or `testcase` elements found).
- The CLI `preset tests` handler catches all three and exits with code 1 with a user-friendly message.

**`get_coverage`:**
- Raises `FileNotFoundError` if `coverage_xml` does not exist.
- Raises `ValueError` on unparseable coverage data (delegates to `parse_coverage_xml` behaviour).
- The CLI `preset coverage` handler catches both and exits with code 1.

**`get_lines_of_code`:**
- Never raises. Returns `"0"` if no files match the given extensions in the search path.
- `"0"` is a valid result and is included by `--all` (it is not a skip-filter value).

---

## 4. `presets.py`

### 4.1 Data structure

```python
@dataclass
class Preset:
    label: str                           # left_text
    color: Union[BadgeColor, str]        # left_color
    source: Optional[Callable] = None   # sources fn → right_text value; see §4.3 for protocol
    right_text: Optional[str] = None    # fixed value for cosmetic presets
    right_color: str = "#555555"
    description: str = ""
```

### 4.2 Full preset registry

Presets marked with `—` for right_text render as a single-section badge (label only, no right panel). All others produce a two-section badge.

| Name | Label | Source / Right text |
|------|-------|---------------------|
| `version` | version | `get_version` |
| `license` | license | `get_license` |
| `python` | python | `get_python_requires` |
| `branch` | branch | `get_git_branch` |
| `tag` | tag | `get_git_tag` |
| `commits` | commits | `get_git_commit_count` |
| `repo-status` | repo | `get_git_status` |
| `lines` | lines | `get_lines_of_code` |
| `tests` | tests | `get_test_results` |
| `coverage` | coverage | `get_coverage` |
| `black` | code style | fixed: "black" |
| `ruff` | linting | fixed: "ruff" |
| `flake8` | linting | fixed: "flake8" |
| `isort` | imports | fixed: "isort" |
| `mypy` | types | fixed: "mypy" |
| `passing` | build | fixed: "passing" |
| `failing` | build | fixed: "failing" |
| `stable` | status | fixed: "stable" |
| `wip` | status | fixed: "wip" |
| `alpha` | status | fixed: "alpha" |
| `beta` | status | fixed: "beta" |
| `rc` | status | fixed: "rc" |
| `experimental` | status | fixed: "experimental" |
| `maintained` | maintained | fixed: "maintained" |
| `deprecated` | deprecated | fixed: "deprecated" |
| `archived` | archived | fixed: "archived" |
| `library` | type | fixed: "library" |
| `cli` | type | fixed: "cli" |
| `framework` | type | fixed: "framework" |
| `api` | type | fixed: "api" |
| `contributions-welcome` | contributions | fixed: "welcome" |
| `hacktoberfest` | hacktoberfest | fixed: "hacktoberfest" |
| `cross-platform` | platform | fixed: "cross-platform" |
| `linux` | platform | fixed: "linux" |
| `windows` | platform | fixed: "windows" |
| `macos` | platform | fixed: "macos" |

### 4.3 Source callable protocol

`Preset.source` is typed as `Optional[Callable[[Path], str]]`. Every source function stored in the registry must conform to this signature: it accepts exactly one positional argument (`search_path: Path`) and returns a `str`.

For the three presets that require extra arguments, the CLI handler wraps them in a lambda before calling — bringing them into conformance with the uniform protocol:

```python
# Standard call (all search_path-only presets)
right_text = preset.source(search_path)

# tests preset — CLI wraps before dispatch
source = lambda p: get_test_results(junit_xml=junit_xml_path)
right_text = source(search_path)   # search_path is accepted but unused

# coverage preset — CLI wraps before dispatch
source = lambda p: get_coverage(coverage_xml=coverage_xml_path)
right_text = source(search_path)

# lines preset — CLI wraps before dispatch
source = lambda p: get_lines_of_code(search_path=p, extensions=extensions)
right_text = source(search_path)
```

This means `Preset.source` is **always** called as `source(search_path)`, with no exceptions. The wrapping is done at CLI dispatch time, not at registry definition time. Programmatic API users iterating `PRESETS` must apply the same wrapping for the three special-case presets, or call the underlying source functions directly with their required arguments.

---

## 5. CLI Changes

### 5.1 New `preset` subcommand

```bash
# Zero-config — badge_name defaults to {preset-name}.svg
badgeshield preset version
badgeshield preset lines --extensions .py .js
badgeshield preset tests --junit tests/junit.xml
badgeshield preset coverage --coverage_xml coverage.xml

# Override output name
badgeshield preset version --badge_name v.svg

# Generate all resolvable data-wired presets at once
badgeshield preset --all --output_path ./badges/ --format markdown

# Common flags
--output_path     Output directory (default: current directory)
--search_path     Repo root for source resolution (default: .)
--style           FLAT | ROUNDED | GRADIENT | SHADOWED
--format          markdown | rst | html (prints snippet to stdout)
--extensions      File extensions for lines-of-code (default: .py)
--junit           Path to JUnit XML for tests preset
--coverage_xml    Path to coverage.xml for coverage preset
```

**`--all` resolution policy:**
- Cosmetic (fixed) presets are always included.
- Data-wired presets are included only if their source returns a value other than `"unknown"` / `"untagged"`. Presets requiring an explicit path argument (`--junit`, `--coverage_xml`) are skipped when those flags are not provided.
- Skipped presets are listed in a Rich summary table after generation.
- If zero badges are written, exit with code 1 and print a diagnostic.

### 5.2 New `presets` subcommand

```bash
badgeshield presets   # prints Rich table of all preset names and descriptions
```

### 5.3 `--format` flag added to existing subcommands

Added to: `single`, `batch`, `coverage`, `preset`.

```bash
badgeshield preset version --format markdown
# output: ![version](./version.svg)

badgeshield preset version --format rst
# output: .. image:: ./version.svg
#            :alt: version

badgeshield preset version --format html
# output: <img src="./version.svg" alt="version" />

badgeshield batch config.json --format markdown
# output: one snippet per badge, printed to stdout
```

For `batch --format`, the alt text for each snippet is `left_text` from the batch config entry.

The SVG file is always written. The snippet is always printed to stdout (capturable with `>`).

### 5.4 Embed format implementation

Private helper in `generate_badge_cli.py` — no new module needed:

```python
def _format_snippet(svg_path: str, alt_text: str, fmt: str) -> str:
    match fmt:
        case "markdown":
            return f"![{alt_text}]({svg_path})"
        case "rst":
            return f".. image:: {svg_path}\n   :alt: {alt_text}"
        case "html":
            return f'<img src="{svg_path}" alt="{alt_text}" />'
        case _:
            raise ValueError(f"Unknown format {fmt!r}. Expected: markdown, rst, html")
```

The `--format` CLI option is typed as `Optional[str]` with Typer validation against the three allowed values, so the `case _` arm is a last-resort guard only.

---

## 6. Public API Additions (`__init__.py`)

```python
from .sources import (
    get_version, get_license, get_python_requires,
    get_git_branch, get_git_tag, get_git_commit_count, get_git_status,
    get_lines_of_code, get_test_results, get_coverage,
)
from .presets import PRESETS, Preset
```

---

## 7. Docs Updates

| File | Change |
|------|--------|
| `README.md` | New top section: "Why badgeshield?" — privacy/offline/reproducibility pitch + `badgeshield preset --all` quick-start |
| `docs/index.md` | Mirror the pitch from README |
| `docs/getting-started/cli_usage.md` | New `preset` and `presets` subcommand examples |
| `docs/getting-started/usage.md` | Programmatic API examples for `sources.py` |
| `docs/reference/sources.md` | New — API reference for all `sources.py` functions |
| `docs/reference/presets.md` | New — full preset table with descriptions |
| `mkdocs.yml` | Wire in `sources.md` and `presets.md` reference pages |

---

## 8. Testing Strategy

- **`tests/test_sources.py`**
  - One test per source function.
  - Version chain: **four isolated tests**, each using a `tmp_path` containing only the artifacts for that step (step 1: only `pyproject.toml`; step 2: only `setup.py`; step 3: only `version.py`; step 4: only a git repo with a tag). This ensures a bug in step 1 does not mask a broken step 3.
  - Git tests use `tmp_path` with `git init` + necessary commits/tags.
  - `get_test_results`: tests for valid XML, malformed XML (`ParseError`), non-JUnit XML (`ValueError`), and missing file (`FileNotFoundError`).
  - `get_lines_of_code`: tests that excluded dirs are skipped and that `extensions` filtering works.

- **`tests/test_presets.py`**
  - Every preset in the registry resolves without error.
  - Data-wired presets tested with fixture artifacts (`tmp_path` containing minimal `pyproject.toml`, git repo, etc.).
  - Cosmetic presets verified to produce non-empty `right_text`.

- **`tests/test_generate_badge_cli.py`** (extend existing)
  - `preset` subcommand: happy path, missing file args, unknown preset name.
  - `presets` subcommand: renders without error.
  - `--format` flag: all three formats produce correct snippet strings.
  - `preset --all`: happy path (some badges written).
  - `preset --all` all-data-wired-skip path: monkeypatch all `sources.*` functions to return `"unknown"`; verify cosmetic presets still render, skipped presets appear in summary table, exit code is 0 (cosmetic badges were written).
  - `preset --all` true-zero path: patch `PRESETS` with an empty dict; verify exit code 1 and diagnostic message. (Requires registry injection — use a `monkeypatch` fixture.)
  - `batch --format`: alt text is `left_text` from config.

---

## 9. Out of Scope

- Runtime HTTP calls of any kind.
- shields.io compatibility shim or URL format.
- Plugin system for third-party sources (can be added later).
- Writing snippets directly into README.md (inject/replace behaviour).
- Batch audit (`audit` subcommand remains single-file; running it against `--all` output is a manual step).
