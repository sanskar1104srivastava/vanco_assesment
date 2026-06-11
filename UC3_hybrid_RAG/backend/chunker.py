"""Chapter and section-aware chunking."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .logging_utils import get_logger
from .schemas import DocumentChunk, ParsedPage


LOGGER = get_logger(__name__)
WORD_RE = re.compile(r"\S+")


@dataclass
class _Unit:
    page: int
    text: str


def _word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


def _normalise_text(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text.strip())


def _split_large_unit(unit: _Unit, chunk_size: int, chunk_overlap: int) -> list[_Unit]:
    words = WORD_RE.findall(unit.text)
    if len(words) <= chunk_size:
        return [unit]

    step = max(1, chunk_size - chunk_overlap)
    pieces: list[_Unit] = []
    for start in range(0, len(words), step):
        window = words[start : start + chunk_size]
        if not window:
            break
        pieces.append(_Unit(page=unit.page, text=" ".join(window)))
        if start + chunk_size >= len(words):
            break
    return pieces


def _page_to_units(page: ParsedPage, chunk_size: int, chunk_overlap: int) -> list[_Unit]:
    text_parts = [page.text]
    if page.tables:
        text_parts.append("\n\n".join(page.tables))
    text = _normalise_text("\n\n".join(part for part in text_parts if part.strip()))
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]

    units: list[_Unit] = []
    for paragraph in paragraphs:
        units.extend(_split_large_unit(_Unit(page=page.page, text=paragraph), chunk_size, chunk_overlap))
    return units


def _chunk_id(source: str, chapter: str, section: str, pages: list[int], index: int, text: str) -> str:
    raw = f"{source}|{chapter}|{section}|{','.join(map(str, pages))}|{index}|{text}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _build_metadata(
    page_group: list[ParsedPage],
    pages: list[int],
    index: int,
    chunk_size: int,
    chunk_overlap: int,
) -> dict[str, object]:
    first = page_group[0]
    return {
        "page": min(pages),
        "pages": ",".join(str(page) for page in sorted(set(pages))),
        "chapter": first.chapter or "Unknown Chapter",
        "section": first.section or "Unknown Section",
        "source": first.source,
        "chunk_index": index,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
    }


def _pack_section(page_group: list[ParsedPage], chunk_size: int, chunk_overlap: int) -> list[DocumentChunk]:
    if not page_group:
        return []

    first = page_group[0]
    units: list[_Unit] = []
    for page in page_group:
        units.extend(_page_to_units(page, chunk_size, chunk_overlap))

    chunks: list[DocumentChunk] = []
    buffer: list[_Unit] = []
    buffer_words = 0

    def flush() -> None:
        nonlocal buffer, buffer_words
        if not buffer:
            return
        pages = [unit.page for unit in buffer]
        body = "\n\n".join(f"[Page {unit.page}]\n{unit.text}" for unit in buffer)
        index = len(chunks)
        metadata = _build_metadata(page_group, pages, index, chunk_size, chunk_overlap)
        chunks.append(
            DocumentChunk(
                id=_chunk_id(first.source, first.chapter, first.section, pages, index, body),
                text=body,
                metadata=metadata,
            )
        )

        if chunk_overlap <= 0:
            buffer = []
            buffer_words = 0
            return

        overlap_units: list[_Unit] = []
        overlap_words = 0
        for unit in reversed(buffer):
            unit_words = _word_count(unit.text)
            if overlap_words + unit_words > chunk_overlap and overlap_units:
                break
            overlap_units.insert(0, unit)
            overlap_words += unit_words
            if overlap_words >= chunk_overlap:
                break
        buffer = overlap_units
        buffer_words = overlap_words

    for unit in units:
        unit_words = _word_count(unit.text)
        if buffer and buffer_words + unit_words > chunk_size:
            flush()
        buffer.append(unit)
        buffer_words += unit_words

    flush()
    return chunks


def _section_key(page: ParsedPage) -> tuple[str, str]:
    return (page.chapter or "Unknown Chapter", page.section or "Unknown Section")


def chunk_pages(
    pages: Iterable[ParsedPage],
    chunk_size: int = 350,
    chunk_overlap: int = 100,
) -> list[DocumentChunk]:
    """Create chunks while respecting chapter, section, then page boundaries."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be non-negative")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: list[DocumentChunk] = []
    current_group: list[ParsedPage] = []
    current_key: tuple[str, str] | None = None

    for page in pages:
        key = _section_key(page)
        if current_group and key != current_key:
            chunks.extend(_pack_section(current_group, chunk_size, chunk_overlap))
            current_group = []
        current_group.append(page)
        current_key = key

    if current_group:
        chunks.extend(_pack_section(current_group, chunk_size, chunk_overlap))

    LOGGER.info("Created %s section-aware chunks", len(chunks))
    return chunks


def save_chunks(chunks: list[DocumentChunk], path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump([chunk.to_dict() for chunk in chunks], file, indent=2, ensure_ascii=False)
    LOGGER.info("Saved %s chunks to %s", len(chunks), path)


def load_chunks(path: str) -> list[DocumentChunk]:
    with open(path, "r", encoding="utf-8") as file:
        payload = json.load(file)
    return [DocumentChunk.from_dict(item) for item in payload]
