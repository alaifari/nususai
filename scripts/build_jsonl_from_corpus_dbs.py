#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

TEXT_COL_PRIORITY = [
    "text_ar",
    "text",
    "nass",
    "matn",
    "content",
    "body",
    "bk",
]
BOOK_COL_PRIORITY = ["book_title_ar", "book", "kitab", "book_name", "title"]
AUTHOR_COL_PRIORITY = ["author_ar", "author", "auth", "moalf", "muallif"]
ID_COL_PRIORITY = ["id", "pid", "no", "rowid"]
PAGE_COL_PRIORITY = ["page", "safha"]
VOLUME_COL_PRIORITY = ["volume", "part", "juz", "vol"]

AR_RE = re.compile(r"[\u0600-\u06FF]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build JSONL passages from extracted corpus SQLite databases.")
    parser.add_argument("--db-root", required=True, help="Root folder containing many .db files")
    parser.add_argument("--output", required=True, help="Output JSONL path")
    parser.add_argument("--max-per-db", type=int, default=0, help="Optional max rows per db (0 = unlimited)")
    return parser.parse_args()


def choose_col(columns: list[str], preferred: list[str]) -> str | None:
    lower_map = {c.lower(): c for c in columns}
    for name in preferred:
        if name.lower() in lower_map:
            return lower_map[name.lower()]
    return None


def looks_like_text_column_name(name: str) -> bool:
    n = name.lower()
    return any(token in n for token in ["text", "nass", "matn", "body", "content", "bk"])


def find_text_col(columns: list[str]) -> str | None:
    explicit = choose_col(columns, TEXT_COL_PRIORITY)
    if explicit:
        return explicit
    for col in columns:
        if looks_like_text_column_name(col):
            return col
    return None


def is_candidate_text(value: str) -> bool:
    if not value:
        return False
    v = " ".join(value.split())
    if len(v) < 40:
        return False
    return bool(AR_RE.search(v))


def list_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
    return [r[0] for r in rows]


def table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    safe_table = table.replace("'", "''")
    rows = conn.execute(f"PRAGMA table_info('{safe_table}')").fetchall()
    return [r[1] for r in rows]


def extract_from_db(db_path: Path, out_file, max_per_db: int = 0) -> int:
    count = 0
    book_fallback = db_path.stem

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        tables = list_tables(conn)
        if not tables:
            return 0

        for table in tables:
            cols = table_columns(conn, table)
            if not cols:
                continue

            text_col = find_text_col(cols)
            if not text_col:
                continue

            id_col = choose_col(cols, ID_COL_PRIORITY)
            book_col = choose_col(cols, BOOK_COL_PRIORITY)
            author_col = choose_col(cols, AUTHOR_COL_PRIORITY)
            page_col = choose_col(cols, PAGE_COL_PRIORITY)
            volume_col = choose_col(cols, VOLUME_COL_PRIORITY)

            select_cols = [text_col]
            for c in [id_col, book_col, author_col, page_col, volume_col]:
                if c and c not in select_cols:
                    select_cols.append(c)

            qcols = ", ".join([f'"{c}"' for c in select_cols])
            query = f"SELECT {qcols} FROM \"{table}\""
            if max_per_db > 0:
                query += f" LIMIT {max_per_db}"

            try:
                rows = conn.execute(query).fetchall()
            except Exception:
                continue

            for row in rows:
                text_val = str(row[text_col] or "").strip()
                if not is_candidate_text(text_val):
                    continue

                row_id = str(row[id_col]) if id_col else f"{table}-{count+1}"
                book_title = str(row[book_col]).strip() if book_col else book_fallback
                author = str(row[author_col]).strip() if author_col else "غير محدد"
                page = str(row[page_col]).strip() if page_col else ""
                volume = str(row[volume_col]).strip() if volume_col else ""

                source_ref = f"{book_title}"
                if volume:
                    source_ref += f"، ج{volume}"
                if page:
                    source_ref += f"، ص{page}"

                out = {
                    "id": f"{db_path.stem}:{table}:{row_id}",
                    "book_title_ar": book_title or book_fallback,
                    "author_ar": author or "غير محدد",
                    "source_ref_ar": source_ref,
                    "volume": volume,
                    "page": page,
                    "text_ar": " ".join(text_val.split()),
                }
                out_file.write(json.dumps(out, ensure_ascii=False) + "\n")
                count += 1
    finally:
        conn.close()

    return count


def main() -> None:
    args = parse_args()
    db_root = Path(args.db_root).resolve()
    output_path = Path(args.output).resolve()

    if not db_root.exists():
        raise SystemExit(f"DB root not found: {db_root}")

    db_files = sorted(db_root.rglob("*.db"))
    if not db_files:
        raise SystemExit("No .db files found under DB root")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    with output_path.open("w", encoding="utf-8") as out:
        for db in db_files:
            try:
                total += extract_from_db(db, out, max_per_db=args.max_per_db)
            except Exception:
                continue

    print(f"Wrote {total} passages to {output_path}")


if __name__ == "__main__":
    main()
