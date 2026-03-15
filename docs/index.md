---
hide:
  - navigation
  - toc
---

<div class="hero" markdown>
<img src="img/badgeshield.png" alt="BadgeShield Logo">

**Generate beautiful, customizable SVG badges — from Python or the command line.**

[Get Started](installation.md){ .md-button .md-button--primary }
[View on GitHub](https://github.com/vertex-ai-automations/badgeshield){ .md-button }

</div>

---

<div align="center" markdown>

[![PyPI](https://img.shields.io/pypi/v/badgeshield?color=673ab7&logo=pypi&logoColor=white)](https://pypi.org/project/badgeshield/)
[![Python](https://img.shields.io/pypi/pyversions/badgeshield?color=673ab7&logo=python&logoColor=white)](https://pypi.org/project/badgeshield/)
[![License](https://img.shields.io/badge/license-MIT-673ab7.svg)](https://github.com/vertex-ai-automations/badgeshield/blob/main/LICENSE.txt)
[![Downloads](https://img.shields.io/pypi/dm/badgeshield?color=673ab7)](https://pypi.org/project/badgeshield/)
[![CI](https://img.shields.io/github/actions/workflow/status/vertex-ai-automations/badgeshield/release.yml?branch=main&label=CI&logo=github)](https://github.com/vertex-ai-automations/badgeshield/actions)

</div>

---

## Why BadgeShield?

BadgeShield gives you pixel-perfect SVG badges — rectangular, circle, or framed — with accurate text sizing powered by real font metrics. Drop it into a CI pipeline, a Python script, or call it from the terminal.

<div class="feature-grid" markdown>

<div class="feature-item" markdown>
<span class="feature-icon">🎨</span>
**3 Templates**

Choose `DEFAULT` (two-part horizontal), `CIRCLE`, or `CIRCLE_FRAME` with one of 11 PNG frame overlays.
</div>

<div class="feature-item" markdown>
<span class="feature-icon">🌈</span>
**51 Built-in Colors**

Use `BadgeColor` enum names like `GREEN` or `DARK_PURPLE`, or supply any `#RRGGBB` hex value.
</div>

<div class="feature-item" markdown>
<span class="feature-icon">📐</span>
**Accurate Text Sizing**

Text widths are measured with Pillow font metrics (DejaVuSans), not guesswork — badges always fit.
</div>

<div class="feature-item" markdown>
<span class="feature-icon">🖼️</span>
**Logo Support**

Embed any PNG/JPEG logo with optional color tinting to match your brand palette.
</div>

<div class="feature-item" markdown>
<span class="feature-icon">⚡</span>
**Concurrent Batch**

Generate hundreds of badges in parallel from a single JSON config using `BadgeBatchGenerator`.
</div>

<div class="feature-item" markdown>
<span class="feature-icon">🖥️</span>
**Modern CLI**

Typer-powered CLI with Rich progress bars, error panels, and a summary table after batch runs.
</div>

</div>

---

## Quick Look

=== "Python API"

    ```python
    from badgeshield import BadgeGenerator, BadgeTemplate

    generator = BadgeGenerator(template=BadgeTemplate.DEFAULT)
    generator.generate_badge(
        left_text="build",
        left_color="DARK_GREEN",
        right_text="passing",
        right_color="#44cc11",
        badge_name="build.svg",
    )
    ```

=== "CLI — single"

    ```bash
    badgeshield single \
      --left-text "coverage" \
      --left-color "#555555" \
      --right-text "94%" \
      --right-color "#44cc11" \
      --badge-name coverage.svg \
      --output-path ./badges
    ```

=== "CLI — batch"

    ```bash
    badgeshield batch badges.json --output-path ./badges
    ```

    `badges.json`:
    ```json
    [
      { "badge_name": "build.svg",    "left_text": "build",    "left_color": "GREEN" },
      { "badge_name": "coverage.svg", "left_text": "coverage", "left_color": "#555", "right_text": "94%", "right_color": "#44cc11" }
    ]
    ```

---

📖 Continue to [Installation](installation.md) or jump to the [Python API guide](getting-started/usage.md).
