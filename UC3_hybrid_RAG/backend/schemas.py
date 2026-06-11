"""Dataclasses used across the Hybrid RAG pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


Metadata = dict[str, Any]


@dataclass
class ParsedPage:
    page: int
    text: str
    chapter: str
    section: str
    source: str
    formulas: list[str] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)

    @property
    def metadata(self) -> Metadata:
        return {
            "page": self.page,
            "chapter": self.chapter,
            "section": self.section,
            "source": self.source,
            "formula_count": len(self.formulas),
            "table_count": len(self.tables),
        }


@dataclass
class DocumentChunk:
    id: str
    text: str
    metadata: Metadata

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DocumentChunk":
        return cls(id=payload["id"], text=payload["text"], metadata=payload["metadata"])


@dataclass
class RetrievalItem:
    retrieval_type: str
    id: str
    text: str
    metadata: Metadata
    score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GraphEvidence:
    node_label: str
    node_name: str
    relationship: str
    neighbor_label: str
    neighbor_name: str
    metadata: Metadata
    score: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HybridEvidence:
    semantic_chunks: list[RetrievalItem] = field(default_factory=list)
    keyword_chunks: list[RetrievalItem] = field(default_factory=list)
    graph_nodes: list[GraphEvidence] = field(default_factory=list)
    merged_chunks: list[RetrievalItem] = field(default_factory=list)
    graph_error: str | None = None
    original_query: str = ""
    retrieval_query: str = ""

    def has_context(self) -> bool:
        return bool(self.merged_chunks or self.graph_nodes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "semantic_chunks": [item.to_dict() for item in self.semantic_chunks],
            "keyword_chunks": [item.to_dict() for item in self.keyword_chunks],
            "graph_nodes": [item.to_dict() for item in self.graph_nodes],
            "merged_chunks": [item.to_dict() for item in self.merged_chunks],
            "graph_error": self.graph_error,
            "original_query": self.original_query,
            "retrieval_query": self.retrieval_query,
        }


@dataclass(frozen=True)
class Citation:
    chapter: str
    section: str
    page: str
    source: str

    def to_text(self) -> str:
        return f"Chapter: {self.chapter}\nSection: {self.section}\nPage: {self.page}"


@dataclass
class AnswerResult:
    answer: str
    citations: list[Citation]
    evidence: HybridEvidence
    latency_ms: float
    debug: Metadata = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": [asdict(citation) for citation in self.citations],
            "evidence": self.evidence.to_dict(),
            "latency_ms": self.latency_ms,
            "debug": self.debug,
        }
