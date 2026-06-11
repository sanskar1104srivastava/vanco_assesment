Current Limitations

Single Document Scope

The project is built around one configured Physics PDF.
It does not compare answers across multiple books, editions, or external references.
This keeps the assessment scope clear, but it also means the system cannot answer outside that document.

PDF Extraction Quality Dependency

The ingestion pipeline depends on text extracted from the PDF.
If headings, formulas, tables, or symbols are extracted poorly, the downstream chunks inherit those issues.
This is common with textbook PDFs that contain dense notation.

Graph Extraction Uses Heuristics

The Neo4j graph is built from detected headings, definitions, formulas, and simple relationship patterns.
It does not perform deep scientific relation extraction.
Some useful concept links may be missed, and some weak links may be included.

Formula Extraction Depends On Text Extraction

Formulas are captured from the extracted text stream.
If the PDF parser separates symbols or changes layout order, a formula may be incomplete.
The system still stores surrounding text, but the formula node may not be perfect.

Retrieval Quality Depends On Chunk Quality

The retrievers can only work with the chunks created during ingestion.
If a chunk is too broad, too narrow, or split across a formula boundary, the final context can be less direct.
The current chunking is tuned for the assessment PDF, not for every textbook layout.

No Reranking Layer

The hybrid retriever merges semantic, keyword, and graph evidence without a separate reranker.
This keeps the pipeline easier to inspect.
It also means the final ordering may not always place the best passage first.

Built For Assessment Scope

The project focuses on showing a complete local Hybrid RAG workflow.
It is not packaged as a production service.
Operational concerns such as monitoring, access control, and long running maintenance are outside this submission.

Improvement Ideas

Add a reranking step after hybrid retrieval.
Add OCR fallback for scanned or image heavy PDFs.
Improve formula parsing for multi line equations.
Add a small query evaluation set with saved outputs.
Make graph extraction more precise with relation templates.
