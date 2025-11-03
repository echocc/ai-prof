.PHONY: venv install db scrape transcribe ingest_books embed search all up down psql

PY?=python
PIP?=pip
ENV?=.env

venv:
	$(PY) -m venv .venv && . .venv/bin/activate && $(PIP) install -U pip

install:
	. .venv/bin/activate && pip install -r requirements.txt

up:
	docker compose up -d

down:
	docker compose down

psql:
	docker compose exec db psql -U postgres -d ai_prof

db:
	. .venv/bin/activate && psql "$$(grep -v '^#' $(ENV) | xargs)" -f scripts/00_init_db.sql

scrape:
	. .venv/bin/activate && $(PY) scripts/10_scrape_site.py

transcribe:
	. .venv/bin/activate && $(PY) scripts/20_transcribe_audio.py

ingest_books:
	. .venv/bin/activate && $(PY) scripts/30_ingest_pdfs_epubs.py

embed:
	. .venv/bin/activate && $(PY) scripts/40_chunk_embed_load.py

search:
	. .venv/bin/activate && $(PY) scripts/maintenance.py

all: scrape transcribe ingest_books embed search
