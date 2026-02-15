#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build local corpus sqlite index from JSONL passages.")
    parser.add_argument("--input", required=True, help="Input JSONL path")
    parser.add_argument("--output", required=True, help="Output sqlite DB path")
    return parser.parse_args()


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS passages;
        DROP TABLE IF EXISTS passages_fts;

        CREATE TABLE passages (
            id TEXT PRIMARY KEY,
            book_title_ar TEXT NOT NULL,
            author_ar TEXT NOT NULL,
            source_ref_ar TEXT NOT NULL,
            volume TEXT,
            page TEXT,
            text_ar TEXT NOT NULL
        );

        CREATE VIRTUAL TABLE passages_fts USING fts5(
            id UNINDEXED,
            text_ar,
            book_title_ar,
            author_ar,
            source_ref_ar,
            tokenize = 'unicode61 remove_diacritics 2'
        );
        """
    )


def ingest_jsonl(conn: sqlite3.Connection, input_path: Path) -> int:
    count = 0
    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            row = json.loads(line)
            pid = str(row["id"])
            book_title_ar = str(row.get("book_title_ar", "")).strip()
            author_ar = str(row.get("author_ar", "")).strip()
            source_ref_ar = str(row.get("source_ref_ar", "")).strip()
            text_ar = str(row.get("text_ar", "")).strip()
            volume = str(row.get("volume", "")).strip() or None
            page = str(row.get("page", "")).strip() or None

            if not pid or not book_title_ar or not author_ar or not source_ref_ar or not text_ar:
                continue

            conn.execute(
                """
                INSERT INTO passages (id, book_title_ar, author_ar, source_ref_ar, volume, page, text_ar)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (pid, book_title_ar, author_ar, source_ref_ar, volume, page, text_ar),
            )
            conn.execute(
                """
                INSERT INTO passages_fts (id, text_ar, book_title_ar, author_ar, source_ref_ar)
                VALUES (?, ?, ?, ?, ?)
                """,
                (pid, text_ar, book_title_ar, author_ar, source_ref_ar),
            )
            count += 1

    return count


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(str(output_path)) as conn:
        create_schema(conn)
        count = ingest_jsonl(conn, input_path)
        conn.commit()

    print(f"Indexed {count} passages into {output_path}")


if __name__ == "__main__":
    main()
