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

  carouselIndex = carouselIndex % items.length;
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
      if (isNaN(target)) return;
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
  if (revealObserver) { revealObserver.disconnect(); revealObserver = null; }
  typingIndex  = 0;
  charIndex    = 0;
  isDeleting   = false;
  carouselIndex = 0;
}

/* ── Init ──────────────────────────────────────────────── */
function init() {
  teardown();

  if (document.getElementById('bs-badge-0')) {
    initCarousel();
  }
  initScrollReveal();
  initStatCounters();

  // Typing effect and carousel only on the home page (where the element exists)
  if (document.getElementById('bs-typing-text')) {
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    typingTimer = setTimeout(runTyping, 400);
    if (!prefersReduced) {
      carouselTimer = setTimeout(rotateCarousel, 2500);
    }
  }
}

// Register init: use MkDocs Material instant navigation if available,
// otherwise fall back to DOMContentLoaded. Using both causes double-init
// on first load when instant navigation is enabled.
if (typeof document$ !== 'undefined') {
  document$.subscribe(init);
} else {
  document.addEventListener('DOMContentLoaded', init);
}
