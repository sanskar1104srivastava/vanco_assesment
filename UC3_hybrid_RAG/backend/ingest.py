"""PDF ingestion pipeline and CLI entrypoint."""

from __future__ import annotations

import argparse
import re
from dataclasses import replace
from pathlib import Path

from .bm25_search import BM25Retriever
from .chunker import chunk_pages, save_chunks
from .config import Settings, get_settings
from .embeddings import SentenceTransformerEmbedder
from .graph_builder import GraphConfigError, Neo4jGraphBuilder
from .logging_utils import get_logger
from .schemas import ParsedPage
from .vector_store import ChromaVectorStore


LOGGER = get_logger(__name__)

SECTION_RE = re.compile(r"^\s*(\d+(?:\.\d+)+)\s+(.{3,100})$")
CHAPTER_NUMBER_RE = re.compile(
    r"^\s*(?:chapter\s+)?(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(.{4,90})$",
    re.IGNORECASE,
)
CHAPTER_WORD_RE = re.compile(r"^\s*chapter\s+([A-Z]+|\d+)\s*$", re.IGNORECASE)
FORMULA_HINT_RE = re.compile(r"(=|\\frac|\\sqrt|proportional to|therefore|where\s+[A-Za-z]\s*=)")
BODY_TEXT_HINT_RE = re.compile(r"\b(is|are|was|were|has|have|can|will|would|should|because|therefore)\b", re.IGNORECASE)


def _title(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    return text.title() if text.isupper() else text


def _clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def _is_heading_candidate(line: str) -> bool:
    line = _clean_line(line)
    if not 4 <= len(line) <= 90:
        return False
    if line.endswith((".", ",", ";", ":", "?", "!")):
        return False
    if any(symbol in line for symbol in ["=", "|", "\\sqrt", "\\frac"]):
        return False

    words = re.findall(r"[A-Za-z][A-Za-z&/-]*", line)
    if not 1 <= len(words) <= 10:
        return False
    if sum(char.isdigit() for char in line) > 4:
        return False

    alpha_chars = [char for char in line if char.isalpha()]
    if not alpha_chars:
        return False

    uppercase_ratio = sum(char.isupper() for char in alpha_chars) / len(alpha_chars)
    titlecase_words = sum(1 for word in words if word[0].isupper())
    titlecase_ratio = titlecase_words / len(words)

    if uppercase_ratio >= 0.65:
        return True
    if titlecase_ratio >= 0.75 and not BODY_TEXT_HINT_RE.search(line):
        return True
    return False


def _detect_formula_lines(text: str) -> list[str]:
    formulas: list[str] = []
    for raw_line in text.splitlines():
        line = _clean_line(raw_line)
        if not line or len(line) > 180:
            continue
        if FORMULA_HINT_RE.search(line) and any(char.isdigit() or char.isalpha() for char in line):
            formulas.append(line)
    return formulas[:20]


def _table_to_markdown(table: list[list[object]]) -> str:
    rows = [
        ["" if cell is None else _clean_line(str(cell)) for cell in row]
        for row in table
        if any(cell not in (None, "") for cell in row)
    ]
    if not rows:
        return ""

    width = max(len(row) for row in rows)
    normalised = [row + [""] * (width - len(row)) for row in rows]
    header = normalised[0]
    separator = ["---"] * width
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    for row in normalised[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _extract_tables(pdf_path: str) -> dict[int, list[str]]:
    try:
        import pdfplumber
    except ImportError as exc:
        raise RuntimeError("pdfplumber is required for table-preserving PDF ingestion") from exc

    tables_by_page: dict[int, list[str]] = {}
    with pdfplumber.open(pdf_path) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            page_tables: list[str] = []
            for table in page.extract_tables() or []:
                markdown = _table_to_markdown(table)
                if markdown:
                    page_tables.append(markdown)
            if page_tables:
                tables_by_page[index] = page_tables
    return tables_by_page


def _update_headings(
    text: str,
    current_chapter: str,
    current_section: str,
) -> tuple[str, str]:
    pending_chapter = False
    pending_chapter_lines = 0
    for raw_line in text.splitlines():
        line = _clean_line(raw_line)
        if not line:
            continue

        section_match = SECTION_RE.match(line)
        if section_match and _is_heading_candidate(section_match.group(2)):
            current_section = f"{section_match.group(1)} {_title(section_match.group(2))}"
            continue

        chapter_match = CHAPTER_NUMBER_RE.match(line)
        if chapter_match and _is_heading_candidate(chapter_match.group(1)):
            current_chapter = _title(chapter_match.group(1))
            current_section = "Chapter Overview"
            pending_chapter = False
            pending_chapter_lines = 0
            continue

        if CHAPTER_WORD_RE.match(line):
            pending_chapter = True
            pending_chapter_lines = 0
            continue

        if pending_chapter and _is_heading_candidate(line):
            current_chapter = _title(line)
            current_section = "Chapter Overview"
            pending_chapter = False
            pending_chapter_lines = 0
            continue

        if pending_chapter:
            pending_chapter_lines += 1
            if pending_chapter_lines >= 4:
                pending_chapter = False
                pending_chapter_lines = 0

    return current_chapter, current_section


def parse_pdf(pdf_path: str, source_name: str) -> list[ParsedPage]:
    """Parse a PDF into page records with page, chapter, section, formulas, and tables."""
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF not found at {pdf_path}")

    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for PDF text ingestion") from exc

    LOGGER.info("Starting PDF ingestion for %s", pdf_path)
    tables_by_page = _extract_tables(pdf_path)
    pages: list[ParsedPage] = []
    current_chapter = "Unknown Chapter"
    current_section = "Unknown Section"

    with fitz.open(pdf_path) as doc:
        for index, page in enumerate(doc, start=1):
            text = page.get_text("text", sort=True)
            current_chapter, current_section = _update_headings(text, current_chapter, current_section)
            tables = tables_by_page.get(index, [])
            formulas = _detect_formula_lines(text)

            table_text = ""
            if tables:
                table_text = "\n\nTables extracted from this page:\n" + "\n\n".join(tables)

            pages.append(
                ParsedPage(
                    page=index,
                    text=(text.strip() + table_text).strip(),
                    chapter=current_chapter,
                    section=current_section,
                    source=source_name,
                    formulas=formulas,
                    tables=tables,
                )
            )

    LOGGER.info("Parsed %s PDF pages", len(pages))
    return pages


def run_ingestion(
    settings: Settings | None = None,
    pdf_path: str | None = None,
    reset_graph: bool = False,
) -> dict[str, object]:
    settings = settings or get_settings()
    if pdf_path:
        settings = replace(settings, pdf_path=str(Path(pdf_path).expanduser().resolve()))

    pages = parse_pdf(settings.pdf_path, settings.source_name)
    chunks = chunk_pages(pages, chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
    save_chunks(chunks, settings.chunks_path)

    embedder = SentenceTransformerEmbedder(
        model_name=settings.embedding_model,
        normalize_embeddings=settings.embedding_normalize,
    )
    vector_store = ChromaVectorStore(settings=settings, embedder=embedder)
    vector_store.reset_collection()
    vector_store.upsert_chunks(chunks)

    bm25 = BM25Retriever()
    bm25.build(chunks)
    bm25.save(settings.bm25_index_path)

    graph_status = "created"
    try:
        graph_builder = Neo4jGraphBuilder(settings)
        graph_builder.build(chunks, reset=reset_graph)
        graph_builder.close()
    except GraphConfigError as exc:
        graph_status = f"not configured: {exc}"
        if settings.neo4j_required:
            raise
        LOGGER.warning("Neo4j graph build skipped: %s", exc)

    return {
        "pages": len(pages),
        "chunks": len(chunks),
        "chroma_collection": settings.chroma_collection,
        "bm25_index": settings.bm25_index_path,
        "graph": graph_status,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest the NCERT Physics PDF into Hybrid RAG stores.")
    parser.add_argument("--pdf", default=None, help="Path to the NCERT Physics PDF.")
    parser.add_argument("--reset-graph", action="store_true", help="Clear existing graph nodes for this source first.")
    args = parser.parse_args()
    result = run_ingestion(pdf_path=args.pdf, reset_graph=args.reset_graph)
    print(result)


if __name__ == "__main__":
    main()
