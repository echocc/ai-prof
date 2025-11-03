"""
Semantic Search and Maintenance Script

This script provides semantic search functionality over the indexed document corpus.
It demonstrates how to query the vector database to find semantically similar content
to a natural language question or query.

Input:
    - Natural language query string (e.g., "What is awakening?")
    - Number of results to return (k, defaults to 5)
    - Embeddings stored in zen_chunks table

Output:
    - Top-k most semantically similar text chunks
    - Each result includes:
        * Similarity score (0-1, higher is more similar)
        * Document title and source type
        * Text content of the matching chunk
        * Source URL (if available)

How It Works:
    1. Load the same embedding model used for indexing (all-MiniLM-L6-v2)
    2. Generate a vector embedding for the query string
    3. Use pgvector's distance operators to find nearest neighbors:
        - <-> : L2 distance (Euclidean) - used for ORDER BY
        - <=> : Cosine distance - used for similarity score
        - Score = 1 - cosine_distance (ranges 0-1, 1 is identical)
    4. Join with zen_docs to get document metadata
    5. Return top-k results ordered by similarity

Vector Distance Operators:
    pgvector provides multiple distance functions:

    - Cosine Distance (<=>): Measures angle between vectors
      * Best for normalized embeddings (like ours)
      * Range: 0-2, where 0 = identical, 2 = opposite
      * Score = 1 - cosine_distance gives 0-1 similarity

    - L2 Distance (<->): Euclidean distance
      * Measures straight-line distance in vector space
      * Faster than cosine for large datasets
      * Equivalent to cosine for normalized vectors

    - Inner Product (<#>): Dot product
      * Negative values for similarity ranking
      * Use when vectors are not normalized

    Why We Use Both:
    - ORDER BY uses <-> (L2) for speed
    - SELECT uses <=> (cosine) for interpretable scores
    - Since our embeddings are normalized, both give same ordering

Performance:
    - Query generation: ~10-50ms
    - Vector search on 5000+ chunks: ~10-50ms
    - Total latency: ~50-150ms for typical queries
    - Fast enough for real-time interactive search
    - Can scale to 100k+ chunks without indexes
    - For larger datasets, create IVFFlat or HNSW indexes

Index Recommendations:
    For datasets > 50k chunks, create a vector index:

    ```sql
    -- IVFFlat index (faster build, good for most cases)
    CREATE INDEX zen_chunks_embedding_idx
    ON zen_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

    -- HNSW index (slower build, better recall)
    CREATE INDEX zen_chunks_embedding_idx
    ON zen_chunks
    USING hnsw (embedding vector_cosine_ops);
    ```

Usage Examples:

    # Basic search
    python scripts/maintenance.py

    # In Python code
    from scripts.maintenance import search

    results = search("What is the nature of awareness?", k=10)
    for result in results:
        print(f"Score: {result['score']:.3f}")
        print(f"Title: {result['title']}")
        print(f"Content: {result['content']}")
        print()

    # Integration with RAG pipeline
    def answer_question(question: str) -> str:
        # 1. Retrieve relevant context
        context_chunks = search(question, k=5)
        context = "\\n\\n".join([c['content'] for c in context_chunks])

        # 2. Generate answer using LLM (Claude, GPT, etc.)
        prompt = f"Context:\\n{context}\\n\\nQuestion: {question}\\n\\nAnswer:"
        answer = llm.complete(prompt)

        return answer

Configuration:
    - DATABASE_URL: PostgreSQL connection string (.env)
    - EMBED_MODEL: HuggingFace model name (must match indexing model)

Requirements:
    - PostgreSQL with pgvector extension
    - zen_chunks table populated with embeddings
    - sentence-transformers Python package
    - Same embedding model used in 40_chunk_embed_load.py

Maintenance Tasks:
    This script can be extended with maintenance functions:

    - Recompute embeddings after model upgrade
    - Deduplicate near-identical chunks
    - Analyze chunk distribution across documents
    - Validate embedding quality and coverage
    - Clean up orphaned chunks
    - Rebuild vector indexes

    Example maintenance functions to add:

    ```python
    def recompute_embeddings(doc_id=None):
        # Regenerate embeddings for all or specific documents
        pass

    def find_duplicates(threshold=0.95):
        # Find and remove near-duplicate chunks
        pass

    def chunk_stats():
        # Analyze chunk count, size distribution, etc.
        pass
    ```

Why This Approach:
    - Simple and transparent: Easy to understand and debug
    - Fast: Vector search is highly optimized in pgvector
    - Flexible: Can easily adjust k, add filters, rerank results
    - Local: No API calls, no rate limits, no costs
    - Privacy: All data stays on your infrastructure
    - RAG-ready: Drop-in retrieval for LLM augmentation
"""

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
                   1 - (c.embedding <=> %s::vector) AS score
            FROM zen_chunks c
            JOIN zen_docs d ON d.id=c.doc_id
            ORDER BY c.embedding <-> %s::vector
            LIMIT %s
        """, (qv, qv, k))
        return cur.fetchall()

if __name__=="__main__":
    for r in search("What is awakening and how to relate to thoughts?", k=5):
        print(f"[{r['score']:.3f}] {r['title']} :: {r['content'][:140]}…")
