# Frontend Code Quality Changes

## Summary

Added code quality tooling for the frontend (HTML/CSS/JS) files.

## Tools Added

### Prettier (code formatter)
The frontend equivalent of `black` for Python. Enforces consistent formatting across all frontend files.

- **Config**: `.prettierrc` at repo root
- **Ignore patterns**: `.prettierignore` (excludes `node_modules/`, minified files)
- **Formatted files**: `frontend/index.html`, `frontend/script.js`, `frontend/style.css`

**Key formatting rules:**
- 2-space indentation
- 100-character print width
- Double quotes
- Trailing commas (ES5 style)
- LF line endings

### ESLint (JavaScript linter)
Catches potential bugs and enforces code quality rules in `script.js`.

- **Config**: `.eslintrc.json` at repo root
- **Rules**: `no-var` (error), `eqeqeq` (error), `no-console` (warning), `prefer-const` (warning), `no-unused-vars` (warning)

## New Files

| File | Purpose |
|------|---------|
| `package.json` | Node dev dependencies + npm scripts |
| `.prettierrc` | Prettier formatting config |
| `.prettierignore` | Files to exclude from formatting |
| `.eslintrc.json` | ESLint rules config |
| `scripts/format-frontend.sh` | Script to auto-format all frontend files |
| `scripts/check-frontend.sh` | Script to check formatting + lint (CI-friendly) |

## npm Scripts

```bash
npm run format        # Auto-format all frontend files with Prettier
npm run format:check  # Check formatting without writing (for CI)
npm run lint          # Run ESLint on script.js
npm run lint:fix      # Auto-fix ESLint issues
npm run check         # Run format:check + lint (full quality gate)
```

## Shell Scripts

```bash
./scripts/format-frontend.sh   # Format all frontend files
./scripts/check-frontend.sh    # Full quality check (exits non-zero on failure)
```

## Formatting Applied

Prettier was run on all three frontend files at setup time, applying consistent style:
- Consistent quote style (double quotes)
- Trailing commas in JS objects/arrays
- Consistent indentation (2 spaces)
- Normalized whitespace and line endings
