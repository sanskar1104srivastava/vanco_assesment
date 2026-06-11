from backend.bm25_search import BM25Retriever
from backend.schemas import DocumentChunk


def test_bm25_returns_top_k_even_with_zero_scores():
    chunks = [
        DocumentChunk("a", "alpha beta", {"page": 1}),
        DocumentChunk("b", "gamma delta", {"page": 2}),
    ]
    retriever = BM25Retriever()
    retriever.build(chunks)

    results = retriever.query("unmatched", top_k=2)

    assert len(results) == 2
    assert all(result.score == 0.0 for result in results)
