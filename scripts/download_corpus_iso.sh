#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-./data/raw}"
OUT_FILE="${OUT_DIR}/corpus.iso"
URL="${CORPUS_ISO_URL:-}"

if [[ -z "${URL}" ]]; then
  echo "CORPUS_ISO_URL is not set."
  echo "Usage: CORPUS_ISO_URL='https://.../full.iso' ./scripts/download_corpus_iso.sh ./data/raw"
  exit 1
fi

mkdir -p "${OUT_DIR}"

echo "Downloading corpus ISO to ${OUT_FILE}"
curl -L --fail --progress-bar "${URL}" -o "${OUT_FILE}"
echo "Done."
