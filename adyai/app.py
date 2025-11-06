"""
Adyai Chatbot Backend API

This FastAPI application provides a chatbot interface for querying Adyashanti's teachings
using Retrieval Augmented Generation (RAG). It combines semantic search over the vector
database with Claude AI to generate contextually grounded responses.

Architecture:
    1. User sends a question via POST /api/chat
    2. Backend retrieves top-k relevant chunks from vector database
    3. Context is formatted and sent to Claude API with the question
    4. Claude generates a response grounded in the retrieved teachings
    5. Response includes sources and similarity scores

Endpoints:
    - GET / : Serves the chatbot HTML interface
    - POST /api/chat : Processes chat messages and returns AI responses
    - GET /api/health : Health check endpoint

Configuration:
    - DATABASE_URL: PostgreSQL connection string (.env)
    - ANTHROPIC_API_KEY: Claude API key (.env)
    - EMBED_MODEL: Embedding model name (defaults to all-MiniLM-L6-v2)

Usage:
    python adyai/app.py
    # Server runs on http://localhost:8000
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import anthropic
from sentence_transformers import SentenceTransformer
import psycopg
from psycopg.rows import dict_row
import httpx

# Add parent directory to path to import from scripts
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Embedding configuration
USE_API_EMBEDDINGS = os.getenv("USE_API_EMBEDDINGS", "false").lower() == "true"
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "paraphrase-MiniLM-L3-v2")

print("="*60)
print("🔧 Embedding Configuration")
print("="*60)
if USE_API_EMBEDDINGS and OPENAI_API_KEY:
    print("✓ Using OpenAI API embeddings (no memory overhead)")
    print("  Model: text-embedding-3-small (1536 dims)")
    print("  ⚠️  WARNING: Database must contain OpenAI embeddings!")
    print("  If database has local model embeddings, re-embed first.")
else:
    if USE_API_EMBEDDINGS and not OPENAI_API_KEY:
        print("⚠️  USE_API_EMBEDDINGS=true but OPENAI_API_KEY not set")
        print("  Falling back to local model")
    print(f"✓ Using local model: {EMBED_MODEL_NAME}")
    print("  (Model will be lazy-loaded on first request)")
print("="*60)

if not ANTHROPIC_API_KEY:
    print("WARNING: ANTHROPIC_API_KEY not found in .env file")
    print("Please add: ANTHROPIC_API_KEY=your_key_here")

if not DATABASE_URL:
    print("WARNING: DATABASE_URL not found in .env file")

# Global variable to cache the embedding model after first load
_embedding_model = None

def get_embedding_model():
    """
    Lazy-load the embedding model on first use to avoid OOM at startup.
    This caches the model in memory after first load for fast subsequent requests.

    On Render free tier (512MB RAM), loading at startup causes OOM.
    Loading on first request allows the app to start successfully.
    """
    global _embedding_model
    if _embedding_model is None:
        print(f"Loading embedding model: {EMBED_MODEL_NAME} (first request will be slow)")
        _embedding_model = SentenceTransformer(EMBED_MODEL_NAME)
        print("✓ Embedding model loaded and cached")
    return _embedding_model

def get_embedding_vector(text: str) -> list:
    """
    Generate embedding vector for text using either OpenAI API or local model.
    Switches based on USE_API_EMBEDDINGS environment variable.

    - If USE_API_EMBEDDINGS=true and OPENAI_API_KEY is set: Use OpenAI API (no memory overhead)
    - Otherwise: Use local SentenceTransformer model (lazy-loaded, ~300MB memory)
    """
    if USE_API_EMBEDDINGS and OPENAI_API_KEY:
        # Use OpenAI API for embeddings
        try:
            with httpx.Client() as client:
                response = client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "text-embedding-3-small",
                        "input": text,
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            print(f"⚠️  OpenAI API embedding failed, falling back to local model: {e}")
            model = get_embedding_model()
            return model.encode([text], normalize_embeddings=True)[0].tolist()
    else:
        # Use local model
        model = get_embedding_model()
        return model.encode([text], normalize_embeddings=True)[0].tolist()

# Custom search function using cached model
def vector_search(query: str, k: int = 5):
    """
    Semantic search using either API embeddings or local model.
    Controlled by USE_API_EMBEDDINGS environment variable.
    """
    try:
        # Generate embedding vector
        query_vector = get_embedding_vector(query)

        # Query database
        with psycopg.connect(DATABASE_URL) as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT c.content, d.title, d.source_type, d.source_url,
                       1 - (c.embedding <=> %s::vector) AS score
                FROM zen_chunks c
                JOIN zen_docs d ON d.id=c.doc_id
                ORDER BY c.embedding <-> %s::vector
                LIMIT %s
            """, (query_vector, query_vector, k))
            return cur.fetchall()
    except Exception as e:
        print(f"Error in vector_search: {e}")
        raise

# Initialize FastAPI app
app = FastAPI(
    title="Adyai - AI Professor of Adyashanti's Teachings",
    description="A RAG-powered chatbot for exploring Adyashanti's wisdom",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    k: Optional[int] = 5  # Number of chunks to retrieve

class Source(BaseModel):
    title: str
    content: str
    score: float
    source_type: str
    source_url: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    sources: List[Source]
    context_used: bool

# Initialize Anthropic client
claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the chatbot HTML interface"""
    html_path = Path(__file__).parent / "templates" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(), status_code=200)
    return HTMLResponse(
        content="<h1>Adyai Chatbot</h1><p>Interface not found. Please create templates/index.html</p>",
        status_code=200
    )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "anthropic_configured": ANTHROPIC_API_KEY is not None,
        "database_configured": os.getenv("DATABASE_URL") is not None
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process chat messages using RAG

    Flow:
        1. Retrieve relevant chunks from vector database
        2. Format context for Claude
        3. Generate response using Claude API
        4. Return response with sources
    """
    try:
        # Step 1: Retrieve relevant context from vector database
        results = vector_search(request.message, k=request.k)

        if not results:
            return ChatResponse(
                response="I couldn't find any relevant teachings to answer your question. Please try rephrasing or ask about a different topic.",
                sources=[],
                context_used=False
            )

        # Step 2: Format sources
        sources = [
            Source(
                title=r["title"] or "Untitled",
                content=r["content"][:300] + "..." if len(r["content"]) > 300 else r["content"],
                score=float(r["score"]),
                source_type=r["source_type"],
                source_url=r.get("source_url")
            )
            for r in results
        ]

        # Step 3: Format context for Claude
        context_text = "\n\n---\n\n".join([
            f"[Source: {r['title']}]\n{r['content']}"
            for r in results
        ])

        # Step 4: Generate response using Claude
        if not claude_client:
            # Fallback if API key not configured
            return ChatResponse(
                response="⚠️ Anthropic API key not configured. Here are the most relevant passages I found:\n\n" +
                         "\n\n".join([f"• {r['content'][:200]}..." for r in results[:3]]),
                sources=sources,
                context_used=True
            )

        system_prompt = """You are Adyai, an AI assistant deeply versed in the teachings of Adyashanti,
a contemporary spiritual teacher known for his direct, clear approach to awakening and enlightenment.

Your role is to:
- Answer questions based ONLY on the provided context from Adyashanti's teachings
- Speak in a clear, compassionate, and direct tone similar to Adyashanti's style
- Point directly to truth and awareness, not just concepts
- If the context doesn't contain enough information, acknowledge this honestly
- Never make up teachings or attribute ideas to Adyashanti that aren't in the context
- When appropriate, ask questions that invite deeper inquiry

The context provided comes from Adyashanti's books, talks, and writings."""

        user_prompt = f"""Context from Adyashanti's teachings:

{context_text}

---

Question: {request.message}

Please provide a response based on the teachings in the context above. If the context doesn't fully address the question, say so."""

        # Try models in order of preference with fallback
        models = [
            "claude-sonnet-4-20250514",  # Best quality
            "claude-3-haiku-20240307"     # Fallback: faster, always available
        ]

        message = None
        last_error = None

        for model_name in models:
            try:
                print(f"Trying model: {model_name}")
                message = claude_client.messages.create(
                    model=model_name,
                    max_tokens=1024,
                    temperature=0.7,
                    system=system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ]
                )
                print(f"✓ Successfully used model: {model_name}")
                break  # Success, exit loop

            except anthropic.OverloadedError as e:
                print(f"✗ Model {model_name} is overloaded, trying next...")
                last_error = e
                continue

            except anthropic.NotFoundError as e:
                print(f"✗ Model {model_name} not found, trying next...")
                last_error = e
                continue

            except Exception as e:
                print(f"✗ Error with model {model_name}: {str(e)}")
                last_error = e
                continue

        if message is None:
            raise Exception(f"All models failed. Last error: {str(last_error)}")

        response_text = message.content[0].text

        return ChatResponse(
            response=response_text,
            sources=sources,
            context_used=True
        )

    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"\n{'='*60}")
        print(f"ERROR in /api/chat endpoint:")
        print(f"{'='*60}")
        print(error_traceback)
        print(f"{'='*60}\n")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("🧘 Starting Adyai - AI Professor of Adyashanti's Teachings")
    print("=" * 60)
    print(f"Server: http://localhost:8000")
    print(f"API Docs: http://localhost:8000/docs")
    print(f"Health Check: http://localhost:8000/api/health")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
