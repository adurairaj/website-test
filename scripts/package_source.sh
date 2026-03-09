#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$ROOT_DIR/dist"
OUT_FILE="$OUT_DIR/website-test-source.zip"

mkdir -p "$OUT_DIR"
rm -f "$OUT_FILE"

cd "$ROOT_DIR"
zip -r "$OUT_FILE" . \
  -x ".git/*" \
  -x "dist/*" \
  -x "frontend/node_modules/*" \
  -x "backend/.venv/*" \
  -x "__pycache__/*" \
  -x "*.pyc"

echo "Created: $OUT_FILE"
