# Nusus AI

Nusus AI is a local-first web application for asking questions in any language and receiving answers grounded in a local source corpus, with explicit Arabic citations.

## Current product decisions
- Runtime: local machine only.
- Access: users can access the local app and bring their own OpenAI API key.
- Token usage: each user uses their own OpenAI key (session-scoped in browser).
- Corpus: full database download + local indexing supported.
- Abuse controls: intentionally deferred for a later milestone.
- Launch reminder: enabled by default before any public deployment.

## Features in this version
- User-friendly web chat UI (desktop + mobile).
- `POST /api/chat` backend endpoint.
- Retrieval from local sqlite index (FTS5 full-text search).
- Multi-opinion output structure with per-opinion citation IDs.
- Arabic citation list including book, author, source reference, and snippet.
- Language handling:
  - Input can be in any language.
  - If user provides API key, app translates non-Arabic queries for retrieval and generates answers in the same language as the question.
  - Without API key, app falls back to extractive mode.

## Project structure
- `index.html`, `styles.css`, `app.js`: frontend chat app.
- `backend/app/main.py`: FastAPI app and API routes.
- `backend/app/service.py`: question pipeline (language detection, retrieval, answer synthesis).
- `backend/app/retrieval.py`: sqlite retrieval and source diversity logic.
- `backend/app/llm.py`: LLM translation/answer generation.
- `scripts/build_sqlite_from_jsonl.py`: build searchable sqlite index from JSONL.
- `scripts/import_sqlite_table_to_jsonl.py`: convert existing sqlite table to expected JSONL schema.
- `scripts/seed_sample_data.py`: generate sample dataset for quick local testing.
- `scripts/download_corpus_iso.sh`: download corpus ISO using env URL.

## Requirements
- Python 3.11+
- SQLite with FTS5

## Quick start
1. Create environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

2. Configure env:
```bash
cp .env.example .env
```

3. Build sample index:
```bash
python3 scripts/seed_sample_data.py
python3 scripts/build_sqlite_from_jsonl.py --input data/corpus_sample.jsonl --output data/corpus.sqlite
```

4. Run locally:
```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8010
```

5. Open:
- `http://localhost:8010`
- `http://localhost:8010/api/health`

## Full corpus download and indexing
1. Download ISO (set URL at runtime):
```bash
CORPUS_ISO_URL='https://.../full.iso' ./scripts/download_corpus_iso.sh ./data/raw
```

2. Extract/convert data into sqlite table or JSONL.

3. Export sqlite table to JSONL format expected by Nusus AI:
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

4. Build retrieval index:
```bash
python3 scripts/build_sqlite_from_jsonl.py --input ./data/corpus_export.jsonl --output ./data/corpus.sqlite
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
Headers:
- `X-OpenAI-API-Key: sk-...` (optional, user key)

## Public launch reminder
Before going public, do not deploy without adding:
1. Authentication and account boundaries.
2. Abuse controls and rate limiting.
3. Logging/privacy policy decisions.
4. Secret management and key safety model.

Keep `PUBLIC_LAUNCH_REMINDER=1` until these are complete.
