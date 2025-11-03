#!/usr/bin/env python3
import argparse, subprocess, os, sys

def run(cmd):
    print("+", " ".join(cmd))
    return subprocess.call(cmd)

def main():
    ap = argparse.ArgumentParser(description="AI Zen ingestion/index CLI")
    ap.add_argument("command", choices=[
        "scrape","transcribe","ingest_books","embed","search","db","up","down"
    ])
    args = ap.parse_args()

    env = os.environ.copy()
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                line=line.strip()
                if not line or line.startswith("#") or "=" not in line: continue
                k,v=line.split("=",1); env[k]=v

    m = {
        "scrape": ["python","scripts/10_scrape_site.py"],
        "transcribe": ["python","scripts/20_transcribe_audio.py"],
        "ingest_books": ["python","scripts/30_ingest_pdfs_epubs.py"],
        "embed": ["python","scripts/40_chunk_embed_load.py"],
        "search": ["python","scripts/maintenance.py"],
        "db": ["psql", env.get("DATABASE_URL","postgresql://postgres:postgres@localhost:5432/ai_prof"), "-f", "scripts/00_init_db.sql"],
        "up": ["docker","compose","up","-d"],
        "down": ["docker","compose","down"],
    }
    sys.exit(run(m[args.command]))

if __name__ == "__main__":
    main()
