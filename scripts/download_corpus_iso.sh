#!/usr/bin/env bash
set -euo pipefail

URL="https://example.com/corpus.iso"
OUT_DIR="${1:-./data/raw}"
OUT_FILE="${OUT_DIR}/corpus.iso"

mkdir -p "${OUT_DIR}"

echo "Downloading corpus ISO to ${OUT_FILE}"
curl -L --fail --progress-bar "${URL}" -o "${OUT_FILE}"
echo "Done."
