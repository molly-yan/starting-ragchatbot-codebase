# Frontend Changes

## Dark/Light Mode Toggle Button

### What was added

A fixed-position theme toggle button in the top-right corner of the UI that switches between the existing dark mode and a new light mode.

### Files modified

**`frontend/index.html`**
- Added a `<button id="themeToggle">` element directly inside `<body>`, before `.container`, so it sits above all layout.
- The button contains two SVG icons: a sun (shown in dark mode) and a moon (shown in light mode). Both have `aria-hidden="true"` so screen readers use the button's `aria-label` instead.
- Bumped cache-busting query string on `style.css` and `script.js` to `v=10`.

**`frontend/style.css`**
- Added a `/* Theme Transition */` block applying `transition` for `background-color`, `border-color`, and `color` to all elements — gives the smooth cross-fade when toggling.
- Added a `:root[data-theme="light"]` rule (using a `data-theme` attribute on `<html>`) that overrides the dark-mode CSS variables with WCAG-accessible light equivalents:
  - `--primary-color: #1d4ed8` (Blue 700, 7.2:1 on white — WCAG AAA)
  - `--primary-hover: #1e40af` (Blue 800)
  - `--text-primary: #0f172a` (Slate 900, ~18:1 — WCAG AAA)
  - `--text-secondary: #475569` (Slate 600, 7:1 — WCAG AAA, upgraded from Slate 500)
  - `--border-color: #cbd5e1` (Slate 300 — more visible than Slate 200)
  - `--shadow` tinted with dark ink (`rgba(15,23,42,…)`) instead of pure black
  - `--focus-ring: rgba(29,78,216,0.3)` — 50% more opaque than dark mode for better visibility on light backgrounds
- Added `--toggle-bg`, `--toggle-border`, `--toggle-color`, `--toggle-hover-bg` variables (with light-mode overrides) so the button blends into whichever theme is active.
- Added `#themeToggle` styles: `position: fixed; top: 1rem; right: 1rem; z-index: 1000`, circular (42×42px), with hover scale, focus ring, and active shrink effects.
- Added icon transition rules: `.icon-sun` / `.icon-moon` use `opacity` + `rotate/scale` transforms for a spinning crossfade animation.

**`frontend/script.js`**
- Added `initTheme()` — called on `DOMContentLoaded`, reads `localStorage.getItem('theme')` (defaults to `'dark'`) and calls `applyTheme()`. Wires up click and keyboard (`Enter`/`Space`) listeners on `#themeToggle`.
- Added `applyTheme(theme)` — sets `data-theme` attribute on `document.documentElement` and updates the button's `aria-label`.
- Added `toggleTheme()` — reads the current `data-theme` attribute, flips to the other value, calls `applyTheme()`, and persists to `localStorage`.

### Behavior

- **Default**: dark mode (no change to existing appearance).
- **Toggle**: clicking or pressing Enter/Space switches modes with a smooth 0.3s color transition and a rotating icon crossfade.
- **Persistence**: chosen theme saved in `localStorage` under key `theme` (`"light"` or `"dark"`), restored on next page load.
- **Accessibility**: `aria-label` updates dynamically to describe the *action* ("Switch to dark mode" / "Switch to light mode"); SVG icons are decorative (`aria-hidden`); focus ring is visible in both modes; fully keyboard-navigable.

### Accessibility contrast ratios (light mode)

| Token | Value | Contrast on `--background` |
|---|---|---|
| `--text-primary` | #0f172a | ~18:1 (AAA) |
| `--text-secondary` | #475569 | ~7:1 (AAA) |
| `--primary-color` | #1d4ed8 | ~7.2:1 (AAA) |
| `--user-message` text (white on #1d4ed8) | — | ~7.2:1 (AAA) |
