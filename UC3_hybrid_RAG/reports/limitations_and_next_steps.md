UC3 Limitations And Next Steps

Chunking Limitations

Chunk quality controls retrieval quality. If a concept or formula is split across chunks, the final answer may miss important context. Current chunking is tuned for the assessment PDF and should be retested for other textbooks.

Graph Limitations

The Neo4j graph is built with heuristic extraction. It captures useful concepts, headings, definitions, formulas, and neighboring relationships, but it is not a full expert curated physics knowledge graph.

Formula Extraction Limitations

Formula extraction depends on the PDF text stream. Multi line formulas, symbols, and special notation may be incomplete if the PDF parser changes layout order or drops characters.

Hallucination Risks

The model can still produce weak answers if irrelevant context is retrieved. The project reduces this risk by exposing citations, final context, and unsupported answer behavior, but retrieval quality remains the primary control.

Latency Concerns

Hybrid retrieval adds work across vector, keyword, and graph stores. This is acceptable for a local assessment demo, but production use would need latency budgets, caching, and possibly a reranker.

Cost Considerations

The local demo uses Ollama, which avoids API costs. A hosted model would introduce token and infrastructure cost. Embedding generation, graph maintenance, and PDF re ingestion would also need cost controls.

Future Enhancements

Add a reranking layer after hybrid retrieval.
Add OCR fallback for scanned PDFs.
Build a small benchmark set with expected citations.
Improve formula parsing and graph relation extraction.
Add automated ingestion validation checks.
Add authentication, logging, and monitoring for production use.
