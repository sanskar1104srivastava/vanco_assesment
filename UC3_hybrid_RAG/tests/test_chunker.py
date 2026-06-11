from backend.chunker import chunk_pages
from backend.schemas import ParsedPage


def test_chunk_pages_preserves_required_metadata():
    pages = [
        ParsedPage(
            page=10,
            text="Coulomb's law explains the force between two point charges.",
            chapter="Electric Charges And Fields",
            section="1.3 Coulomb's Law",
            source="NCERT_Physics_Part1.pdf",
        )
    ]

    chunks = chunk_pages(pages, chunk_size=20, chunk_overlap=5)

    assert chunks
    assert chunks[0].metadata["page"] == 10
    assert chunks[0].metadata["chapter"] == "Electric Charges And Fields"
    assert chunks[0].metadata["section"] == "1.3 Coulomb's Law"
    assert chunks[0].metadata["source"] == "NCERT_Physics_Part1.pdf"
    assert chunks[0].metadata["chunk_size"] == 20
    assert chunks[0].metadata["chunk_overlap"] == 5


def test_chunk_pages_respects_section_boundaries():
    pages = [
        ParsedPage(1, "A " * 40, "Chapter A", "Section A", "source.pdf"),
        ParsedPage(2, "B " * 40, "Chapter A", "Section B", "source.pdf"),
    ]

    chunks = chunk_pages(pages, chunk_size=30, chunk_overlap=5)

    sections = {chunk.metadata["section"] for chunk in chunks}
    assert sections == {"Section A", "Section B"}
