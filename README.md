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

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Coverage Badge](#-coverage-badge)
- [In-Memory Rendering](#-in-memory-rendering)
- [CLI Usage](#%EF%B8%8F-cli-usage)
- [Batch Generation](#-batch-generation)
- [Contributing](#-contributing)

---

## 📣 Overview

**BadgeShield** generates customizable SVG badges for GitLab, GitHub, and anywhere you can embed SVG. Three badge templates (rectangular, circle, framed-circle), 51 built-in colors, Pillow-powered font metrics, logo embedding with color tinting, automatic coverage badges from `coverage.xml`, and a Typer CLI with Rich progress bars.

---

## 💡 Features

- **3 templates** — `DEFAULT` (two-part rectangular), `CIRCLE`, and `CIRCLE_FRAME` with 11 PNG overlay frames.
- **51 built-in colors** — `BadgeColor` enum or any `#RRGGBB` hex string.
- **Accurate text sizing** — font widths measured via Pillow (DejaVuSans) with a fallback estimator when Pillow is absent.
- **Logo support** — embed PNG/JPEG logos with optional color tinting.
- **Coverage badge** — read `coverage.xml` and auto-generate a correctly-colored badge in one command.
- **In-memory rendering** — `render_badge()` returns a `BadgeSVG` string with `.to_bytes()`, `.to_data_uri()`, and `.save()` helpers.
- **Concurrent batch** — generate hundreds of badges in parallel from a JSON config.
- **Modern CLI** — Typer + Rich: progress bar, error panels, summary table.
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

### Python API — write to file

```python
from badgeshield import BadgeGenerator, BadgeTemplate

generator = BadgeGenerator(template=BadgeTemplate.DEFAULT)
generator.generate_badge(
    left_text="build",
    left_color="#555555",
    right_text="passing",
    right_color="#44cc11",
    badge_name="build.svg",
    output_path="./badges",
)
```

### Python API — in-memory

```python
from badgeshield import BadgeGenerator, BadgeSVG, BadgeTemplate

gen = BadgeGenerator(template=BadgeTemplate.DEFAULT)
svg: BadgeSVG = gen.render_badge(
    left_text="build",
    left_color="#555555",
    right_text="passing",
    right_color="#44cc11",
)

svg.to_bytes()       # b"<svg ..."
svg.to_data_uri()    # "data:image/svg+xml;base64,..."
svg.save("out.svg")  # write to disk
```

### Circle template

```python
from badgeshield import BadgeGenerator, BadgeTemplate

generator = BadgeGenerator(template=BadgeTemplate.CIRCLE)
generator.generate_badge(
    left_text="v2.1",
    left_color="#673ab7",
    badge_name="version.svg",
)
```

### Framed circle (CIRCLE_FRAME)

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

---

## 📊 Coverage Badge

Generate a correctly-colored badge directly from a `coverage.xml` report — no manual color selection needed.

### CLI

```bash
badgeshield coverage coverage.xml \
  --badge-name coverage.svg \
  --output-path ./badges
```

The color is chosen automatically using shields.io thresholds:

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

## 🧠 In-Memory Rendering

`render_badge()` returns a [`BadgeSVG`](https://vertex-ai-automations.github.io/badgeshield/reference/batch_generator/) string with no file written. Use it to serve badges over HTTP, inline them as data URIs, or inspect SVG content in tests.

```python
from badgeshield import BadgeGenerator, BadgeSVG, BadgeTemplate

gen = BadgeGenerator(template=BadgeTemplate.DEFAULT)
svg: BadgeSVG = gen.render_badge(
    left_text="coverage",
    left_color="#555555",
    right_text="94%",
    right_color="#44cc11",
)

# Serve over HTTP
response.body = svg.to_bytes()

# Inline in a web page
html = f'<img src="{svg.to_data_uri()}" alt="coverage 94%">'

# Test without touching the filesystem
assert "94%" in svg

# Write to disk when ready
svg.save("./badges/coverage.svg")
```

`render_badge()` accepts every parameter that `generate_badge()` does, except `badge_name` and `output_path`.

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
  --badge-name coverage.svg \
  --output-path ./badges
```

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
    "right_color": "#44cc11"
  },
  {
    "badge_name": "version.svg",
    "left_text": "v2.1.0",
    "left_color": "#673ab7"
  }
]
```

After the run, a Rich summary table shows which badges succeeded or failed.

### Python API

```python
from badgeshield import BadgeBatchGenerator, BadgeTemplate

batch = BadgeBatchGenerator(max_workers=4)
badges = [
    {"badge_name": "build.svg",    "left_text": "build",    "left_color": "GREEN",   "output_path": "./out", "template": BadgeTemplate.DEFAULT},
    {"badge_name": "coverage.svg", "left_text": "coverage", "left_color": "#555",    "right_text": "94%", "right_color": "#44cc11", "output_path": "./out", "template": BadgeTemplate.DEFAULT},
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
