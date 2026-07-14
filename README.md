# AI Research Assistant Agent

An agentic AI research assistant that helps you investigate topics end-to-end — searching the web, reading PDFs, building RAG indexes, and generating cited research documents.

## Features

- **Agentic tool routing** — the LLM decides whether to search the web, read a URL/PDF, use RAG retrieval, or answer directly
- **Web search** via DuckDuckGo (no API key)
- **PDF upload & structured extraction** (abstract, methodology, results, etc.)
- **RAG pipeline** with Sentence Transformers + ChromaDB
- **Document generation** — summaries, literature reviews, comparison tables, reports, paper drafts
- **Real citations only** — APA, IEEE, or MLA bibliography from retrieved sources
- **Export** to PDF, DOCX, or Markdown
- **Session memory** — notes, saved papers, search history (SQLite)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite + TypeScript + Tailwind + shadcn/ui |
| Backend | Python + FastAPI |
| Agent | LangGraph + LangChain |
| LLM | Gemini 2.5 Flash (free tier) |
| Search | DuckDuckGo |
| Embeddings | Sentence Transformers (local) |
| Vector DB | ChromaDB (local) |
| Database | SQLite |

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Gemini API key** — free at [Google AI Studio](https://aistudio.google.com/apikey)

## Setup

### 1. Clone and configure environment

```bash
cd "D:\ai research assistant"
cp .env.example .env
```

Edit `.env` and set your `GEMINI_API_KEY`.

### 2. Backend

```bash
cd backend
python -m venv venv

# Windows (PowerShell)
venv\Scripts\Activate.ps1
# Windows (cmd)
venv\Scripts\activate.bat
# macOS/Linux
source venv/bin/activate

# (Recommended) install the CPU-only build of torch first — no GPU is needed,
# and this avoids pulling the much larger CUDA build via sentence-transformers:
pip install torch --index-url https://download.pytorch.org/whl/cpu

pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Health check: `http://localhost:8000/api/health`.

> **Python version:** use Python **3.11 or 3.12**. Prebuilt wheels for all
> dependencies are available for these versions, so no C/C++ compiler is
> required. (Python 3.14 has no prebuilt wheels for several packages yet.)

#### Troubleshooting

- **`sentence-transformers` / `torch` install is slow or fails** — install the
  CPU-only torch wheel first (see the command above), then re-run
  `pip install -r requirements.txt`.
- **`Microsoft Visual C++ 14.0 or greater is required`** — this happens with
  older `chromadb`/`chroma-hnswlib` pins that build native code from source.
  The pinned `chromadb==1.0.15` ships prebuilt wheels and does **not** need a
  compiler; make sure you're installing from the provided `requirements.txt`.
- **First request is slow** — the local embedding model (~90 MB) downloads on
  first use and is then cached.
- **The backend starts but chat returns a "GEMINI_API_KEY is not configured"
  error** — this is expected until you add a real key to `.env`. Everything
  except the LLM calls (PDF upload, RAG indexing, exports, saved notes/papers)
  works without a key.

### 3. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

## Usage

1. **Ask a research question** in the chat — the agent will search the web and synthesize findings with citations.
2. **Request a literature review** — e.g. "Write a literature review on federated learning for healthcare."
3. **Upload a PDF** — click the paperclip icon; the agent extracts structured sections and enables RAG Q&A.
4. **Paste a URL** — ask the agent to read and summarize a website or YouTube video.
5. **Export** — use the Export buttons in the right panel (PDF / DOCX / Markdown).

## Environment Variables

See `.env.example` for the full list. Required:

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `JWT_SECRET` | Secret for session tokens |

## Project Structure

```
├── frontend/          React + Vite UI
├── backend/
│   ├── app.py         FastAPI entry point
│   ├── agents/        Research, Writing, Citation, Review agents
│   ├── tools/         Search, PDF, web scraper, YouTube
│   ├── rag/           Embeddings, ChromaDB, retriever
│   ├── api/           REST endpoints
│   ├── exports/       PDF/DOCX/Markdown export
│   └── database/      SQLite models
├── .env.example
├── README.md
└── DECISIONS.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat` | Send message to research agent |
| POST | `/api/documents/upload` | Upload PDF |
| POST | `/api/documents/export` | Export document |
| GET | `/api/sessions` | List sessions |
| GET | `/api/notes` | List notes |
| GET | `/api/papers` | List saved papers |
| GET | `/api/health` | Health check |

## License

MIT
