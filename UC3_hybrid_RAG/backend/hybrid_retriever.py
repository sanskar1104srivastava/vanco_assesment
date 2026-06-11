"""Hybrid retriever that combines ChromaDB, BM25, and Neo4j evidence."""

from __future__ import annotations

from pathlib import Path

from .bm25_search import BM25Retriever
from .chunker import load_chunks
from .config import Settings, get_settings
from .embeddings import SentenceTransformerEmbedder
from .graph_builder import GraphConfigError
from .graph_retriever import Neo4jGraphRetriever
from .logging_utils import get_logger
from .query_normalizer import normalize_query
from .schemas import HybridEvidence, RetrievalItem
from .vector_store import ChromaVectorStore


LOGGER = get_logger(__name__)


class IndexNotReadyError(RuntimeError):
    pass


class HybridRetriever:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        if not Path(self.settings.chunks_path).exists():
            raise IndexNotReadyError("Chunks are missing. Run ingestion first.")
        if not Path(self.settings.bm25_index_path).exists():
            raise IndexNotReadyError("BM25 index is missing. Run ingestion first.")

        self.chunks = load_chunks(self.settings.chunks_path)
        self.embedder = SentenceTransformerEmbedder(
            self.settings.embedding_model,
            normalize_embeddings=self.settings.embedding_normalize,
        )
        self.vector_store = ChromaVectorStore(self.settings, self.embedder)
        self.bm25 = BM25Retriever.load(self.settings.bm25_index_path)
        self.graph = None

    def _graph_retriever(self) -> Neo4jGraphRetriever:
        if self.graph is None:
            self.graph = Neo4jGraphRetriever(self.settings)
        return self.graph

    def retrieve(self, query: str, top_k: int | None = None) -> HybridEvidence:
        top_k = top_k or self.settings.default_top_k
        retrieval_query = normalize_query(query)
        if retrieval_query != query:
            LOGGER.info("Normalized retrieval query from %r to %r", query, retrieval_query)

        semantic = self.vector_store.query(retrieval_query, top_k)
        keyword = self.bm25.query(retrieval_query, top_k)

        graph_nodes = []
        graph_error = None
        try:
            graph_nodes = self._graph_retriever().query(retrieval_query, top_k)
        except GraphConfigError as exc:
            graph_error = str(exc)
            if self.settings.neo4j_required:
                raise
            LOGGER.warning("Graph retrieval unavailable: %s", exc)

        merged = self._merge_chunks(semantic, keyword)
        return HybridEvidence(
            semantic_chunks=semantic,
            keyword_chunks=keyword,
            graph_nodes=graph_nodes,
            merged_chunks=merged,
            graph_error=graph_error,
            original_query=query,
            retrieval_query=retrieval_query,
        )

    @staticmethod
    def _merge_chunks(semantic: list[RetrievalItem], keyword: list[RetrievalItem]) -> list[RetrievalItem]:
        by_id: dict[str, RetrievalItem] = {}
        for item in semantic + keyword:
            existing = by_id.get(item.id)
            if existing is None or item.score > existing.score:
                by_id[item.id] = RetrievalItem(
                    retrieval_type="hybrid",
                    id=item.id,
                    text=item.text,
                    metadata=item.metadata,
                    score=item.score,
                )
        return sorted(by_id.values(), key=lambda item: item.score, reverse=True)
