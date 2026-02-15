# Nusus AI

Nusus AI is a web application for asking questions in any language and receiving answers grounded in local source texts, with explicit citations in Arabic.

## Features in this version
- User-friendly web chat UI (desktop + mobile).
- `POST /api/chat` backend endpoint.
- Retrieval from local sqlite index (FTS5 full-text search).
- Multi-opinion output structure with per-opinion citation IDs.
- Arabic citation list including book, author, source reference, and snippet.
- Language handling:
  - Input can be in any language.
  - If `OPENAI_API_KEY` is configured, the system translates non-Arabic queries for retrieval and generates the answer in the same language as the question.
  - Without API key, the app falls back to extractive mode.

## Project structure
- `index.html`, `styles.css`, `app.js`: frontend chat application.
- `backend/app/main.py`: FastAPI app and API routes.
- `backend/app/service.py`: question pipeline (language detection, retrieval, answer synthesis).
- `backend/app/retrieval.py`: sqlite retrieval and source diversity logic.
- `backend/app/llm.py`: optional LLM translation/answer generation.
- `scripts/build_sqlite_from_jsonl.py`: build searchable sqlite index from JSONL.
- `scripts/import_sqlite_table_to_jsonl.py`: convert existing sqlite table to expected JSONL schema.
- `scripts/seed_sample_data.py`: generate sample dataset for quick local testing.
- `scripts/download_corpus_iso.sh`: download a corpus ISO file.

## Requirements
- Python 3.11+
- SQLite with FTS5 (default in modern Python builds)

## Quick start
1. Create environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
```

3. Build a sample index (for immediate testing):
```bash
python3 scripts/seed_sample_data.py
python3 scripts/build_sqlite_from_jsonl.py --input data/corpus_sample.jsonl --output data/corpus.sqlite
```

4. Run the app:
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8010
```

5. Open:
- `http://localhost:8010`
- Health check: `http://localhost:8010/api/health`

## Run with Docker
```bash
docker compose up --build
```

## Ingestion workflow
1. Download source ISO:
```bash
./scripts/download_corpus_iso.sh ./data/raw
```

2. Extract or convert source data to a sqlite table or JSONL.

3. If you have a sqlite table, export to JSONL format expected by Nusus AI:
```bash
python3 scripts/import_sqlite_table_to_jsonl.py \
  --db ./path/to/source.sqlite \
  --table passages_table \
  --id-col id \
  --book-col book_title_ar \
  --author-col author_ar \
  --source-col source_ref_ar \
  --text-col text_ar \
  --volume-col volume \
  --page-col page \
  --output ./data/corpus_export.jsonl
```

4. Build Nusus retrieval index:
```bash
python3 scripts/build_sqlite_from_jsonl.py --input ./data/corpus_export.jsonl --output ./data/corpus.sqlite
```

## JSONL schema expected by index builder
Each line should be a JSON object:
```json
{
  "id": "unique-id",
  "book_title_ar": "اسم الكتاب",
  "author_ar": "اسم المؤلف",
  "source_ref_ar": "المرجع، جX، صY",
  "volume": "X",
  "page": "Y",
  "text_ar": "النص العربي"
}
```

## API contract
### `POST /api/chat`
Request:
```json
{
  "question": "What are the conditions of valid sale in fiqh?",
  "top_k": 12,
  "max_opinions": 4
}
```

Response shape:
```json
{
  "answer": "...",
  "language": "en",
  "opinions": [
    {
      "title": "...",
      "summary": "...",
      "citation_ids": ["id-1", "id-2"]
    }
  ],
  "citations": [
    {
      "id": "id-1",
      "book_title_ar": "...",
      "author_ar": "...",
      "source_ref_ar": "...",
      "volume": "...",
      "page": "...",
      "snippet_ar": "...",
      "score": -8.14
    }
  ],
  "notes": []
}
```

## Notes
- Citation metadata intentionally remains Arabic.
- Future version can add translated citation metadata in the user language.
- For high quality multilingual answers, set `OPENAI_API_KEY` in `.env`.
