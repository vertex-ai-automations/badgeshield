---
title: BadgeShield Docs — "Badge Matrix" Redesign
date: 2026-04-17
status: approved
---

# BadgeShield Docs Modernization — Design Spec

## Overview

Modernize the MkDocs Material documentation site for badgeshield with a bold, dark-first "Badge Matrix" aesthetic. The audience is Python developers and CI/CD engineers who care about quality and visual craft. The redesign communicates that badgeshield produces beautiful output by being beautiful itself.

## Visual Design System

### Aesthetic Direction

**"Badge Matrix"** — editorial dark-first design inspired by product sites like Raycast, Linear, and Vercel docs. Near-black canvas with electric purple glows, cinematic depth through noise grain texture, and animated badge previews that showcase the actual product output.

### Color Palette

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--bs-bg` | `#ffffff` | `#07071a` | Page background |
| `--bs-bg-surface` | `#f5f4ff` | `#0e0d24` | Card / surface backgrounds |
| `--bs-bg-code` | `#f0eeff` | `#12112b` | Code block backgrounds |
| `--bs-purple` | `#7c3aed` | `#8b5cf6` | Primary brand color |
| `--bs-purple-glow` | `rgba(124,58,237,0.12)` | `rgba(139,92,246,0.15)` | Glow/shadow effects |
| `--bs-amber` | `#d97706` | `#f59e0b` | Accent (CTAs, highlights) |
| `--bs-fg` | `#1a1030` | `#e8e6ff` | Primary text |
| `--bs-fg-muted` | `#6b5fa0` | `#a39dd6` | Muted / secondary text (~5.2:1 on `#07071a`) |
| `--bs-border` | `rgba(124,58,237,0.15)` | `rgba(139,92,246,0.12)` | Borders |

### Typography

| Role | Font | Weight | Notes |
|------|------|--------|-------|
| Display / H1 | Syne | 800 | Google Fonts, geometric boldness |
| Headings H2–H4 | Syne | 700 | Same family, unified |
| Body | DM Sans | 400/500 | Readable, friendly, not generic |
| Code | Fira Code | 400 | Google Fonts, has ligatures, distinctive |

`mkdocs.yml` font config updated to `text: DM Sans`, `code: Fira Code`. Both available on Google Fonts. Syne loaded via `@import` in `extra.css` since Material only supports one text + one code font in config.

### Noise Grain Texture

A subtle SVG-based noise grain overlay (`::before` pseudo-element on `body`) at 3% opacity in dark mode, 1.5% in light. Creates atmospheric depth without performance cost.

---

## File Architecture

| File | Action | Purpose |
|------|--------|---------|
| `docs/css/extra.css` | Full rewrite | Design system, component styles, animations |
| `docs/js/extra.js` | Create new | Badge carousel, scroll reveals, typing effect |
| `docs/overrides/home.html` | Create new | Custom hero with animated badge showcase |
| `mkdocs.yml` | Update | Fonts, add `extra_javascript`, remove PLACEHOLDER note |

---

## Component Designs

### 1. Hero Section (`home.html` override)

`docs/overrides/home.html` uses Material's template inheritance pattern:
```jinja
{% extends "main.html" %}
{% block content %}
  <!-- custom hero HTML here -->
{% endblock %}
```

`docs/index.md` front matter must include `template: home.html` to activate the override. `mkdocs.yml` already has `custom_dir: docs/overrides` so no config change needed for the override directory.

Replaces the current basic Markdown hero with rich HTML:

- **Glowing orb**: Absolute-positioned radial gradient blob behind the logo, animating with `@keyframes pulse-glow` (scale + opacity)
- **Logo**: 160px, `filter: drop-shadow` with purple glow, subtle float animation
- **Headline**: 3.5rem Syne 800, gradient text purple→amber
- **Subheadline**: Typing effect cycling through use cases ("Generate build badges offline", "No shields.io API calls", "Concurrent batch generation")
- **CTAs**: Primary gradient button + ghost button, both with hover lift
- **Badge Carousel**: Live animated SVG badge previews (build/passing, coverage/94%, version/v1.2.0, license/MIT, status/stable) cycling with 2.5s transitions using CSS `opacity` + `transform`
- **PyPI badges row**: Current shields.io badges, centered, with subtle fade-in

### 2. Feature Cards

Glassmorphism treatment:
- Background: `rgba` surface color + `backdrop-filter: blur(12px)`
- Border: 1px `--bs-border` with `border-radius: 16px`
- Hover: `translateY(-4px)` + purple glow box-shadow + border brightens to `--bs-purple` at 40% opacity
- Icon: 2.5rem emoji in a purple-tinted circular background chip
- Scroll-reveal: `opacity: 0 → 1` + `translateY(20px → 0)` via Intersection Observer, staggered by card index

### 3. Code Blocks

Terminal window aesthetic:
- Fake title bar: `::before` pseudo with three colored dots (red `#ff5f57`, yellow `#ffbd2e`, green `#28ca41`) + language label on right
- Background: `--bs-bg-code` with left border `3px solid --bs-purple`
- Copy button: positioned top-right inside the terminal bar

### 4. Navigation / Header

- Header: `background: var(--bs-bg)` + `border-bottom: 1px solid --bs-border` + `backdrop-filter: blur(16px)`  
- Replaces current gradient header — cleaner, frosted glass feel
- Tabs: transparent background, active tab underlined with amber accent
- Search form: rounded, purple focus ring

### 5. Tables

- Rounded corners (12px), overflow hidden
- Header row: `--bs-purple` background, white text, Syne font
- Alternating row tint in light mode
- Box-shadow: `0 4px 24px var(--bs-purple-glow)`

### 6. Admonitions

- Border-left thickened to 4px
- Border-radius 12px
- Title font: Syne 700
- Note/tip types: purple-tinted; warning: amber-tinted

### 7. Footer

- Dark surface background matching `--bs-bg-surface`
- Top border: 1px `--bs-border`
- Social icons: hover lifts to `--bs-purple`

---

## JavaScript Behaviors (`docs/js/extra.js`)

### Badge Carousel
- Array of 5 hardcoded inline SVG strings (actual badgeshield-style output, 200px wide × 20px tall):
  1. `build | passing` — left `#555555`, right `#44cc11`
  2. `coverage | 94%` — left `#555555`, right `#44cc11`
  3. `version | v1.2.0` — left `#555555`, right `#7c3aed`
  4. `license | MIT` — left `#555555`, right `#007ec6`
  5. `status | stable` — left `#555555`, right `#0075ca`
- Each SVG is a two-rect badgeshield DEFAULT-template representation: left rect + right rect, 11px DejaVuSans-approximate text, `rx="3"` corners
- Cycles every 2500ms with CSS class toggle for fade transition
- No DOM manipulation beyond class swaps — CSS handles animation

### Scroll Reveal
- Single `IntersectionObserver` watching elements with `.reveal` class
- Threshold: 0.1 (10% visible triggers)
- Adds `.visible` class; CSS handles the transition (opacity + translateY)
- Elements: feature cards, section headings, code blocks, tables

### Typing Effect
- Pure JS, cycles through 3 tagline strings in the hero subtitle
- Writes character by character at 40ms/char, erases at 25ms/char
- 1800ms pause between phrases

### Stat Counter
- In scope. Animates 3 stats in the hero area (51 colors, 5 templates, 4 styles) counting up when scrolled into view
- Uses `requestAnimationFrame` with ease-out timing over 1200ms
- Markup: `<span class="stat-number" data-target="51">0</span>` pattern

---

## MkDocs Config Changes

```yaml
theme:
  font:
    text: DM Sans
    code: Fira Code

extra_css:
  - css/extra.css

extra_javascript:
  - js/extra.js
```

Home page (`docs/index.md`): keep front matter and PyPI badges row; the hero div is replaced by the `home.html` override block.

---

## Accessibility & Performance

- All animations respect `prefers-reduced-motion: reduce` — motion disabled, transitions set to `0.01ms`
- Typing effect paused when `prefers-reduced-motion` is set
- Color contrast maintained: all text against backgrounds ≥ 4.5:1
- Noise texture via inline SVG data URI — zero HTTP requests
- Fonts loaded via Google Fonts with `display=swap`

---

## Out of Scope

- Changing any MkDocs plugins or markdown extensions
- Modifying docs content (installation.md, API reference pages, etc.)
- Adding new nav pages
- Dark/light mode toggle behavior — keep existing Material toggle
