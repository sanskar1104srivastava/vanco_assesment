"""ChromaDB vector store integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import Settings
from .embeddings import SentenceTransformerEmbedder
from .logging_utils import get_logger
from .schemas import DocumentChunk, RetrievalItem


LOGGER = get_logger(__name__)


def _chroma_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
    clean: dict[str, str | int | float | bool] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            clean[key] = value
        else:
            clean[key] = str(value)
    return clean


class ChromaVectorStore:
    def __init__(self, settings: Settings, embedder: SentenceTransformerEmbedder) -> None:
        self.settings = settings
        self.embedder = embedder
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError("chromadb is required for semantic vector retrieval") from exc

        Path(settings.chroma_path).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=settings.chroma_path)
        self.collection_name = settings.chroma_collection
        self.collection_metadata = {"hnsw:space": "cosine"}
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata=self.collection_metadata,
        )

    def reset_collection(self) -> None:
        LOGGER.info("Resetting ChromaDB collection %s", self.collection_name)
        try:
            self.client.delete_collection(name=self.collection_name)
        except Exception as exc:
            LOGGER.info("ChromaDB collection %s did not need deletion: %s", self.collection_name, exc)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata=self.collection_metadata,
        )

    def upsert_chunks(self, chunks: list[DocumentChunk], batch_size: int = 64) -> None:
        LOGGER.info("Upserting %s chunks into ChromaDB", len(chunks))
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            embeddings = self.embedder.embed_documents([chunk.text for chunk in batch])
            self.collection.upsert(
                ids=[chunk.id for chunk in batch],
                documents=[chunk.text for chunk in batch],
                metadatas=[_chroma_metadata(chunk.metadata) for chunk in batch],
                embeddings=embeddings,
            )
        LOGGER.info("ChromaDB collection %s now has %s records", self.settings.chroma_collection, self.count())

    def query(self, query: str, top_k: int) -> list[RetrievalItem]:
        LOGGER.info("Running semantic retrieval top_k=%s", top_k)
        if self.count() == 0:
            return []
        query_embedding = self.embedder.embed_query(query)
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        items: list[RetrievalItem] = []
        for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
            score = 1.0 - float(distance)
            items.append(
                RetrievalItem(
                    retrieval_type="semantic",
                    id=chunk_id,
                    text=text,
                    metadata=dict(metadata or {}),
                    score=score,
                )
            )
        return items

    def count(self) -> int:
        return int(self.collection.count())
