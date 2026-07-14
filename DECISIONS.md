# Architecture & Design Decisions

This document records judgment calls made while building the AI Research Assistant Agent.

## Frontend: Vite + React (not Next.js)

**Decision:** Vite + React SPA.

**Why:** The app is a single-page workspace with a three-pane layout and no need for SSR, SEO, or file-based routing. Vite offers faster local dev startup, simpler deployment, and a lighter footprint than Next.js for this use case.

## Agent Framework: LangGraph (not plain LangChain chains)

**Decision:** LangGraph with a tool-calling loop.

**Why:** LangGraph gives a clean state-machine graph (`agent → tools → agent → …`) that matches the requirement for genuine LLM-driven tool routing. A fixed if/else pipeline would violate the "agentic" requirement. LangGraph's `ToolNode` and conditional edges keep the loop explicit and debuggable.

## LLM: Gemini 2.5 Flash via abstraction layer

**Decision:** `GeminiLLMService` behind a `LLMService` ABC in `services/llm_service.py`.

**Why:** Meets the free-tier requirement and keeps the rest of the codebase provider-agnostic. Swapping to another model means implementing one class, not refactoring agents.

## Embeddings: Sentence Transformers (local)

**Decision:** `all-MiniLM-L6-v2` running locally.

**Why:** Zero cost, no API key, reasonable quality for RAG over research documents. First run downloads the model (~90 MB).

## Vector DB: ChromaDB (embedded)

**Decision:** Persistent local ChromaDB, one collection per session.

**Why:** No hosted service or credit card required. Collections are namespaced by session ID for isolation.

## Web Search: DuckDuckGo

**Decision:** `duckduckgo-search` Python package.

**Why:** Free, no API key. Trade-off: less reliable than paid search APIs and rate-limited; acceptable for a local research tool.

## Auth: Optional JWT with guest mode

**Decision:** Simple JWT auth with a default guest user; no third-party auth.

**Why:** Per-user memory (notes, papers, history) needs some identity, but requiring signup would friction a local dev tool. Guest mode lets users start immediately; register/login endpoints exist for persistence across browser clears.

## Document Generation Pipeline

**Decision:** Three-agent pipeline — Research → Writing → Review.

**Why:**
- **Research Agent** gathers sources via tools (search, scrape, RAG).
- **Writing Agent** drafts the requested document type from verified sources only.
- **Review Agent** polishes grammar/clarity without adding new claims or citations.

The Citation Agent formats bibliographies separately to enforce "real sources only."

## PDF Extraction: Heuristic section parsing

**Decision:** Regex/heuristic section detection in `pdf_reader.py`, not an LLM pass.

**Why:** Faster, free, and works offline. LLM-based extraction could be added later for messy PDFs.

## UI Design

**Decision:** Muted navy accent on off-white, serif document preview, three-pane desktop / tab-bar mobile.

**Why:** Matches the brief for a calm, editorial, trustworthy research tool — not a generic chatbot clone.

## SQLite for Development

**Decision:** SQLite via SQLAlchemy async (`aiosqlite`).

**Why:** Zero setup, file-based, sufficient for local single-user/dev use. Can migrate to PostgreSQL later by changing `DATABASE_URL`.

## Export: reportlab + python-docx

**Decision:** Server-side export generation.

**Why:** Consistent output regardless of browser; supports PDF, DOCX, and Markdown from the same content payload.

## Known Limitations

1. **DuckDuckGo rate limits** — heavy search usage may be throttled.
2. **Gemini free tier quotas** — daily request limits apply.
3. **First embedding model load** — slow cold start while Sentence Transformers downloads.
4. **YouTube transcripts** — only available when the video has captions.
5. **PDF section extraction** — heuristic; non-standard paper layouts may miss sections.
6. **LangGraph sync invoke** — agent runs synchronously inside async endpoints; fine for local use, would need `ainvoke` + worker queue at scale.

---

# Continuation Session — Setup, Fixes & Verification

The following decisions were made while resuming the project, getting both
servers running, and doing an end-to-end verification pass.

## Recreated the backend virtualenv with Python 3.12

**Decision:** Deleted and recreated `backend/venv` using Python 3.12.

**Why:** The existing `venv` was unusable — its `pyvenv.cfg` pointed at a
base interpreter (`C:\Program Files\Python314`) that no longer exists, and the
project had also been moved (`D:\ai research assistant` → `d:\Projects\ai research assistant`).
A venv can't be repaired once its base Python is gone. Python 3.12 was the
available interpreter and has prebuilt wheels for every dependency (no compiler
needed). The instruction to "reuse the existing venv" assumed it was
salvageable; it was not.

## Bumped `chromadb` 0.6.3 → 1.0.15

**Decision:** Updated the `chromadb` pin in `requirements.txt`.

**Why:** `chromadb==0.6.3` depends on `chroma-hnswlib==0.7.6`, which has no
prebuilt Windows wheel for Python 3.12 and tries to compile a C++ extension —
failing with "Microsoft Visual C++ 14.0 or greater is required." `chromadb`
1.x ships a prebuilt vector index and needs no compiler. The public API used
here (`PersistentClient`, `get_or_create_collection`, `add`, `query`,
`count`, `delete_collection`) is unchanged, so no code changes were required.

## Replaced `duckduckgo-search` 7.2.1 → `ddgs` 9.14.4

**Decision:** Switched the search dependency and rewrote `tools/search_tool.py`.

**Why:** The pinned `duckduckgo-search==7.2.1` consistently returned
`202 Ratelimit` and warned that its bundled browser-impersonation profiles were
outdated — current DuckDuckGo endpoints reject that client. The package was
renamed to `ddgs`; the current release returns real results. The rewrite keeps
the same output shape and adds a short retry/backoff on rate limits plus
graceful empty-list degradation on any search error.

## Fail-fast, on-brand LLM error handling

**Decision:** Added `MissingAPIKeyError` in `services/llm_service.py` (raised
only when an LLM call is actually attempted with an empty/placeholder key), and
an error classifier in `api/chat.py` that maps errors to clean HTTP responses
(400 for missing/invalid key, 429 for quota/rate limits, 500 otherwise).

**Why:** With no key, `langchain-google-genai` fell back to Application Default
Credentials and produced a confusing "credentials were not found" message. The
app now starts fine with a placeholder key and only fails — with a clear,
actionable message — when the user actually sends a chat.

## Lightweight toast system instead of extra shadcn components

**Decision:** Added a small dependency-free `ToastProvider`/`useToast`
(`components/ui/toast.tsx`) and surfaced errors/success through it. Kept the
existing native `<input>`/`<select>`/`<textarea>` controls rather than adding
shadcn `input`/`select`/`dialog`/etc. wrappers.

**Why:** The only UI primitive the app genuinely needed for clean error/success
states was toasts. The native controls are already styled on-brand and work
correctly, so wrapping them in unused shadcn components would add surface area
without benefit.

## Added save-note / favorite-paper UI

**Decision:** Added a "New Note" composer in the sidebar Notes tab and a
per-source "save to library" (bookmark) action under assistant messages, wired
to the existing `/api/notes` and `/api/papers` endpoints.

**Why:** The backend and sidebar already supported notes and saved papers, but
there was no way to create them from the UI, so that persistence path couldn't
be exercised. The sidebar now refreshes after activity so new items appear
without a page reload.

## Mobile layout fix

**Decision:** Removed `hidden lg:flex` from the `DocumentPanel` aside and made
`DocumentPanel`/`Sidebar` widths responsive (`w-full lg:w-96` / `w-full lg:w-64`).

**Why:** The document panel's own `hidden lg:flex` overrode the mobile tab
switch, so tapping the "Document" tab on mobile showed an empty pane. Panel
visibility is now controlled solely by the mobile tab wrapper.

## Recorded `results_count` for search history

**Decision:** Set `SearchHistory.results_count` to the number of sources found
for each chat turn.

**Why:** The column existed and was surfaced in the schema but was always left
at its `"0"` default.
