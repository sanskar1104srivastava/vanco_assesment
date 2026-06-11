Project Overview

This project is a Hybrid RAG application built for an AI Solution Architect assessment. It answers questions from the configured NCERT Physics PDF stored at data/physics.pdf. The scope is intentionally narrow: the system should answer only when the source document contains enough evidence. Hybrid RAG is used because physics content mixes definitions, formulas, examples, and concept relationships. A semantic search can find similar meaning, keyword search can catch exact terms such as laws and symbols, and graph retrieval can add related concepts when a question depends on connections between topics.

The review focus is grounding. Each answer is expected to come from retrieved PDF evidence and include page level citations.

Architecture

The backend indexes the Physics PDF into three retrieval paths. ChromaDB stores dense embeddings for semantic search. BM25 stores a keyword index for exact phrase and term matching. Neo4j stores a lightweight concept graph extracted from headings, formulas, definitions, and relationships found during ingestion. Hybrid Retrieval merges these signals, removes duplicate chunks, and builds the final evidence context. The answer step uses Qwen3 through Ollama and receives only the retrieved context. The frontend is a Streamlit app, and the API layer is FastAPI.

See architecture/architecture.png for the submission diagram.

The stores are kept separate so their evidence can be inspected in the UI. This is useful during assessment review because the reviewer can see semantic chunks, keyword chunks, and graph nodes instead of only seeing the final answer.

Retrieval Flow

The flow starts with a user question in the Streamlit UI or through the FastAPI /ask endpoint.

First, the question is normalized for retrieval. ChromaDB runs semantic retrieval and returns chunks that are close in embedding space. BM25 runs keyword retrieval and returns chunks that match important terms from the question. Neo4j runs graph retrieval and returns related concepts, formulas, definitions, or neighboring topics when available.

The hybrid retriever combines the results and keeps the final chunk list grounded in the PDF metadata. The context builder formats these chunks with page, chapter, section, and source details. Qwen3 generates the answer from that context. Citations are collected from the retrieved metadata and shown with the answer. If no useful evidence is found, the system returns the fixed unsupported answer message instead of guessing.

This flow keeps the answer step separate from retrieval. The model does not search the PDF on its own. It receives a prepared context, the original question, and grounding instructions. This makes it easier to review failures: if the answer is weak, the retrieval evidence and the final context can be checked directly in the debug panel.

Project Structure

backend/ contains the FastAPI app, ingestion pipeline, retrievers, graph builder, prompt builder, and answer generation code.

frontend/ contains the Streamlit interface used for asking questions, running ingestion, and reviewing retrieval evidence.

data/ stores the source PDF, parsed chunks, and the BM25 index.

chroma_db/ stores the persisted ChromaDB collection.

architecture/ contains the architecture diagram for the assessment submission.

screenshots/ contains guidance for the required reviewer screenshots.

scripts/ contains helper scripts for starting the backend and frontend on Windows.

tests/ contains focused tests for chunking, prompts, BM25, ingestion headings, and query normalization.

logs/ is used for runtime and evaluation output. It is not required for reading the code, but it is useful when checking ingestion or backend behavior during a demo.

requirements.txt lists the Python packages needed for the local run. setup.py is present for package style project metadata.

Setup

Use Python 3.11 or a compatible Python 3.x version.

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Place the source file at:

```text
data/physics.pdf
```

Create a .env file with the PDF path, Neo4j settings, ChromaDB settings, and Ollama model. For the assessment run, use Qwen3 with Ollama:

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3
```

Neo4j should be running before ingestion if NEO4J_REQUIRED=true. Ollama should also be running before asking questions. The source PDF must exist before ingestion starts.

Running The Project

Backend:

```powershell
uvicorn backend.api:app --reload
```

Frontend:

```powershell
streamlit run frontend/app.py
```

Ingestion:

```powershell
python -m backend.ingest --pdf data/physics.pdf --reset-graph
```

The backend must be running before the Streamlit app can answer questions. Ingestion should be run after the PDF and Neo4j settings are ready.

The Streamlit sidebar can also trigger ingestion through the backend API. For a clean demo, start Neo4j and Ollama first, run ingestion once, start the backend, and then open the frontend. The API health endpoint is available at http://localhost:8000/health.

Example Questions

What is Coulombs Law?
Define Electric Field.
What is Electric Potential?
Explain Amperes Circuital Law.

Grounding Behaviour

The application is designed to answer only from retrieved source evidence. Unsupported questions return:

```text
Information not found in the source document.
```

This behavior is intentional. It is better for the assessment demo to refuse an unsupported question than to produce an answer that cannot be traced to the PDF. The citations and evidence tabs are the main way to check grounding.
