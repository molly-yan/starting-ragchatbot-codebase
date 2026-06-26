#!/usr/bin/env bash
# Run all frontend quality checks (format check + lint)
set -e

cd "$(dirname "$0")/.."

echo "=== Prettier format check ==="
npx prettier --check frontend/

echo ""
echo "=== ESLint ==="
npx eslint frontend/script.js

echo ""
echo "All checks passed."
