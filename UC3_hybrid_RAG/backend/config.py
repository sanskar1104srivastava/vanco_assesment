"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_env_file() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        # python-dotenv is optional during early local checks.
        return


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    if value is None or value.strip() == "":
        return default
    return int(value)


def _abs_path(path: str) -> str:
    return str(Path(path).expanduser().resolve())


@dataclass(frozen=True)
class Settings:
    pdf_path: str
    source_name: str
    chunk_size: int
    chunk_overlap: int
    chunks_path: str
    chroma_path: str
    chroma_collection: str
    bm25_index_path: str
    embedding_model: str
    embedding_normalize: bool
    logs_path: str
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str
    neo4j_database: str
    neo4j_required: bool
    llm_provider: str
    groq_api_key: str
    groq_base_url: str
    groq_model: str
    openai_api_key: str
    openai_model: str
    ollama_base_url: str
    ollama_model: str
    mistral_api_key: str
    mistral_model: str
    llama_base_url: str
    llama_model: str
    max_context_chars: int
    default_top_k: int


_CACHED_SETTINGS: Settings | None = None


def get_settings(reload: bool = False) -> Settings:
    global _CACHED_SETTINGS
    if _CACHED_SETTINGS is not None and not reload:
        return _CACHED_SETTINGS

    _load_env_file()

    settings = Settings(
        pdf_path=_abs_path(os.getenv("PDF_PATH", "data/physics.pdf")),
        source_name=os.getenv("SOURCE_NAME", "NCERT_Physics_Part1.pdf"),
        chunk_size=_as_int(os.getenv("CHUNK_SIZE"), 350),
        chunk_overlap=_as_int(os.getenv("CHUNK_OVERLAP"), 100),
        chunks_path=_abs_path(os.getenv("CHUNKS_PATH", "data/chunks.json")),
        chroma_path=_abs_path(os.getenv("CHROMA_PATH", "chroma_db")),
        chroma_collection=os.getenv("CHROMA_COLLECTION", "ncert_physics"),
        bm25_index_path=_abs_path(os.getenv("BM25_INDEX_PATH", "data/bm25_index.pkl")),
        embedding_model=os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"),
        embedding_normalize=_as_bool(os.getenv("EMBEDDING_NORMALIZE"), True),
        logs_path=_abs_path(os.getenv("LOGS_PATH", "logs")),
        neo4j_uri=os.getenv("NEO4J_URI", ""),
        neo4j_username=os.getenv("NEO4J_USERNAME", ""),
        neo4j_password=os.getenv("NEO4J_PASSWORD", ""),
        neo4j_database=os.getenv("NEO4J_DATABASE", "neo4j"),
        neo4j_required=_as_bool(os.getenv("NEO4J_REQUIRED"), True),
        llm_provider=os.getenv("LLM_PROVIDER", "ollama").strip().lower(),
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        groq_base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1"),
        mistral_api_key=os.getenv("MISTRAL_API_KEY", ""),
        mistral_model=os.getenv("MISTRAL_MODEL", "mistral-large-latest"),
        llama_base_url=os.getenv("LLAMA_BASE_URL", "http://localhost:8080"),
        llama_model=os.getenv("LLAMA_MODEL", "llama"),
        max_context_chars=_as_int(os.getenv("MAX_CONTEXT_CHARS"), 14000),
        default_top_k=_as_int(os.getenv("DEFAULT_TOP_K"), 5),
    )
    _CACHED_SETTINGS = settings
    return settings
