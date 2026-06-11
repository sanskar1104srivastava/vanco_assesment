"""Sentence-transformer embedding wrapper."""

from __future__ import annotations

from .logging_utils import get_logger


LOGGER = get_logger(__name__)


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str, normalize_embeddings: bool = True) -> None:
        self.model_name = model_name
        self.normalize_embeddings = normalize_embeddings
        self._model = None

    @property
    def model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError("sentence-transformers is required for embeddings") from exc
            LOGGER.info("Loading embedding model %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        LOGGER.info("Generating embeddings for %s documents", len(texts))
        vectors = self.model.encode(
            texts,
            normalize_embeddings=self.normalize_embeddings,
            show_progress_bar=True,
        )
        return [vector.tolist() for vector in vectors]

    def embed_query(self, text: str) -> list[float]:
        vector = self.model.encode(
            [text],
            normalize_embeddings=self.normalize_embeddings,
            show_progress_bar=False,
        )[0]
        return vector.tolist()

