"""FastAPI application for ingestion and live question answering."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .answer_generator import AnswerGenerator
from .config import get_settings
from .hybrid_retriever import HybridRetriever, IndexNotReadyError
from .ingest import run_ingestion
from .logging_utils import get_logger


LOGGER = get_logger(__name__)

app = FastAPI(title="Vanco Hybrid RAG", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_retriever: HybridRetriever | None = None


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)


class IngestRequest(BaseModel):
    pdf_path: str | None = None
    reset_graph: bool = False


def _get_retriever(force_reload: bool = False) -> HybridRetriever:
    global _retriever
    if _retriever is None or force_reload:
        _retriever = HybridRetriever(get_settings(reload=True))
    return _retriever


@app.get("/health")
def health() -> dict[str, object]:
    settings = get_settings(reload=True)
    return {
        "status": "ok",
        "pdf_exists": Path(settings.pdf_path).exists(),
        "chunks_exists": Path(settings.chunks_path).exists(),
        "bm25_exists": Path(settings.bm25_index_path).exists(),
        "chroma_path": settings.chroma_path,
        "neo4j_configured": bool(settings.neo4j_uri and settings.neo4j_username and settings.neo4j_password),
        "llm_provider": settings.llm_provider,
    }


@app.post("/ingest")
def ingest(request: IngestRequest) -> dict[str, object]:
    try:
        settings = get_settings(reload=True)
        if request.pdf_path:
            settings = replace(settings, pdf_path=str(Path(request.pdf_path).expanduser().resolve()))
        result = run_ingestion(settings=settings, reset_graph=request.reset_graph)
        _get_retriever(force_reload=True)
        return result
    except Exception as exc:
        LOGGER.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ask")
def ask(request: AskRequest) -> dict[str, object]:
    try:
        retriever = _get_retriever()
        evidence = retriever.retrieve(request.question, request.top_k)
        answer = AnswerGenerator(get_settings()).answer(request.question, evidence)
        return answer.to_dict()
    except IndexNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        LOGGER.exception("Question answering failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

