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
