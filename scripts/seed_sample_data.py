#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


SAMPLE_ROWS = [
    {
        "id": "mughni-1-45",
        "book_title_ar": "المغني",
        "author_ar": "ابن قدامة",
        "source_ref_ar": "المغني، ج1، ص45",
        "volume": "1",
        "page": "45",
        "text_ar": "ومن شروط صحة البيع التراضي بين المتبايعين، وأن يكون المعقود عليه معلوماً مباحاً مقدوراً على تسليمه.",
    },
    {
        "id": "majmoo-3-112",
        "book_title_ar": "المجموع",
        "author_ar": "النووي",
        "source_ref_ar": "المجموع، ج3، ص112",
        "volume": "3",
        "page": "112",
        "text_ar": "وأما البيع بشرط مجهول فلا يصح عند جمهور أصحابنا، لأن الغرر منهي عنه في المعاوضات.",
    },
    {
        "id": "fath-2-97",
        "book_title_ar": "فتح الباري",
        "author_ar": "ابن حجر",
        "source_ref_ar": "فتح الباري، ج2، ص97",
        "volume": "2",
        "page": "97",
        "text_ar": "استدل العلماء بحديث النهي عن بيع الغرر على منع صور من البيوع يكثر فيها الجهالة والنزاع.",
    },
    {
        "id": "bidaya-2-166",
        "book_title_ar": "بداية المجتهد",
        "author_ar": "ابن رشد",
        "source_ref_ar": "بداية المجتهد، ج2، ص166",
        "volume": "2",
        "page": "166",
        "text_ar": "واختلفوا في بعض البيوع المستحدثة لاختلافهم في تحقيق معنى الغرر المؤثر في العقد.",
    },
    {
        "id": "umm-3-25",
        "book_title_ar": "الأم",
        "author_ar": "الشافعي",
        "source_ref_ar": "الأم، ج3، ص25",
        "volume": "3",
        "page": "25",
        "text_ar": "وأحب إلي أن يكون الثمن معلوماً والأجل معلوماً دفعاً للتنازع وقطعاً للخصومة.",
    },
]


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    out_path = repo_root / "data" / "corpus_sample.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        for row in SAMPLE_ROWS:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Wrote sample dataset to {out_path}")


if __name__ == "__main__":
    main()
