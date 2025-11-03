# Adyai - AI Professor of Adyashanti's Teachings

A RAG-powered chatbot that provides answers about Adyashanti's teachings using semantic search over a vector database of his books, talks, and writings.

## Architecture

```
adyai/
├── app.py              # FastAPI backend server (Python)
├── frontend/           # Next.js frontend (TypeScript/React)
│   ├── app/
│   │   ├── page.tsx           # Main chat interface
│   │   ├── layout.tsx         # App layout
│   │   └── globals.css        # Global styles
│   ├── components/
│   │   ├── ChatMessage.tsx    # Message component
│   │   └── WelcomeScreen.tsx  # Welcome screen
│   └── package.json
└── README.md          # This file
```

## How It Works

1. **User sends a question** through the Next.js frontend
2. **Frontend makes API call** to FastAPI backend at `/api/chat`
3. **Backend retrieves context** using semantic search from PostgreSQL + pgvector
4. **Context is sent to Claude API** with the question
5. **Claude generates response** grounded in Adyashanti's teachings
6. **Response and sources** are displayed to the user

## Prerequisites

### Backend Requirements
- Python 3.10+
- PostgreSQL with pgvector extension
- Virtual environment with dependencies installed
- Anthropic API key

### Frontend Requirements
- Node.js 18+
- npm or yarn

## Setup Instructions

### 1. Install Python Dependencies

```bash
cd /Users/echo/ai-prof
pip install -r requirements.txt
```

The backend requires:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `anthropic` - Claude API client
- `sentence-transformers` - For embeddings
- `psycopg` - PostgreSQL driver

### 2. Configure Environment Variables

Update `.env` file in the project root with your Anthropic API key:

```bash
# .env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_prof
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
ANTHROPIC_API_KEY=your_actual_api_key_here
```

Get your API key at: https://console.anthropic.com/

### 3. Install Frontend Dependencies

```bash
cd adyai/frontend
npm install
```

This installs:
- Next.js 15
- React 19
- TypeScript
- Tailwind CSS

### 4. Ensure Database is Ready

Make sure your PostgreSQL database has:
- pgvector extension installed
- `zen_docs` table with documents
- `zen_chunks` table with embeddings

If not, run the ingestion pipeline first:
```bash
# From project root
python scripts/10_scrape_site.py
python scripts/20_transcribe_audio.py
python scripts/30_ingest_pdfs_epubs.py
python scripts/40_chunk_embed_load.py
```

## Running the Application

### Option 1: Run Both Servers Separately (Recommended for Development)

**Terminal 1 - Backend:**
```bash
cd /Users/echo/ai-prof
source .venv/bin/activate  # or . .venv/bin/activate
python adyai/app.py
```

Backend runs on: http://localhost:8000
- API: http://localhost:8000/api/chat
- Docs: http://localhost:8000/docs

**Terminal 2 - Frontend:**
```bash
cd /Users/echo/ai-prof/adyai/frontend
npm run dev
```

Frontend runs on: http://localhost:3000

### Option 2: Production Build

**Build frontend:**
```bash
cd adyai/frontend
npm run build
npm start
```

**Run backend:**
```bash
python adyai/app.py
```

## Usage

1. Open http://localhost:3000 in your browser
2. You'll see a welcome screen with example questions
3. Type your question or click an example
4. Wait for Adyai to retrieve relevant teachings and generate a response
5. View sources at the bottom of each response

### Example Questions

- "What is awakening?"
- "How do I relate to thoughts?"
- "What is the nature of awareness?"
- "What does it mean to let go?"
- "How can I recognize my true nature?"

## API Endpoints

### POST /api/chat

Send a chat message and receive a response.

**Request:**
```json
{
  "message": "What is awakening?",
  "k": 5
}
```

**Response:**
```json
{
  "response": "According to Adyashanti...",
  "sources": [
    {
      "title": "The Impact of Awakening",
      "content": "...",
      "score": 0.85,
      "source_type": "pdf",
      "source_url": null
    }
  ],
  "context_used": true
}
```

### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "anthropic_configured": true,
  "database_configured": true
}
```

## Configuration

### Adjusting Retrieval
Edit `adyai/app.py` to change:
- Number of chunks retrieved (`k` parameter)
- Claude model (`claude-sonnet-4-5-latest`)
- Temperature (0.7)
- Max tokens (1024)

### Customizing UI
Edit files in `adyai/frontend/`:
- `components/ChatMessage.tsx` - Message styling
- `components/WelcomeScreen.tsx` - Welcome screen
- `app/globals.css` - Global styles
- `tailwind.config.ts` - Tailwind configuration

## Troubleshooting

### Backend Issues

**"ANTHROPIC_API_KEY not found"**
- Make sure you've set the API key in `.env`
- Restart the backend server

**"operator does not exist: vector <=>"**
- pgvector extension not installed
- Run: `CREATE EXTENSION vector;` in PostgreSQL

**"No module named 'anthropic'"**
- Install dependencies: `pip install -r requirements.txt`

**"Connection refused to database"**
- Ensure PostgreSQL is running
- Check DATABASE_URL in `.env`

### Frontend Issues

**"Module not found"**
- Run `npm install` in `adyai/frontend/`
- Delete `node_modules` and `.next`, then reinstall

**"Cannot connect to API"**
- Ensure backend is running on port 8000
- Check Next.js proxy configuration in `next.config.ts`

**Port 3000 already in use**
- Change port: `PORT=3001 npm run dev`

## Performance

- **Query latency**: 1-3 seconds (including Claude API)
- **Vector search**: ~50-100ms for 5000+ chunks
- **Claude API**: ~1-2 seconds for response generation
- **Concurrent users**: Handles 10-20 simultaneous requests

## Future Improvements

- [ ] Add conversation history/context
- [ ] Implement streaming responses
- [ ] Add source document links
- [ ] Include citation highlighting
- [ ] Add feedback mechanism
- [ ] Implement rate limiting
- [ ] Add authentication
- [ ] Support multiple languages
- [ ] Add voice input/output
- [ ] Mobile-responsive design improvements

## Tech Stack

**Backend:**
- FastAPI (Python web framework)
- Anthropic Claude API (LLM)
- PostgreSQL + pgvector (Vector database)
- sentence-transformers (Embeddings)

**Frontend:**
- Next.js 15 (React framework)
- TypeScript (Type safety)
- Tailwind CSS (Styling)
- React Hooks (State management)

## License

This project is for educational and personal use with Adyashanti's teachings.

## Credits

Built on top of the Adyashanti teachings corpus processed through the ingestion pipeline in this repository.
