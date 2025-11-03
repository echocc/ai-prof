# AI Professional Ingestion & Indexing Starter

Turn-key pipeline to ingest website posts, transcribe audio talks, parse PDFs/EPUBs, chunk + embed with Sentence-Transformers, and index into Postgres + pgvector.

## Quickstart

```bash
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Optional: start Postgres with pgvector
docker compose up -d

# Initialize schema
psql "$(grep -v '^#' .env | xargs)" -f scripts/00_init_db.sql || make db

# Put files
# - audio -> data/raw/audio
# - PDFs  -> data/raw/pdfs
# - EPUBs -> data/raw/epubs

# Crawl public site sections
python scripts/10_scrape_site.py

# Transcribe your audio talks
python scripts/20_transcribe_audio.py

# Parse books
python scripts/30_ingest_pdfs_epubs.py

# Chunk + embed + load
python scripts/40_chunk_embed_load.py

# Sanity search
python scripts/maintenance.py
```

Or use the CLI:
```bash
chmod +x cli.py
./cli.py up
./cli.py db
./cli.py scrape
./cli.py transcribe
./cli.py ingest_books
./cli.py embed
./cli.py search
```

## Notes
- Default embedding: `sentence-transformers/all-MiniLM-L6-v2` (384 dims). Change `EMBED_MODEL` and `zen_chunks.embedding` dim if you switch models.
- The `pgvector` image includes the extension; we also ship an init script to ensure it's enabled.
- `10_scrape_site.py` uses simple domain filtering; adjust `SEEDS` for your target pages.

## Folders
- `data/raw/*`: your source files
- `data/processed/*`: normalized text used for chunking/embedding
- `scripts/*`: ETL steps
```
