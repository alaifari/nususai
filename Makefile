.PHONY: setup seed build-index run

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

seed:
	python3 scripts/seed_sample_data.py

build-index:
	python3 scripts/build_sqlite_from_jsonl.py --input data/corpus_sample.jsonl --output data/corpus.sqlite

run:
	uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8010
