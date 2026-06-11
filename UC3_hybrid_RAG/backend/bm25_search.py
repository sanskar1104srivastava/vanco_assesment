"""Independent BM25 keyword retrieval."""

from __future__ import annotations

import pickle
import re
from pathlib import Path

from .logging_utils import get_logger
from .schemas import DocumentChunk, RetrievalItem


LOGGER = get_logger(__name__)
TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


class BM25Retriever:
    def __init__(self) -> None:
        self.chunks: list[DocumentChunk] = []
        self._bm25 = None

    def build(self, chunks: list[DocumentChunk]) -> None:
        try:
            from rank_bm25 import BM25Okapi
        except ImportError as exc:
            raise RuntimeError("rank-bm25 is required for keyword retrieval") from exc

        self.chunks = chunks
        corpus = [tokenize(chunk.text) for chunk in chunks]
        self._bm25 = BM25Okapi(corpus)
        LOGGER.info("Built BM25 index for %s chunks", len(chunks))

    def save(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as file:
            pickle.dump({"chunks": self.chunks, "bm25": self._bm25}, file)
        LOGGER.info("Saved BM25 index to %s", path)

    @classmethod
    def load(cls, path: str) -> "BM25Retriever":
        with open(path, "rb") as file:
            payload = pickle.load(file)
        retriever = cls()
        retriever.chunks = payload["chunks"]
        retriever._bm25 = payload["bm25"]
        return retriever

    def query(self, query: str, top_k: int) -> list[RetrievalItem]:
        LOGGER.info("Running BM25 retrieval top_k=%s", top_k)
        if self._bm25 is None or not self.chunks:
            return []

        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)[:top_k]
        results: list[RetrievalItem] = []
        max_score = float(max(scores)) if len(scores) else 0.0
        for index, score in ranked:
            chunk = self.chunks[index]
            normalised = float(score / max_score) if max_score > 0 else 0.0
            results.append(
                RetrievalItem(
                    retrieval_type="keyword",
                    id=chunk.id,
                    text=chunk.text,
                    metadata=chunk.metadata,
                    score=normalised,
                )
            )
        return results
