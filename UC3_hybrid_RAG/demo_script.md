Demo Script

Introduction

I will walk through a local Hybrid RAG project built for the AI Solution Architect assessment. The source document is the NCERT Physics PDF in data/physics.pdf. The application answers questions only from that PDF and shows the retrieved evidence used for the answer.

Architecture Overview

At a high level, the system has a FastAPI backend and a Streamlit frontend. During ingestion, the PDF is parsed into page aware chunks. Those chunks are stored in ChromaDB for semantic search and in a BM25 index for keyword search. The same chunks are also used to build a Neo4j concept graph.

When a user asks a question, the backend collects evidence from all three retrieval paths. The merged context is sent to Qwen3 through Ollama. The final answer is shown with citations.

Ingestion Pipeline

I would start by showing the PDF path in the sidebar and then running ingestion if the indexes are not already built. Ingestion parses the PDF, detects headings where possible, extracts tables, creates overlapping chunks, and stores page metadata.

After that, it builds the ChromaDB collection, saves the BM25 index, and writes concept nodes and relationships to Neo4j. The important point is that all three retrieval paths are built from the same source document.

Ask Question Example

Next, I would ask: "What is Coulombs Law?"

The answer should describe the force between two point charges and mention the dependence on charge values and distance. I would keep the focus on whether the answer is grounded, not on making the response long.

Show Retrieval Evidence

After the answer appears, I would open the retrieval evidence tabs. The semantic tab should show chunks from the relevant part of the Physics PDF. The keyword tab should also find the law because the phrase appears directly in the source. If graph nodes are available, I would show the related concept entries from Neo4j.

This part of the demo shows why the project uses hybrid retrieval instead of relying on one search method.

Show Citations

Then I would point out the citations under the answer. The citations should include source and page metadata from the retrieved chunks. This makes it easier for a reviewer to check whether the generated answer is tied back to the PDF.

Unsupported Query Example

For the unsupported case, I would ask a question that is outside the source document, such as a question about a recent sports result or a company policy. The system should return:

```text
Information not found in the source document.
```

This confirms that the app is not trying to answer from general model knowledge when evidence is missing.

Conclusion

I would close by summarizing the project in one sentence: the application ingests one Physics PDF, retrieves evidence through semantic, keyword, and graph paths, and generates grounded answers with citations. The main review areas are the retrieval evidence, citations, and unsupported query behavior.
