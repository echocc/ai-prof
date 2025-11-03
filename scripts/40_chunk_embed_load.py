"""
Text Chunking and Embedding Script

This script processes all ingested documents, splits them into semantically meaningful
chunks, generates vector embeddings for each chunk, and stores them in the database
for semantic search and retrieval.

Input:
    - Document records from zen_docs table (all source types)
    - Processed text files from:
        * data/processed/web/{doc_id}.txt
        * data/processed/audio/{doc_id}.txt
        * data/processed/books/{doc_id}.txt

Output:
    - Chunk records in zen_chunks table with:
        * Original text content
        * 384-dimensional vector embeddings
        * Chunk index and metadata
        * Reference to parent document

Process:
    1. Query all documents from zen_docs table (newest first)
    2. Skip documents that are already chunked (idempotent)
    3. Load document text file from processed directories
    4. Skip documents with less than 400 characters
    5. Split text into overlapping chunks:
        - Target size: ~350 tokens (words)
        - Overlap: 40 tokens between consecutive chunks
        - Ensures context continuity across chunk boundaries
    6. Generate embeddings using sentence-transformers model:
        - Model: all-MiniLM-L6-v2 (384 dimensions)
        - Normalized embeddings for cosine similarity
    7. Upsert chunks to database:
        - Create new chunks or update existing ones
        - Store content, embeddings, and metadata

Chunking Strategy:
    - Word-based splitting (simple but effective)
    - Overlap ensures no information loss at boundaries
    - ~350 tokens provides good semantic context
    - Chunks are too small = fragmented context
    - Chunks are too large = imprecise retrieval

Embedding Model:
    - sentence-transformers/all-MiniLM-L6-v2
    - Lightweight model (80MB)
    - Fast inference on CPU
    - Good balance of speed and quality
    - 384-dimensional embeddings
    - Optimized for semantic similarity tasks

Performance:
    - ~10-50 chunks per document depending on length
    - ~10-20 documents per second on M-series Mac
    - Processes 500 documents in ~30-60 seconds
    - Embedding generation is the bottleneck

Idempotency:
    - Checks if document is already chunked
    - Skips already-processed documents
    - Can be run multiple times safely
    - Only processes new documents

Usage:
    python scripts/40_chunk_embed_load.py

Configuration:
    - DATABASE_URL: PostgreSQL connection string (.env)
    - EMBED_MODEL: HuggingFace model name (optional, defaults to all-MiniLM-L6-v2)

Requirements:
    - PostgreSQL database with zen_docs and zen_chunks tables
    - pgvector extension installed
    - Processed text files in data/processed/ directories
    - sentence-transformers Python package

Comparison to Alternatives Embedding Models

  | Model                         | Dimensions | Size  | Speed  | Quality   | GPU Needed  |
  |-------------------------------|------------|-------|--------|-----------|-------------|
  | all-MiniLM-L6-v2              | 384        | 80MB  | Fast   | Good      | No          |
  | all-MiniLM-L12-v2             | 384        | 120MB | Medium | Better    | No          |
  | all-mpnet-base-v2             | 768        | 420MB | Slow   | Best      | Recommended |
  | OpenAI text-embedding-3-small | 1536       | API   | N/A    | Excellent | N/A         |

  Why not the alternatives:
  - all-mpnet-base-v2: 5x larger, slower, diminishing returns for this use case
  - OpenAI embeddings: API costs add up ($0.02/1M tokens), vendor lock-in
  - Larger models: Require GPU for reasonable speed, overkill for this dataset
  - Smaller models: Noticeable quality degradation below 384 dimensions

  Perfect for This Use Case

  For an AI Professor of Adyashanti's teachings:
  - Local processing (privacy, no API costs)
  - Fast enough for real-time search
  - Good enough quality for semantic understanding of spiritual concepts
  - Can run on consumer hardware (M-series Mac, modern laptops)
  - Scalable to thousands of documents

  The model is the pragmatic choice for a self-hosted RAG system that balances quality, speed, and accessibility.
"""

import os, uuid
from pathlib import Path
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()
DB=os.getenv("DATABASE_URL")
MODEL=os.getenv("EMBED_MODEL","sentence-transformers/all-MiniLM-L6-v2")

model = SentenceTransformer(MODEL)

PROCESSED_DIRS=[
  Path("data/processed/web"),
  Path("data/processed/audio"),
  Path("data/processed/books")
]

def split_into_chunks(text:str, target_tokens:int=350, overlap:int=40)->List[str]:
    words=text.split()
    approx = target_tokens
    step = max(1, approx - overlap)
    out=[]
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i+approx])
        if len(chunk) > 0: out.append(chunk)
    return out

def get_doc_ids(conn):
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT id FROM zen_docs ORDER BY created_at DESC")
        return [r["id"] for r in cur.fetchall()]

def already_chunked(conn, doc_id):
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT 1 FROM zen_chunks WHERE doc_id=%s LIMIT 1", (doc_id,))
        return bool(cur.fetchone())

def load_text_for_id(doc_id:uuid.UUID)->str:
    for d in PROCESSED_DIRS:
        p = d/f"{doc_id}.txt"
        if p.exists(): return p.read_text()
    return ""

def embed_texts(texts:List[str]):
    return np.array(model.encode(texts, normalize_embeddings=True))

def upsert_chunks(conn, doc_id, chunks:List[str], embeddings):
    with conn.cursor() as cur:
        for idx, (content, emb) in enumerate(zip(chunks, embeddings)):
            cur.execute("""                    INSERT INTO zen_chunks (id, doc_id, chunk_index, content, section, token_count, embedding, metadata)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (doc_id, chunk_index) DO UPDATE
                  SET content=EXCLUDED.content, embedding=EXCLUDED.embedding
            """, (
              uuid.uuid4(), doc_id, idx, content, None, len(content.split()),
              emb.tolist(), '{}'
            ))
    conn.commit()

def main():
    with psycopg.connect(DB) as conn:
        doc_ids = get_doc_ids(conn)
        for doc_id in doc_ids:
            if already_chunked(conn, doc_id):
                continue
            text = load_text_for_id(doc_id)
            if len(text)<400:
                continue
            chunks = split_into_chunks(text)
            embs = embed_texts(chunks)
            upsert_chunks(conn, doc_id, chunks, embs)
            print(f"Indexed {doc_id} with {len(chunks)} chunks.")

if __name__=="__main__":
    main()
