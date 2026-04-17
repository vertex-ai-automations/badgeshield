# BadgeShield Docs "Badge Matrix" Modernization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modernize the MkDocs documentation site with the "Badge Matrix" aesthetic — dark-first design, animated badge showcase hero, glassmorphic feature cards, terminal-style code blocks, scroll reveals, and a typing effect subtitle.

**Architecture:** Four files are touched: `mkdocs.yml` (fonts + JS registration), `docs/css/extra.css` (full rewrite with design tokens + all component styles), `docs/overrides/home.html` (new Jinja2 template override that prepends a rich HTML hero before the markdown content), and `docs/js/extra.js` (new file for badge carousel, scroll reveals, typing effect, stat counters). `docs/index.md` front matter is updated to activate the home template and the old Markdown hero div is removed.

**Tech Stack:** MkDocs Material theme, Jinja2 template overrides, vanilla CSS (custom properties, keyframe animations, Intersection Observer), vanilla JS (no dependencies)

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `mkdocs.yml` | Modify | Font config (DM Sans + Fira Code) + `extra_javascript` entry |
| `docs/css/extra.css` | Full rewrite | Design tokens, noise grain, all component styles, animation CSS |
| `docs/overrides/home.html` | Create | Jinja2 template — injects rich hero before page content |
| `docs/index.md` | Modify | Add `template: home.html` front matter; remove old hero div |
| `docs/js/extra.js` | Create | Badge carousel, scroll reveal, typing effect, stat counters |

---

## Task 1: Update `mkdocs.yml`

**Files:**
- Modify: `mkdocs.yml`

- [ ] **Step 1: Update the font block**

In `mkdocs.yml`, find the `font:` block under `theme:` (currently lines 39–41) and replace it:

```yaml
  font:
    text: DM Sans
    code: Fira Code
```

- [ ] **Step 2: Add `extra_javascript` entry**

`extra_css` already exists in `mkdocs.yml` (lines 183–184) — do **not** re-declare it. Add only the `extra_javascript` stanza immediately after the existing `extra_css` block:

```yaml
extra_javascript:
  - js/extra.js
```

The result in `mkdocs.yml` should read:

```yaml
extra_css:
  - css/extra.css

extra_javascript:
  - js/extra.js
```

- [ ] **Step 3: Verify build passes**

```bash
mkdocs build --strict 2>&1 | tail -20
```

Expected: exits 0, no errors. Warnings about git are fine.

- [ ] **Step 4: Commit**

```bash
git add mkdocs.yml
git commit -m "chore(docs): update fonts to DM Sans + Fira Code, register extra.js"
```

---

## Task 2: Rewrite `docs/css/extra.css`

**Files:**
- Modify: `docs/css/extra.css` (full replacement)

- [ ] **Step 1: Replace entire file with the new CSS**

Write the following as the complete contents of `docs/css/extra.css`:

```css
/* ═══════════════════════════════════════════════════════
   BadgeShield Docs — "Badge Matrix" Design System
   ═══════════════════════════════════════════════════════ */

/* ── Fonts ─────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;1,9..40,400&family=Fira+Code:wght@400;500&display=swap');

/* ── Design tokens — light ─────────────────────────────── */
:root {
  --bs-bg:           #ffffff;
  --bs-bg-surface:   #f5f4ff;
  --bs-bg-code:      #f0eeff;
  --bs-purple:       #7c3aed;
  --bs-purple-light: #a78bfa;
  --bs-purple-dark:  #5b21b6;
  --bs-purple-glow:  rgba(124, 58, 237, 0.12);
  --bs-amber:        #d97706;
  --bs-fg:           #1a1030;
  --bs-fg-muted:     #6b5fa0;
  --bs-border:       rgba(124, 58, 237, 0.15);

  /* Override Material tokens */
  --md-primary-fg-color:        #7c3aed;
  --md-primary-fg-color--light: #a78bfa;
  --md-primary-fg-color--dark:  #5b21b6;
  --md-accent-fg-color:         #d97706;
  --md-text-font:  "DM Sans", sans-serif;
  --md-code-font:  "Fira Code", monospace;
}

/* ── Design tokens — dark ──────────────────────────────── */
[data-md-color-scheme="slate"] {
  --bs-bg:           #07071a;
  --bs-bg-surface:   #0e0d24;
  --bs-bg-code:      #12112b;
  --bs-purple:       #8b5cf6;
  --bs-purple-light: #c4b5fd;
  --bs-purple-dark:  #6d28d9;
  --bs-purple-glow:  rgba(139, 92, 246, 0.15);
  --bs-amber:        #f59e0b;
  --bs-fg:           #e8e6ff;
  --bs-fg-muted:     #a39dd6;
  --bs-border:       rgba(139, 92, 246, 0.12);

  --md-default-bg-color:        #07071a;
  --md-default-fg-color:        #e8e6ff;
  --md-default-fg-color--light: #a39dd6;
  --md-code-bg-color:           #12112b;
  --md-primary-fg-color:        #8b5cf6;
  --md-primary-fg-color--dark:  #6d28d9;
}

/* ── Base ──────────────────────────────────────────────── */
html {
  scroll-behavior: smooth;
}

body {
  background-color: var(--bs-bg);
}

/* Noise grain overlay */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 9999;
  opacity: 0.015;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-size: 200px 200px;
}

[data-md-color-scheme="slate"] body::before {
  opacity: 0.03;
}

.md-grid {
  max-width: 1440px;
}

/* ── Typography — headings ─────────────────────────────── */
.md-typeset h1,
.md-typeset h2,
.md-typeset h3 {
  font-family: "Syne", sans-serif;
  letter-spacing: -0.02em;
}

.md-typeset h1 {
  font-weight: 800;
  font-size: 2rem;
}

.md-typeset h2 {
  font-weight: 700;
  border-bottom: 1px solid var(--bs-border);
  padding-bottom: 0.4rem;
}

/* ── Header ────────────────────────────────────────────── */
.md-header {
  background: var(--bs-bg);
  border-bottom: 1px solid var(--bs-border);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: none;
}

[data-md-color-scheme="slate"] .md-header {
  background: rgba(7, 7, 26, 0.85);
}

.md-header__title {
  font-family: "Syne", sans-serif;
  font-weight: 800;
  letter-spacing: -0.02em;
}

/* ── Navigation tabs ───────────────────────────────────── */
.md-tabs {
  background: transparent;
  border-bottom: 1px solid var(--bs-border);
  backdrop-filter: none;
}

.md-tabs__link {
  color: var(--bs-fg-muted);
  opacity: 1;
  font-family: "DM Sans", sans-serif;
  font-weight: 500;
  font-size: 0.85rem;
}

.md-tabs__link--active,
.md-tabs__link:hover {
  color: var(--bs-purple);
}

.md-tabs__link--active::after {
  background: var(--bs-amber);
  height: 2px;
}

/* ── Search ────────────────────────────────────────────── */
.md-search__form {
  border-radius: 8px;
  border: 1px solid var(--bs-border);
  background: var(--bs-bg-surface);
}

.md-search__form:focus-within {
  border-color: var(--bs-purple);
  box-shadow: 0 0 0 3px var(--bs-purple-glow);
}

/* ── Hero section (home.html override) ─────────────────── */
.bs-hero {
  position: relative;
  text-align: center;
  padding: 5rem 1.5rem 3.5rem;
  overflow: hidden;
}

.bs-hero__orb {
  position: absolute;
  top: -120px;
  left: 50%;
  transform: translateX(-50%);
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: radial-gradient(
    circle at center,
    var(--bs-purple-glow) 0%,
    rgba(124, 58, 237, 0.05) 50%,
    transparent 70%
  );
  pointer-events: none;
  animation: orb-pulse 6s ease-in-out infinite;
}

[data-md-color-scheme="slate"] .bs-hero__orb {
  background: radial-gradient(
    circle at center,
    rgba(139, 92, 246, 0.2) 0%,
    rgba(139, 92, 246, 0.08) 50%,
    transparent 70%
  );
}

@keyframes orb-pulse {
  0%, 100% { transform: translateX(-50%) scale(1);   opacity: 1;   }
  50%       { transform: translateX(-50%) scale(1.1); opacity: 0.7; }
}

.bs-hero__logo {
  position: relative;
  width: 120px;
  height: auto;
  filter: drop-shadow(0 8px 24px var(--bs-purple-glow));
  animation: logo-float 4s ease-in-out infinite;
  margin-bottom: 1.5rem;
}

@keyframes logo-float {
  0%, 100% { transform: translateY(0);    }
  50%       { transform: translateY(-8px); }
}

.bs-hero__title {
  font-family: "Syne", sans-serif;
  font-weight: 800;
  font-size: clamp(2rem, 5vw, 3.5rem);
  letter-spacing: -0.03em;
  line-height: 1.1;
  margin: 0 0 0.75rem;
  background: linear-gradient(135deg, var(--bs-purple) 0%, var(--bs-amber) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.bs-hero__subtitle {
  font-size: 1.15rem;
  color: var(--bs-fg-muted);
  max-width: 560px;
  margin: 0 auto 0.5rem;
  line-height: 1.7;
  min-height: 2em;
}

.bs-hero__cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: var(--bs-purple);
  vertical-align: text-bottom;
  margin-left: 2px;
  animation: cursor-blink 1s step-end infinite;
}

@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0; }
}

/* CTA buttons */
.bs-hero__ctas {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  flex-wrap: wrap;
  margin: 2rem 0;
}

/* Stats row */
.bs-stats {
  display: flex;
  gap: 2.5rem;
  justify-content: center;
  flex-wrap: wrap;
  margin: 1.5rem 0 2.5rem;
}

.bs-stat {
  text-align: center;
}

.bs-stat__number {
  font-family: "Syne", sans-serif;
  font-weight: 800;
  font-size: 2rem;
  color: var(--bs-purple);
  display: block;
  line-height: 1;
}

.bs-stat__label {
  font-size: 0.78rem;
  color: var(--bs-fg-muted);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

/* Badge carousel */
.bs-carousel {
  position: relative;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 2rem 0;
}

.bs-carousel__badge {
  position: absolute;
  opacity: 0;
  transform: translateY(8px) scale(0.95);
  transition: opacity 0.5s ease, transform 0.5s ease;
  transform-origin: center;
}

.bs-carousel__badge.bs-carousel__badge--active {
  opacity: 1;
  transform: translateY(0) scale(1.5);
}

/* PyPI shields row */
.bs-shields {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  flex-wrap: wrap;
  margin: 1rem 0 2rem;
  opacity: 0;
  animation: fade-in 0.6s ease 1.2s forwards;
}

@keyframes fade-in {
  to { opacity: 1; }
}

/* ── Buttons ────────────────────────────────────────────── */
.md-button {
  border-radius: 8px;
  font-family: "DM Sans", sans-serif;
  font-weight: 600;
  font-size: 0.9rem;
  text-transform: none;
  letter-spacing: 0.01em;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
  padding: 0.65em 1.5em;
}

.md-button--primary {
  background: linear-gradient(135deg, var(--bs-purple) 0%, var(--bs-purple-dark) 100%);
  border: none;
  box-shadow: 0 4px 20px var(--bs-purple-glow);
  color: #fff;
}

.md-button--primary:hover {
  background: linear-gradient(135deg, var(--bs-purple-light) 0%, var(--bs-purple) 100%);
  box-shadow: 0 8px 28px rgba(124, 58, 237, 0.35);
  transform: translateY(-2px);
  color: #fff;
}

.md-button:not(.md-button--primary) {
  border: 1px solid var(--bs-border);
  color: var(--bs-fg);
  background: transparent;
}

.md-button:not(.md-button--primary):hover {
  border-color: var(--bs-purple);
  color: var(--bs-purple);
  background: var(--bs-purple-glow);
  transform: translateY(-2px);
}

/* ── Feature grid ───────────────────────────────────────── */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.25rem;
  margin: 2.5rem 0;
}

.feature-item {
  background: var(--bs-bg-surface);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid var(--bs-border);
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}

.feature-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px var(--bs-purple-glow);
  border-color: rgba(124, 58, 237, 0.4);
}

[data-md-color-scheme="slate"] .feature-item:hover {
  border-color: rgba(139, 92, 246, 0.4);
}

.feature-item .feature-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 10px;
  background: var(--bs-purple-glow);
  font-size: 1.25rem;
  margin-bottom: 0.875rem;
}

.feature-item h3 {
  font-family: "Syne", sans-serif;
  font-weight: 700;
  font-size: 1rem;
  margin: 0 0 0.5rem;
  color: var(--bs-fg);
}

.feature-item p {
  margin: 0;
  font-size: 0.875rem;
  color: var(--bs-fg-muted);
  line-height: 1.65;
}

/* ── Code blocks ─────────────────────────────────────────── */
.highlight {
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  background: var(--bs-bg-code);
  border: 1px solid var(--bs-border);
}

/* Terminal title bar */
.highlight::before {
  content: '● ● ●';
  display: block;
  background: var(--bs-bg-surface);
  padding: 0.5rem 0.875rem;
  font-size: 0.6rem;
  letter-spacing: 0.2em;
  border-bottom: 1px solid var(--bs-border);
  color: transparent;
  text-shadow: 0 0 0 #ff5f57, 0.9em 0 0 #ffbd2e, 1.8em 0 0 #28ca41;
}

.highlight pre {
  margin: 0;
  padding: 1rem 1.25rem;
  border-left: 3px solid var(--bs-purple);
  background: var(--bs-bg-code);
}

.highlight code {
  font-family: "Fira Code", monospace;
  font-size: 0.84em;
  line-height: 1.7;
}

/* Inline code */
code:not(.highlight code) {
  background: var(--bs-bg-surface);
  border: 1px solid var(--bs-border);
  border-radius: 5px;
  padding: 0.15em 0.45em;
  font-size: 0.875em;
  font-family: "Fira Code", monospace;
}

/* ── Tables ──────────────────────────────────────────────── */
.md-typeset table:not([class]) {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 24px var(--bs-purple-glow);
  border: 1px solid var(--bs-border);
}

.md-typeset table:not([class]) th {
  background: var(--bs-purple);
  color: #fff;
  font-family: "Syne", sans-serif;
  font-weight: 700;
  letter-spacing: 0.01em;
  padding: 0.75rem 1rem;
}

[data-md-color-scheme="slate"] .md-typeset table:not([class]) th {
  background: var(--bs-purple-dark);
}

.md-typeset table:not([class]) tr:nth-child(even) td {
  background: var(--bs-bg-surface);
}

.md-typeset table:not([class]) td {
  padding: 0.65rem 1rem;
}

/* ── Admonitions ─────────────────────────────────────────── */
.admonition {
  border-radius: 12px;
  border-left-width: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.admonition-title {
  font-family: "Syne", sans-serif;
  font-weight: 700;
  font-size: 0.875rem;
}

.admonition.note,
.admonition.info,
.admonition.tip {
  border-left-color: var(--bs-purple);
}

.admonition.warning,
.admonition.caution {
  border-left-color: var(--bs-amber);
}

/* ── Tabbed content ──────────────────────────────────────── */
.md-typeset .tabbed-set {
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--bs-border);
}

.md-typeset .tabbed-labels {
  background: var(--bs-bg-surface);
  border-bottom: 1px solid var(--bs-border);
}

.md-typeset .tabbed-labels > label {
  font-family: "DM Sans", sans-serif;
  font-weight: 500;
  font-size: 0.85rem;
  color: var(--bs-fg-muted);
}

.md-typeset .tabbed-labels > label:hover {
  color: var(--bs-purple);
}

/* ── Footer ──────────────────────────────────────────────── */
.md-footer {
  background: var(--bs-bg-surface);
  border-top: 1px solid var(--bs-border);
}

.md-footer-meta {
  background: var(--bs-bg-surface);
}

.md-social__link svg {
  transition: fill 0.2s ease, transform 0.2s ease;
}

.md-social__link:hover svg {
  fill: var(--bs-purple);
  transform: translateY(-2px);
}

/* ── Sidebar / TOC ───────────────────────────────────────── */
.md-nav__link {
  font-size: 0.78rem;
  transition: color 0.15s ease;
}

.md-nav__link--active {
  color: var(--bs-purple);
  font-weight: 600;
}

/* ── Copy button ─────────────────────────────────────────── */
.md-clipboard {
  border-radius: 5px;
  transition: background 0.15s ease, color 0.15s ease;
}

.md-clipboard:hover {
  background: var(--bs-purple-glow);
  color: var(--bs-purple);
}

/* ── Inline badge labels ─────────────────────────────────── */
.badge {
  display: inline-block;
  padding: 0.2em 0.55em;
  font-size: 0.72em;
  font-weight: 700;
  border-radius: 4px;
  background: var(--bs-purple);
  color: #fff;
  margin-right: 0.4em;
  vertical-align: middle;
  letter-spacing: 0.03em;
  font-family: "DM Sans", sans-serif;
}

.badge--new     { background: #00c853; }
.badge--beta    { background: #f59e0b; }
.badge--changed { background: #2979ff; }

/* ── Scroll reveal ───────────────────────────────────────── */
.reveal {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.5s ease, transform 0.5s ease;
}

.reveal.visible {
  opacity: 1;
  transform: translateY(0);
}

/* Stagger delay by sibling index (applied via JS data-delay attribute) */
.reveal[data-delay="1"] { transition-delay: 0.1s; }
.reveal[data-delay="2"] { transition-delay: 0.2s; }
.reveal[data-delay="3"] { transition-delay: 0.3s; }
.reveal[data-delay="4"] { transition-delay: 0.4s; }
.reveal[data-delay="5"] { transition-delay: 0.5s; }
.reveal[data-delay="6"] { transition-delay: 0.6s; }

/* ── Reduced motion ──────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }

  .bs-hero__orb,
  .bs-hero__logo {
    animation: none;
  }

  .reveal {
    opacity: 1;
    transform: none;
    transition: none;
  }

  .bs-shields {
    opacity: 1;
    animation: none;
  }
}

/* ── Responsive ──────────────────────────────────────────── */
@media screen and (max-width: 60em) {
  .bs-hero {
    padding: 3rem 1rem 2rem;
  }

  .bs-hero__title {
    font-size: 2rem;
  }

  .bs-stats {
    gap: 1.5rem;
  }

  .feature-grid {
    grid-template-columns: 1fr;
  }
}

/* ── Print ───────────────────────────────────────────────── */
@media print {
  .md-header,
  .md-footer,
  .md-sidebar,
  .bs-hero__orb,
  body::before {
    display: none;
  }
}
```

- [ ] **Step 2: Verify build passes**

```bash
mkdocs build --strict 2>&1 | tail -20
```

Expected: exits 0, no CSS-related errors.

- [ ] **Step 3: Commit**

```bash
git add docs/css/extra.css
git commit -m "style(docs): rewrite extra.css — Badge Matrix design system"
```

---

## Task 3: Create `docs/overrides/home.html`

**Files:**
- Create: `docs/overrides/home.html`

This file uses Material's Jinja2 template system. The `custom_dir: docs/overrides` is already set in `mkdocs.yml`, so creating this file here will make it available as a page template.

- [ ] **Step 1: Create the file**

Write the following as `docs/overrides/home.html`:

```html
{% extends "main.html" %}

{% block content %}
<div class="bs-hero">
  <!-- Glowing orb background -->
  <div class="bs-hero__orb" aria-hidden="true"></div>

  <!-- Logo -->
  <img
    class="bs-hero__logo"
    src="{{ 'img/badgeshield_192x192.png' | url }}"
    alt="BadgeShield Logo"
    width="120"
    height="120"
  >

  <!-- Headline -->
  <h1 class="bs-hero__title">BadgeShield</h1>

  <!-- Typing subtitle -->
  <p class="bs-hero__subtitle">
    <span id="bs-typing-text"></span><span class="bs-hero__cursor" aria-hidden="true"></span>
  </p>

  <!-- CTAs -->
  <div class="bs-hero__ctas">
    <a href="{{ 'installation/' | url }}" class="md-button md-button--primary">
      Get Started
    </a>
    <a href="https://github.com/vertex-ai-automations/badgeshield" class="md-button">
      View on GitHub
    </a>
  </div>

  <!-- Animated badge carousel -->
  <div class="bs-carousel" aria-label="Badge examples" role="img">
    <div class="bs-carousel__badge bs-carousel__badge--active" id="bs-badge-0"></div>
    <div class="bs-carousel__badge" id="bs-badge-1"></div>
    <div class="bs-carousel__badge" id="bs-badge-2"></div>
    <div class="bs-carousel__badge" id="bs-badge-3"></div>
    <div class="bs-carousel__badge" id="bs-badge-4"></div>
  </div>

  <!-- Stat counters -->
  <div class="bs-stats">
    <div class="bs-stat">
      <span class="bs-stat__number stat-number" data-target="51">0</span>
      <span class="bs-stat__label">Colors</span>
    </div>
    <div class="bs-stat">
      <span class="bs-stat__number stat-number" data-target="5">0</span>
      <span class="bs-stat__label">Templates</span>
    </div>
    <div class="bs-stat">
      <span class="bs-stat__number stat-number" data-target="4">0</span>
      <span class="bs-stat__label">Styles</span>
    </div>
  </div>

  <!-- PyPI shields -->
  <div class="bs-shields">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/badgeshield?color=7c3aed&logo=pypi&logoColor=white">
    <img alt="Python" src="https://img.shields.io/pypi/pyversions/badgeshield?color=7c3aed&logo=python&logoColor=white">
    <img alt="License" src="https://img.shields.io/badge/license-MIT-7c3aed.svg">
    <img alt="Downloads" src="https://img.shields.io/pypi/dm/badgeshield?color=7c3aed">
    <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/vertex-ai-automations/badgeshield/release.yml?branch=main&label=CI&logo=github">
  </div>
</div>

<!-- Render the rest of the page markdown (feature grid, Quick Look, etc.) -->
{{ super() }}
{% endblock %}
```

- [ ] **Step 2: Verify the template renders without error**

```bash
mkdocs build --strict 2>&1 | grep -i "error\|warning\|home" | head -20
```

Expected: no Jinja2 template errors.

- [ ] **Step 3: Commit**

```bash
git add docs/overrides/home.html
git commit -m "feat(docs): add home.html template override with animated hero"
```

---

## Task 4: Update `docs/index.md`

**Files:**
- Modify: `docs/index.md`

Two changes: (1) add `template: home.html` to front matter to activate the override, and (2) remove the old `<div class="hero">` block since it is now rendered by `home.html`. Keep everything after the first `---` divider (PyPI badges row, feature grid, Quick Look tabs, etc.).

- [ ] **Step 1: Update the front matter**

Replace the existing front matter block:

```yaml
---
hide:
  - navigation
  - toc
---
```

with:

```yaml
---
template: home.html
hide:
  - navigation
  - toc
---
```

- [ ] **Step 2: Remove the old hero div**

Delete the following lines (the old hero section at the top of the file, after the front matter):

```html
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
```

The file should now start with the front matter, then the first `---` separator, then the `## Why BadgeShield?` heading.

- [ ] **Step 3: Add `.reveal` classes to feature items**

After the `<div class="feature-grid" markdown>` opening tag, add a `data-delay` attribute to each `<div class="feature-item">` for staggered scroll reveal. Replace each opening tag:

```html
<div class="feature-item" markdown>
```

with numbered versions:

```html
<div class="feature-item reveal" data-delay="1" markdown>
```
```html
<div class="feature-item reveal" data-delay="2" markdown>
```
...through `data-delay="7"` for all seven feature items.

- [ ] **Step 4: Build and verify**

```bash
mkdocs build --strict 2>&1 | tail -10
```

Expected: exits 0 cleanly.

- [ ] **Step 5: Commit**

```bash
git add docs/index.md
git commit -m "feat(docs): activate home.html template, remove old hero markup, add reveal classes"
```

---

## Task 5: Create `docs/js/extra.js`

**Files:**
- Create: `docs/js/extra.js`

All four JS behaviors in one file. The script runs on `DOMContentLoaded` and re-runs on MkDocs instant navigation events.

- [ ] **Step 1: Create the file**

Write the following as `docs/js/extra.js`:

```js
/* BadgeShield Docs — extra.js
   Badge carousel · Scroll reveal · Typing effect · Stat counters */

'use strict';

/* ── Badge SVG definitions ────────────────────────────── */
const BADGES = [
  // 1. build | passing
  `<svg xmlns="http://www.w3.org/2000/svg" width="90" height="20">
    <rect rx="3" width="90" height="20" fill="#555"/>
    <rect rx="3" x="37" width="53" height="20" fill="#44cc11"/>
    <rect x="37" width="4" height="20" fill="#44cc11"/>
    <g fill="#fff" font-family="DejaVu Sans,Verdana,sans-serif" font-size="11">
      <text x="5"  y="14" fill="#010101" fill-opacity=".25">build</text>
      <text x="4"  y="13">build</text>
      <text x="41" y="14" fill="#010101" fill-opacity=".25">passing</text>
      <text x="40" y="13">passing</text>
    </g>
  </svg>`,

  // 2. coverage | 94%
  `<svg xmlns="http://www.w3.org/2000/svg" width="96" height="20">
    <rect rx="3" width="96" height="20" fill="#555"/>
    <rect rx="3" x="60" width="36" height="20" fill="#44cc11"/>
    <rect x="60" width="4" height="20" fill="#44cc11"/>
    <g fill="#fff" font-family="DejaVu Sans,Verdana,sans-serif" font-size="11">
      <text x="5"  y="14" fill="#010101" fill-opacity=".25">coverage</text>
      <text x="4"  y="13">coverage</text>
      <text x="65" y="14" fill="#010101" fill-opacity=".25">94%</text>
      <text x="64" y="13">94%</text>
    </g>
  </svg>`,

  // 3. version | v1.2.0
  `<svg xmlns="http://www.w3.org/2000/svg" width="96" height="20">
    <rect rx="3" width="96" height="20" fill="#555"/>
    <rect rx="3" x="50" width="46" height="20" fill="#7c3aed"/>
    <rect x="50" width="4" height="20" fill="#7c3aed"/>
    <g fill="#fff" font-family="DejaVu Sans,Verdana,sans-serif" font-size="11">
      <text x="5"  y="14" fill="#010101" fill-opacity=".25">version</text>
      <text x="4"  y="13">version</text>
      <text x="55" y="14" fill="#010101" fill-opacity=".25">v1.2.0</text>
      <text x="54" y="13">v1.2.0</text>
    </g>
  </svg>`,

  // 4. license | MIT
  `<svg xmlns="http://www.w3.org/2000/svg" width="78" height="20">
    <rect rx="3" width="78" height="20" fill="#555"/>
    <rect rx="3" x="46" width="32" height="20" fill="#007ec6"/>
    <rect x="46" width="4" height="20" fill="#007ec6"/>
    <g fill="#fff" font-family="DejaVu Sans,Verdana,sans-serif" font-size="11">
      <text x="5"  y="14" fill="#010101" fill-opacity=".25">license</text>
      <text x="4"  y="13">license</text>
      <text x="51" y="14" fill="#010101" fill-opacity=".25">MIT</text>
      <text x="50" y="13">MIT</text>
    </g>
  </svg>`,

  // 5. status | stable
  `<svg xmlns="http://www.w3.org/2000/svg" width="92" height="20">
    <rect rx="3" width="92" height="20" fill="#555"/>
    <rect rx="3" x="44" width="48" height="20" fill="#0075ca"/>
    <rect x="44" width="4" height="20" fill="#0075ca"/>
    <g fill="#fff" font-family="DejaVu Sans,Verdana,sans-serif" font-size="11">
      <text x="5"  y="14" fill="#010101" fill-opacity=".25">status</text>
      <text x="4"  y="13">status</text>
      <text x="49" y="14" fill="#010101" fill-opacity=".25">stable</text>
      <text x="48" y="13">stable</text>
    </g>
  </svg>`,
];

/* ── Typing effect ─────────────────────────────────────── */
const TAGLINES = [
  'Generate build badges — fully offline.',
  'No shields.io API calls. No rate limits.',
  'Concurrent batch generation from JSON.',
];

let typingIndex  = 0;
let charIndex    = 0;
let isDeleting   = false;
let typingTimer  = null;

function runTyping() {
  const el = document.getElementById('bs-typing-text');
  if (!el) return;

  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReduced) {
    el.textContent = TAGLINES[0];
    return;
  }

  const current = TAGLINES[typingIndex];

  if (!isDeleting) {
    el.textContent = current.slice(0, charIndex + 1);
    charIndex++;
    if (charIndex === current.length) {
      isDeleting = true;
      typingTimer = setTimeout(runTyping, 1800);
      return;
    }
  } else {
    el.textContent = current.slice(0, charIndex - 1);
    charIndex--;
    if (charIndex === 0) {
      isDeleting = false;
      typingIndex = (typingIndex + 1) % TAGLINES.length;
    }
  }

  typingTimer = setTimeout(runTyping, isDeleting ? 25 : 40);
}

/* ── Badge carousel ────────────────────────────────────── */
let carouselIndex   = 0;
let carouselTimer   = null;

function initCarousel() {
  // Inject SVGs into placeholder divs
  BADGES.forEach((svg, i) => {
    const el = document.getElementById(`bs-badge-${i}`);
    if (el) el.innerHTML = svg;
  });
}

function rotateCarousel() {
  const items = document.querySelectorAll('.bs-carousel__badge');
  if (!items.length) return;

  items[carouselIndex].classList.remove('bs-carousel__badge--active');
  carouselIndex = (carouselIndex + 1) % items.length;
  items[carouselIndex].classList.add('bs-carousel__badge--active');

  carouselTimer = setTimeout(rotateCarousel, 2500);
}

/* ── Scroll reveal ─────────────────────────────────────── */
let revealObserver = null;

function initScrollReveal() {
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (prefersReduced) {
    document.querySelectorAll('.reveal').forEach(el => el.classList.add('visible'));
    return;
  }

  revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));
}

/* ── Stat counters ─────────────────────────────────────── */
function animateCounter(el, target, duration) {
  const start      = performance.now();
  const startValue = 0;

  function update(now) {
    const elapsed  = now - start;
    const progress = Math.min(elapsed / duration, 1);
    // ease-out cubic
    const eased    = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(startValue + (target - startValue) * eased);
    if (progress < 1) requestAnimationFrame(update);
  }

  requestAnimationFrame(update);
}

function initStatCounters() {
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const statObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const el     = entry.target;
      const target = parseInt(el.dataset.target, 10);
      if (prefersReduced) {
        el.textContent = target;
      } else {
        animateCounter(el, target, 1200);
      }
      statObserver.unobserve(el);
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('.stat-number').forEach(el => statObserver.observe(el));
}

/* ── Teardown — clears timers on instant navigation ─────── */
function teardown() {
  clearTimeout(typingTimer);
  clearTimeout(carouselTimer);
  if (revealObserver) revealObserver.disconnect();
  typingIndex  = 0;
  charIndex    = 0;
  isDeleting   = false;
  carouselIndex = 0;
}

/* ── Init ──────────────────────────────────────────────── */
function init() {
  teardown();

  initCarousel();
  initScrollReveal();
  initStatCounters();

  // Typing effect only on the home page (where the element exists)
  if (document.getElementById('bs-typing-text')) {
    typingTimer = setTimeout(runTyping, 400);
    // Start carousel rotation after first badge is shown
    carouselTimer = setTimeout(rotateCarousel, 2500);
  }
}

// Standard page load
document.addEventListener('DOMContentLoaded', init);

// MkDocs Material instant navigation — `document$` is an RxJS Subject
// exposed globally by the Material theme bundle. It emits on every page swap.
if (typeof document$ !== 'undefined') {
  document$.subscribe(init);
}
```

- [ ] **Step 2: Build and verify**

```bash
mkdocs build --strict 2>&1 | tail -10
```

Expected: exits 0, no JS-related errors in MkDocs output (MkDocs doesn't validate JS, so any errors here are likely template or config issues).

- [ ] **Step 3: Commit**

```bash
git add docs/js/extra.js
git commit -m "feat(docs): add extra.js — carousel, scroll reveal, typing effect, stat counters"
```

---

## Task 6: Final build verification

**Files:** None — verification only.

- [ ] **Step 1: Clean build from scratch**

```bash
rm -rf public/ && mkdocs build --strict 2>&1
```

Expected: exits 0, `public/` directory created, no errors.

- [ ] **Step 2: Check key output files exist**

```bash
ls public/index.html public/css/extra.css public/js/extra.js
```

Expected: all three files present and non-empty. (The `docs/overrides/` directory is a theme directory — it is never copied to `public/`.)

- [ ] **Step 3: Spot-check the home page HTML**

```bash
grep -c "bs-hero\|bs-carousel\|bs-typing" public/index.html
```

Expected: a positive integer (hero HTML was rendered from the template).

- [ ] **Step 4: Serve and visually verify**

```bash
mkdocs serve
```

Open `http://127.0.0.1:8000` in a browser. Verify:
- Hero shows BadgeShield logo with float animation
- Purple gradient heading "BadgeShield" visible
- Typing text cycles between 3 taglines
- Badge carousel cycles every 2.5 seconds
- Stat counters animate up when visible
- Feature cards have glass effect and hover lift
- Code blocks have terminal title bar with three dots
- Header is frosted glass (not purple gradient)
- Toggle dark mode — dark background `#07071a` visible

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "docs(ui): Badge Matrix redesign complete — hero, carousel, reveals, stats"
```
