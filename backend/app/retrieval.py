from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Passage:
    id: str
    book_title_ar: str
    author_ar: str
    source_ref_ar: str
    volume: str | None
    page: str | None
    snippet_ar: str
    score: float


_MATCH_CLEANER = re.compile(r"[^\w\s\u0600-\u06FF]+", flags=re.UNICODE)
_WHITESPACE = re.compile(r"\s+")


def normalize_for_match(text: str) -> str:
    cleaned = _MATCH_CLEANER.sub(" ", text).strip()
    return _WHITESPACE.sub(" ", cleaned)


class CorpusRetriever:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        if not self.db_path.exists():
            raise FileNotFoundError(f"Corpus DB not found at: {self.db_path}")
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def search(self, query: str, limit: int = 12) -> list[Passage]:
        normalized = normalize_for_match(query)
        if not normalized:
            return []

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    p.id,
                    p.book_title_ar,
                    p.author_ar,
                    p.source_ref_ar,
                    p.volume,
                    p.page,
                    p.text_ar AS snippet_ar,
                    bm25(passages_fts) AS score
                FROM passages_fts
                JOIN passages p ON p.id = passages_fts.id
                WHERE passages_fts MATCH ?
                ORDER BY score ASC
                LIMIT ?
                """,
                (normalized, limit),
            ).fetchall()

        results: list[Passage] = []
        for row in rows:
            results.append(
                Passage(
                    id=row["id"],
                    book_title_ar=row["book_title_ar"],
                    author_ar=row["author_ar"],
                    source_ref_ar=row["source_ref_ar"],
                    volume=row["volume"],
                    page=row["page"],
                    snippet_ar=(row["snippet_ar"] or "")[:400],
                    score=float(row["score"]),
                )
            )
        return results


def pick_diverse_passages(passages: list[Passage], max_items: int, max_per_source: int = 2) -> list[Passage]:
    selected: list[Passage] = []
    count_by_source: dict[str, int] = {}

    for item in passages:
        source_key = f"{item.book_title_ar}|{item.author_ar}"
        used = count_by_source.get(source_key, 0)
        if used >= max_per_source:
            continue
        count_by_source[source_key] = used + 1
        selected.append(item)
        if len(selected) >= max_items:
            break

    return selected
