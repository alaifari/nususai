#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ISO_PATH="${1:-$REPO_DIR/data/raw/corpus.iso}"
WORK_DIR="$REPO_DIR/data/full_corpus"
EXTRACT_DIR="$WORK_DIR/extracted"
JSONL_PATH="$WORK_DIR/corpus_export.jsonl"
SQLITE_PATH="$REPO_DIR/data/corpus.sqlite"

if [[ ! -f "$ISO_PATH" ]]; then
  echo "ISO file not found: $ISO_PATH"
  exit 1
fi

if [[ -z "${CORPUS_ARCHIVE_PASSWORD:-}" ]]; then
  echo "CORPUS_ARCHIVE_PASSWORD is required."
  echo "Example: CORPUS_ARCHIVE_PASSWORD='...' $0 $ISO_PATH"
  exit 1
fi

mkdir -p "$WORK_DIR" "$EXTRACT_DIR"

echo "[1/5] Mounting ISO..."
MOUNT_OUTPUT="$(hdiutil attach -readonly -nobrowse "$ISO_PATH")"
MOUNT_POINT="$(echo "$MOUNT_OUTPUT" | tail -n1 | awk '{print $NF}')"

cleanup() {
  if [[ -n "${MOUNT_POINT:-}" && -d "$MOUNT_POINT" ]]; then
    hdiutil detach "$MOUNT_POINT" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

ARCHIVE_PATH="$MOUNT_POINT/data/shamela.bin"
if [[ ! -f "$ARCHIVE_PATH" ]]; then
  echo "Could not find payload archive at $ARCHIVE_PATH"
  exit 1
fi

echo "[2/5] Verifying archive password..."
if ! 7zz t -p"$CORPUS_ARCHIVE_PASSWORD" "$ARCHIVE_PATH" "database/book/001/1.db" >/tmp/nusus_password_test.log 2>&1; then
  echo "Password check failed. Please verify CORPUS_ARCHIVE_PASSWORD."
  echo "Details: /tmp/nusus_password_test.log"
  exit 1
fi

echo "[3/5] Extracting database files (this can take a long time)..."
7zz x -bb0 -y -p"$CORPUS_ARCHIVE_PASSWORD" "$ARCHIVE_PATH" "database/*" -o"$EXTRACT_DIR" >/tmp/nusus_extract.log 2>&1

echo "[4/5] Converting extracted .db files to JSONL..."
python3 "$REPO_DIR/scripts/build_jsonl_from_corpus_dbs.py" \
  --db-root "$EXTRACT_DIR/database/book" \
  --output "$JSONL_PATH"

echo "[5/5] Building search index sqlite..."
python3 "$REPO_DIR/scripts/build_sqlite_from_jsonl.py" --input "$JSONL_PATH" --output "$SQLITE_PATH"

echo "Done."
echo "Index ready at: $SQLITE_PATH"
