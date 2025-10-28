import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()
DB=os.getenv("DATABASE_URL")

def search(q:str, k:int=5):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(os.getenv("EMBED_MODEL","sentence-transformers/all-MiniLM-L6-v2"))
    qv = model.encode([q], normalize_embeddings=True)[0].tolist()
    with psycopg.connect(DB) as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("""                SELECT c.content, d.title, d.source_type, d.source_url, 
                   1 - (c.embedding <=> %s) AS score
            FROM zen_chunks c
            JOIN zen_docs d ON d.id=c.doc_id
            ORDER BY c.embedding <-> %s
            LIMIT %s
        """, (qv, qv, k))
        return cur.fetchall()

if __name__=="__main__":
    for r in search("What is awakening and how to relate to thoughts?", k=5):
        print(f"[{r['score']:.3f}] {r['title']} :: {r['content'][:140]}…")
