"""ChromaDB vector store for document chunks."""

import logging
import uuid
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from config import settings
from rag.embeddings import embed_texts

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self) -> None:
        settings.ensure_dirs()
        self._client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def _collection_name(self, session_id: str) -> str:
        safe = session_id.replace("-", "_")[:63]
        return f"session_{safe}"

    def get_or_create_collection(self, session_id: str):
        return self._client.get_or_create_collection(
            name=self._collection_name(session_id),
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(
        self,
        session_id: str,
        chunks: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        source_id: str | None = None,
    ) -> int:
        if not chunks:
            return 0
        collection = self.get_or_create_collection(session_id)
        embeddings = embed_texts(chunks)
        ids = [str(uuid.uuid4()) for _ in chunks]
        meta = metadatas or [{} for _ in chunks]
        if source_id:
            meta = [{**m, "source_id": source_id} for m in meta]
        collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=meta)
        logger.info("Added %d chunks to collection for session %s", len(chunks), session_id)
        return len(chunks)

    def query(self, session_id: str, query_text: str, top_k: int | None = None) -> list[dict]:
        top_k = top_k or settings.retrieval_top_k
        collection = self.get_or_create_collection(session_id)
        if collection.count() == 0:
            return []
        from rag.embeddings import embed_query

        query_embedding = embed_query(query_text)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        items = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                items.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })
        return items

    def delete_session(self, session_id: str) -> None:
        name = self._collection_name(session_id)
        try:
            self._client.delete_collection(name)
        except Exception:
            logger.debug("Collection %s not found for deletion", name)


_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
