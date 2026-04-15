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

Tried in order, first non-empty result wins:

1. `pyproject.toml` → `[project] version` (static) or `[tool.setuptools_scm]`
2. `setup.py` → `version=` kwarg — **regex parsed, never executed**
3. `_version.py` / `version.py` → `__version__ = "..."` — **regex parsed, never imported**
4. `git describe --tags --abbrev=0` — latest tag matching `X.Y.Z`
5. Fallback → `"unknown"`

### 3.2 Public API

All functions accept `search_path: Path = Path(".")` and return `str`.

```python
# Package metadata (pyproject.toml → setup.py → version.py → git tag)
get_version(search_path)           # "1.2.3" or "unknown"
get_license(search_path)           # "MIT" or "unknown"
get_python_requires(search_path)   # ">=3.8" or "unknown"

# Git (subprocess, no network)
get_git_branch(search_path)        # "main"
get_git_tag(search_path)           # "v1.2.3" or "untagged"
get_git_commit_count(search_path)  # "142"
get_git_status(search_path)        # "clean" or "dirty"

# Lines of code
get_lines_of_code(
    search_path: Path = Path("."),
    extensions: tuple[str, ...] = (".py",),
) -> str  # "1,234" (comma-formatted)
# Excludes: __pycache__, .git, *.egg-info, dist, build, .tox, .venv, node_modules

# Test results (JUnit XML)
get_test_results(junit_xml: Path) -> str  # "47 passed" or "2 failed / 49"
```

### 3.3 Error behaviour

- Git functions raise `RuntimeError` with a clear message if `git` is not on PATH.
- All other functions return `"unknown"` on parse failure — never raise.
- `get_test_results` raises `FileNotFoundError` if the XML path does not exist.

---

## 4. `presets.py`

### 4.1 Data structure

```python
@dataclass
class Preset:
    label: str                           # left_text
    color: Union[BadgeColor, str]        # left_color
    source: Optional[Callable] = None   # sources fn → right_text value
    right_text: Optional[str] = None    # fixed value for cosmetic presets
    right_color: str = "#555555"
    description: str = ""
```

### 4.2 Full preset registry

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
| `coverage` | coverage | `get_coverage` (delegates to existing `coverage.py`) |
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
| `maintained` | maintained | — |
| `deprecated` | deprecated | — |
| `archived` | archived | — |
| `library` | type | fixed: "library" |
| `cli` | type | fixed: "cli" |
| `framework` | type | fixed: "framework" |
| `api` | type | fixed: "api" |
| `contributions-welcome` | contributions | fixed: "welcome" |
| `hacktoberfest` | hacktoberfest | — |
| `cross-platform` | platform | fixed: "cross-platform" |
| `linux` | platform | fixed: "linux" |
| `windows` | platform | fixed: "windows" |
| `macos` | platform | fixed: "macos" |

---

## 5. CLI Changes

### 5.1 New `preset` subcommand

```bash
# Zero-config — badge_name defaults to {preset-name}.svg
badgeshield preset version
badgeshield preset lines --extensions .py .js
badgeshield preset tests --junit tests/junit.xml
badgeshield preset coverage --coverage-xml coverage.xml

# Override output name
badgeshield preset version --badge_name v.svg

# Generate all resolvable data-wired presets at once
badgeshield preset --all --output_path ./badges/ --format markdown

# Common flags (shared with other subcommands)
--output_path     Output directory (default: current directory)
--search-path     Repo root for source resolution (default: .)
--style           FLAT | ROUNDED | GRADIENT | SHADOWED
--format          markdown | rst | html (prints snippet to stdout)
--extensions      File extensions for lines-of-code (default: .py)
--junit           Path to JUnit XML for tests preset
--coverage-xml    Path to coverage.xml for coverage preset
```

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

The SVG file is always written. The snippet is always printed to stdout (capturable with `>`).

### 5.4 Embed format implementation

Private helper in `generate_badge_cli.py` — no new module needed:

```python
def _format_snippet(svg_path: str, alt_text: str, fmt: str) -> str:
    match fmt:
        case "markdown": return f"![{alt_text}]({svg_path})"
        case "rst":      return f".. image:: {svg_path}\n   :alt: {alt_text}"
        case "html":     return f'<img src="{svg_path}" alt="{alt_text}" />'
```

---

## 6. Public API Additions (`__init__.py`)

```python
from .sources import (
    get_version, get_license, get_python_requires,
    get_git_branch, get_git_tag, get_git_commit_count, get_git_status,
    get_lines_of_code, get_test_results,
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

- `tests/test_sources.py` — one test per source function; git tests use `tmp_path` with `git init`; version chain tests cover all four resolution steps
- `tests/test_presets.py` — every preset resolves without error; data-wired presets tested with fixture artifacts
- `tests/test_generate_badge_cli.py` — `preset`, `presets`, and `--format` flag tested via Typer's `CliRunner`
- Existing tests untouched

---

## 9. Out of Scope

- Runtime HTTP calls of any kind
- shields.io compatibility shim or URL format
- Plugin system for third-party sources (can be added later)
- Writing snippets directly into README.md (inject/replace behaviour)
