from backend.prompt_builder import REFUSAL, collect_citations, format_sources
from backend.schemas import HybridEvidence, RetrievalItem


def test_collect_citations_deduplicates_by_metadata():
    evidence = HybridEvidence(
        merged_chunks=[
            RetrievalItem(
                retrieval_type="hybrid",
                id="a",
                text="context",
                metadata={
                    "chapter": "Electric Charges And Fields",
                    "section": "Coulomb's Law",
                    "page": 10,
                    "pages": "10",
                    "source": "NCERT_Physics_Part1.pdf",
                },
                score=1.0,
            ),
            RetrievalItem(
                retrieval_type="hybrid",
                id="a",
                text="context",
                metadata={
                    "chapter": "Electric Charges And Fields",
                    "section": "Coulomb's Law",
                    "page": 10,
                    "pages": "10",
                    "source": "NCERT_Physics_Part1.pdf",
                },
                score=0.9,
            ),
        ]
    )

    citations = collect_citations(evidence)

    assert len(citations) == 1
    assert "Page: 10" in format_sources(citations)


def test_refusal_phrase_is_exact():
    assert REFUSAL == "Information not found in the source document."

