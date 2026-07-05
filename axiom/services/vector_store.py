"""ChromaDB integration for storing/retrieving function embeddings (PRD §7.2/§7.12).

Uses an HTTP Chroma client when CHROMA_URL is reachable, otherwise an in-process
ephemeral client so local development works without the Chroma service.
"""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from axiom.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

COLLECTION = "axiom_function_embeddings"


class VectorStore:
    """Thin wrapper over a ChromaDB collection keyed by function content_hash."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: Any = None
        self._collection: Any = None
        self._disabled = False

    def _ensure(self) -> Any:
        if self._collection is not None or self._disabled:
            return self._collection
        try:
            import chromadb
        except ImportError:
            # chromadb not installed at all — disable vector storage, keep pipeline alive.
            logger.warning("chromadb not installed; embeddings not persisted (static-only vectors).")
            self._disabled = True
            return None
        try:
            parsed = urlparse(self.settings.chroma_url)
            self._client = chromadb.HttpClient(
                host=parsed.hostname or "localhost", port=parsed.port or 8001
            )
            self._client.heartbeat()
            logger.info("Connected to ChromaDB at %s", self.settings.chroma_url)
        except Exception as exc:  # noqa: BLE001 - degrade to local ephemeral
            logger.warning("Chroma HTTP unavailable (%s); using in-process client", exc)
            self._client = chromadb.EphemeralClient()
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION, metadata={"hnsw:space": "cosine"}
        )
        return self._collection

    def upsert(self, function_id: str, embedding: list[float], metadata: dict[str, Any]) -> None:
        collection = self._ensure()
        if collection is None:
            return
        collection.upsert(ids=[function_id], embeddings=[embedding], metadatas=[metadata])

    def query_similar(self, embedding: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        """Return the top-K most semantically similar functions by cosine distance."""
        collection = self._ensure()
        if collection is None:
            return []
        res = collection.query(query_embeddings=[embedding], n_results=top_k)
        out: list[dict[str, Any]] = []
        ids = res.get("ids", [[]])[0]
        distances = res.get("distances", [[]])[0]
        metadatas = res.get("metadatas", [[]])[0]
        for fid, dist, meta in zip(ids, distances, metadatas):
            out.append({"function_id": fid, "distance": dist, "metadata": meta})
        return out

    def get(self, function_id: str) -> list[float] | None:
        collection = self._ensure()
        if collection is None:
            return None
        res = collection.get(ids=[function_id], include=["embeddings"])
        embeddings = res.get("embeddings")
        # chromadb returns numpy arrays — compare with len(), not truthiness.
        if embeddings is None or len(embeddings) == 0:
            return None
        return list(embeddings[0])


_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
