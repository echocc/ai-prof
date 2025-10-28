CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS zen_docs (
  id UUID PRIMARY KEY,
  source_type TEXT CHECK (source_type IN ('web','audio','pdf','epub','manual')),
  title TEXT,
  author TEXT,
  source_url TEXT,
  source_path TEXT,
  published_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  hash TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS zen_chunks (
  id UUID PRIMARY KEY,
  doc_id UUID REFERENCES zen_docs(id) ON DELETE CASCADE,
  chunk_index INT,
  content TEXT,
  section TEXT,
  token_count INT,
  embedding VECTOR(384),
  metadata JSONB,
  UNIQUE(doc_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS zen_chunks_embedding_idx ON zen_chunks
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
