#!/usr/bin/env bash
# Format all frontend files with Prettier
set -e

cd "$(dirname "$0")/.."

echo "Formatting frontend files..."
npx prettier --write frontend/
echo "Done."
