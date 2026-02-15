#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export rows from an existing sqlite table to Nusus JSONL format.")
    parser.add_argument("--db", required=True, help="Input sqlite file path")
    parser.add_argument("--table", required=True, help="Table name")
    parser.add_argument("--id-col", required=True, help="ID column")
    parser.add_argument("--book-col", required=True, help="Arabic book title column")
    parser.add_argument("--author-col", required=True, help="Arabic author column")
    parser.add_argument("--source-col", required=True, help="Arabic source reference column")
    parser.add_argument("--text-col", required=True, help="Arabic passage text column")
    parser.add_argument("--volume-col", default="", help="Volume column (optional)")
    parser.add_argument("--page-col", default="", help="Page column (optional)")
    parser.add_argument("--where", default="", help="Optional SQL WHERE clause")
    parser.add_argument("--limit", type=int, default=0, help="Optional row limit")
    parser.add_argument("--output", required=True, help="Output JSONL path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_path = Path(args.db).resolve()
    output_path = Path(args.output).resolve()

    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    cols = [args.id_col, args.book_col, args.author_col, args.source_col, args.text_col]
    if args.volume_col:
        cols.append(args.volume_col)
    if args.page_col:
        cols.append(args.page_col)

    select_cols = ", ".join(cols)
    query = f"SELECT {select_cols} FROM {args.table}"
    if args.where:
        query += f" WHERE {args.where}"
    if args.limit > 0:
        query += f" LIMIT {args.limit}"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with sqlite3.connect(str(db_path)) as conn, output_path.open("w", encoding="utf-8") as out:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query).fetchall()
        for row in rows:
            item = {
                "id": str(row[args.id_col]),
                "book_title_ar": str(row[args.book_col] or "").strip(),
                "author_ar": str(row[args.author_col] or "").strip(),
                "source_ref_ar": str(row[args.source_col] or "").strip(),
                "text_ar": str(row[args.text_col] or "").strip(),
                "volume": str(row[args.volume_col] or "").strip() if args.volume_col else "",
                "page": str(row[args.page_col] or "").strip() if args.page_col else "",
            }

            if not all([item["id"], item["book_title_ar"], item["author_ar"], item["source_ref_ar"], item["text_ar"]]):
                continue

            out.write(json.dumps(item, ensure_ascii=False) + "\n")
            count += 1

    print(f"Exported {count} rows to {output_path}")


if __name__ == "__main__":
    main()
