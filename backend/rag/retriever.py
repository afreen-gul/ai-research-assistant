"""RAG retriever — chunk, store, and retrieve relevant document sections."""

import logging
import re
from typing import Any

from config import settings
from rag.vector_store import get_vector_store

logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    chunk_size = chunk_size or settings.chunk_size
    overlap = overlap or settings.chunk_overlap
    if not text.strip():
        return []

    paragraphs = re.split(r"\n\s*\n", text)
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}".strip() if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) <= chunk_size:
                current = para
            else:
                words = para.split()
                current = ""
                for word in words:
                    if len(current) + len(word) + 1 <= chunk_size:
                        current = f"{current} {word}".strip()
                    else:
                        if current:
                            chunks.append(current)
                        current = word

    if current:
        chunks.append(current)

    if overlap > 0 and len(chunks) > 1:
        overlapped: list[str] = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-overlap:]
            overlapped.append(f"{prev_tail} {chunks[i]}")
        chunks = overlapped

    return chunks


def ingest_document(
    session_id: str,
    text: str,
    source_id: str,
    source_title: str = "",
    source_type: str = "document",
) -> int:
    chunks = chunk_text(text)
    if not chunks:
        return 0
    metadatas = [
        {"source_id": source_id, "source_title": source_title, "source_type": source_type, "chunk_index": i}
        for i in range(len(chunks))
    ]
    store = get_vector_store()
    return store.add_chunks(session_id, chunks, metadatas, source_id)


def retrieve_context(session_id: str, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
    store = get_vector_store()
    results = store.query(session_id, query, top_k)
    logger.info("Retrieved %d chunks for query in session %s", len(results), session_id)
    return results


def format_retrieved_context(results: list[dict[str, Any]]) -> str:
    if not results:
        return "No relevant document sections found."
    parts = []
    for i, r in enumerate(results, 1):
        meta = r.get("metadata", {})
        title = meta.get("source_title", "Unknown source")
        parts.append(f"[{i}] From: {title}\n{r['content']}")
    return "\n\n---\n\n".join(parts)
