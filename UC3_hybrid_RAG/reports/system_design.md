UC3 Hybrid RAG System Design

High Level Architecture

The Hybrid RAG system answers questions from the configured NCERT Physics PDF. It combines semantic retrieval, keyword retrieval, and graph retrieval before sending grounded context to the language model.

Main components:

Streamlit frontend for questions, ingestion controls, and retrieval evidence.
FastAPI backend for health checks, ingestion, and answer generation.
PDF ingestion pipeline for chunking and metadata extraction.
ChromaDB vector store for semantic search.
BM25 index for keyword search.
Neo4j graph store for concepts, definitions, formulas, and relationships.
Ollama / Qwen3 answer generator for grounded responses.

Data Flow

The source PDF is placed at data/physics.pdf.
Ingestion extracts text, headings, formulas, and page metadata.
Chunks are embedded and stored in ChromaDB.
Keyword records are stored for BM25 retrieval.
Concept and formula relationships are written to Neo4j.
A user asks a question in the Streamlit frontend.
The backend normalizes the query and runs semantic, keyword, and graph retrieval.
Retrieved evidence is merged and formatted as model context.
The LLM generates an answer from the retrieved context.
Citations are returned with the answer.

Component Responsibilities

Component: Responsibility
backend/ingest.py: Build searchable stores from the PDF.
backend/chunker.py: Split extracted text into retrievable chunks.
backend/vector_store.py: Manage ChromaDB embeddings.
backend/bm25_search.py: Support exact term and phrase matching.
backend/graph_builder.py: Build concept graph records.
backend/graph_retriever.py: Retrieve related graph evidence.
backend/hybrid_retriever.py: Merge semantic, keyword, and graph results.
backend/prompt_builder.py: Build grounded prompt context.
backend/answer_generator.py: Generate answers with the configured LLM.
frontend/app.py: Reviewer facing UI and evidence display.

Design Decisions

Hybrid retrieval was used because physics questions may contain definitions, formulas, exact law names, or conceptual relationships.
Citations are preserved from chunk metadata so reviewers can trace answers back to the PDF.
Unsupported questions return a fixed refusal instead of a guessed answer.
The debug panel exposes retrieved chunks and final context to make failures inspectable.

Tradeoffs

The graph is heuristic and lightweight, not a full scientific knowledge graph.
No reranker is included, which keeps the system easier to inspect but may leave ordering imperfect.
Formula extraction depends on PDF text quality.
The project is optimized for assessment review, not for production operations.
