<a name="readme-top"></a>

<div align="center">
<img src="https://github.com/vertex-ai-automations/badgeshield/raw/main/docs/img/badgeshield.png" alt="BadgeShield Logo" width="400">

<br/>

[![PyPI version](https://img.shields.io/pypi/v/badgeshield?color=673ab7&logo=pypi&logoColor=white)](https://pypi.org/project/badgeshield/)
[![Python versions](https://img.shields.io/pypi/pyversions/badgeshield?color=673ab7&logo=python&logoColor=white)](https://pypi.org/project/badgeshield/)
[![License: MIT](https://img.shields.io/badge/license-MIT-673ab7.svg)](https://github.com/vertex-ai-automations/badgeshield/blob/main/LICENSE.txt)
[![Downloads](https://img.shields.io/pypi/dm/badgeshield?color=673ab7)](https://pypi.org/project/badgeshield/)
[![CI](https://img.shields.io/github/actions/workflow/status/vertex-ai-automations/badgeshield/release.yml?branch=main&label=CI&logo=github)](https://github.com/vertex-ai-automations/badgeshield/actions)
[![Docs](https://img.shields.io/badge/docs-online-673ab7?logo=readthedocs&logoColor=white)](https://vertex-ai-automations.github.io/badgeshield)

<br/>

<p>
<a href="https://vertex-ai-automations.github.io/badgeshield"><strong>📃 Documentation</strong></a>
&nbsp;·&nbsp;
<a href="https://github.com/vertex-ai-automations/badgeshield/issues/new">🔧 Report Bug</a>
&nbsp;·&nbsp;
<a href="https://www.vertexaiautomations.com">⛪ Vertex AI Automations</a>
</p>

</div>

---

## Why badgeshield instead of shields.io?

shields.io is great — but it makes an HTTP call to an external server on every CI run.

**badgeshield generates badges entirely offline:**

- **No network calls** — works in air-gapped CI, behind corporate proxies, and offline laptops
- **No rate limits** — generate thousands of badges in a single run
- **No data sent externally** — your version numbers, branch names, and repo stats stay local
- **Reproducible** — same inputs always produce the same SVG, no caching surprises

```bash
# Generate every standard badge for your Python project in one command
badgeshield preset --all --output_path ./badges/ --format markdown
```

Drop the output straight into your README. No account needed, no tokens, no network.

---

## 📋 Table of Contents

- [Why badgeshield?](#why-badgeshield-instead-of-shieldsio)
- [Overview](#-overview)
- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Coverage Badge](#-coverage-badge)
- [CLI Usage](#%EF%B8%8F-cli-usage)
- [Batch Generation](#-batch-generation)
- [Contributing](#-contributing)

---

## 📣 Overview

**BadgeShield** generates customizable SVG badges for GitLab, GitHub, and anywhere you can embed SVG. Five badge templates, four visual styles, 51 built-in colors, Pillow-powered font metrics, logo embedding with color tinting, automatic coverage badges from `coverage.xml`, and a Typer CLI with Rich progress bars and an SVG audit subcommand.

---

## 💡 Features

- **5 templates** — `DEFAULT` (two-part rectangular), `PILL` (fully rounded), `CIRCLE`, `CIRCLE_FRAME` with 11 PNG overlay frames, and `BANNER` (icon-zone + text).
- **4 visual styles** — `FLAT`, `ROUNDED`, `GRADIENT`, and `SHADOWED` via `BadgeStyle` enum or `--style` CLI flag.
- **51 built-in colors** — `BadgeColor` enum or any `#RRGGBB` hex string.
- **Accurate text sizing** — font widths measured via Pillow (DejaVuSans) with a fallback estimator when Pillow is absent.
- **Logo support** — embed PNG/JPEG logos with optional color tinting.
- **Coverage badge** — read `coverage.xml` and auto-generate a correctly-colored badge in one command.
- **Concurrent batch** — generate hundreds of badges in parallel from a JSON config; per-entry `style` overrides the CLI flag.
- **Modern CLI** — Typer + Rich: progress bar, error panels, summary table, and `audit` subcommand.
- **Python API** — import and generate from any script or CI job.

---

## 📌 Installation

```bash
pip install badgeshield
```

With logo tinting support (requires Pillow):

```bash
pip install "badgeshield[image]"
```

Upgrade:

```bash
pip install --upgrade badgeshield
```

---

## 🚀 Quick Start

### Python API — DEFAULT template

```python
from badgeshield import BadgeGenerator, BadgeStyle, BadgeTemplate

generator = BadgeGenerator(template=BadgeTemplate.DEFAULT, style=BadgeStyle.GRADIENT)
generator.generate_badge(
    left_text="build",
    left_color="#555555",
    right_text="passing",
    right_color="#44cc11",
    badge_name="build.svg",
    output_path="./badges",
)
```

`style` is set at generator construction time and applies to all badges that instance generates. Options: `FLAT` (default), `ROUNDED`, `GRADIENT`, `SHADOWED`.

### PILL template

```python
from badgeshield import BadgeGenerator, BadgeTemplate

generator = BadgeGenerator(template=BadgeTemplate.PILL)
generator.generate_badge(
    left_text="build",
    left_color="#555555",
    right_text="passing",
    right_color="#44cc11",
    badge_name="build-pill.svg",
)
```

### CIRCLE template

```python
from badgeshield import BadgeGenerator, BadgeTemplate

generator = BadgeGenerator(template=BadgeTemplate.CIRCLE)
generator.generate_badge(
    left_text="v2.1",
    left_color="#673ab7",
    badge_name="version.svg",
)
```

### CIRCLE_FRAME template

```python
from badgeshield import BadgeGenerator, BadgeTemplate, FrameType

generator = BadgeGenerator(template=BadgeTemplate.CIRCLE_FRAME)
generator.generate_badge(
    left_text="MH",
    left_color="#FF0000",
    badge_name="initials.svg",
    frame=FrameType.FRAME1,
    logo="path/to/avatar.png",
    logo_tint="#ffffff",
)
```

### BANNER template

```python
from badgeshield import BadgeGenerator, BadgeTemplate

generator = BadgeGenerator(template=BadgeTemplate.BANNER)
generator.generate_badge(
    left_text="badgeshield",
    left_color="#1a1a2e",
    right_text="v1.0",
    right_color="#16213e",
    badge_name="banner.svg",
)
```

---

## 📊 Coverage Badge

Generate a correctly-colored badge directly from a `coverage.xml` report — no manual color selection needed.

### CLI

```bash
badgeshield coverage coverage.xml \
  --badge-name coverage.svg \
  --output-path ./badges
```

The color is chosen automatically based on these thresholds:

| Coverage | Color |
|----------|-------|
| ≥ 90% | ![#44cc11](https://img.shields.io/badge/-44cc11-44cc11) green |
| ≥ 80% | ![#97ca00](https://img.shields.io/badge/-97ca00-97ca00) yellow-green |
| ≥ 70% | ![#a4a61d](https://img.shields.io/badge/-a4a61d-a4a61d) yellow |
| ≥ 60% | ![#dfb317](https://img.shields.io/badge/-dfb317-dfb317) orange |
| < 60%  | ![#e05d44](https://img.shields.io/badge/-e05d44-e05d44) red |

Use `--metric branch` to badge on branch coverage instead of line coverage.

### Python API

```python
from badgeshield import parse_coverage_xml, coverage_color
from badgeshield import BadgeGenerator, BadgeTemplate

pct = parse_coverage_xml("coverage.xml")          # e.g. 94.3
color = coverage_color(pct)                        # "#44cc11"

gen = BadgeGenerator(template=BadgeTemplate.DEFAULT)
gen.generate_badge(
    left_text="coverage",
    left_color="#555555",
    right_text=f"{pct:.0f}%",
    right_color=color,
    badge_name="coverage.svg",
    output_path="./badges",
)
```

---

## 🖥️ CLI Usage

### Coverage badge

```bash
badgeshield coverage coverage.xml --badge-name coverage.svg --output-path ./badges
```

Use `--metric branch` for branch coverage, `--left-text` to change the label.

### Single badge

```bash
badgeshield single \
  --left-text "coverage" \
  --left-color "#555555" \
  --right-text "94%" \
  --right-color "#44cc11" \
  --style gradient \
  --badge-name coverage.svg \
  --output-path ./badges
```

`--style` accepts `flat` (default), `rounded`, `gradient`, or `shadowed` (case-insensitive).

With a logo and links:

```bash
badgeshield single \
  --left-text "build" \
  --left-color "DARK_GREEN" \
  --right-text "passing" \
  --right-color "#44cc11" \
  --logo path/to/logo.png \
  --logo-tint "#ffffff" \
  --left-link "https://example.com/pipeline" \
  --badge-name build.svg
```

Framed circle:

```bash
badgeshield single \
  --left-text "MH" \
  --left-color "#673ab7" \
  --template CIRCLE_FRAME \
  --frame FRAME1 \
  --badge-name initials.svg
```

### SVG audit

Verify that a generated SVG contains no external resource references:

```bash
badgeshield audit badges/build.svg          # exits 0 if clean, 1 if violations found
badgeshield audit badges/build.svg --json   # machine-readable JSON output
```

---

## ⚡ Batch Generation

### CLI

```bash
badgeshield batch badges.json --output-path ./badges --max-workers 8
```

### JSON config (`badges.json`)

```json
[
  {
    "badge_name": "build.svg",
    "left_text": "build",
    "left_color": "GREEN"
  },
  {
    "badge_name": "coverage.svg",
    "left_text": "coverage",
    "left_color": "#555555",
    "right_text": "94%",
    "right_color": "#44cc11",
    "style": "gradient"
  },
  {
    "badge_name": "version.svg",
    "left_text": "v2.1.0",
    "left_color": "#673ab7"
  }
]
```

A per-entry `"style"` key overrides the CLI `--style` flag for that badge.

After the run, a Rich summary table shows which badges succeeded or failed.

### Python API

```python
from badgeshield import BadgeBatchGenerator, BadgeStyle, BadgeTemplate

batch = BadgeBatchGenerator(max_workers=4)
badges = [
    {"badge_name": "build.svg",    "left_text": "build",    "left_color": "GREEN", "output_path": "./out", "template": BadgeTemplate.DEFAULT, "style": BadgeStyle.FLAT},
    {"badge_name": "coverage.svg", "left_text": "coverage", "left_color": "#555",  "right_text": "94%", "right_color": "#44cc11", "output_path": "./out", "template": BadgeTemplate.DEFAULT, "style": BadgeStyle.GRADIENT},
]

try:
    batch.generate_batch(badges, progress_callback=lambda name: print(f"✓ {name}"))
except RuntimeError:
    for badge_name, error in batch._failures:
        print(f"✗ {badge_name}: {error}")
```

---

## 👪 Contributing

All contributions are welcome. Fork the repo, make your changes, and open a pull request. You can also open an issue with the label `enhancement`.

Don't forget to ⭐ star the project!

🔶 [View all contributors](https://github.com/vertex-ai-automations/badgeshield/graphs/contributors)

---

📃 [Full Docs](https://vertex-ai-automations.github.io/badgeshield) &nbsp;·&nbsp; 🔧 [Report a Bug](https://github.com/vertex-ai-automations/badgeshield/issues/new) &nbsp;·&nbsp; ⛪ [Vertex AI Automations](https://www.vertexaiautomations.com)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
