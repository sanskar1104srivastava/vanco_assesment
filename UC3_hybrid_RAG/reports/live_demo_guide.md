UC3 Hybrid RAG Live Demo Guide

Install Dependencies

Open PowerShell in the UC3_hybrid_RAG folder:

```powershell
cd D:\vanco_assesment\UC3_hybrid_RAG
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Start Databases And Model Runtime

Start Neo4j and confirm the configured database credentials match the .env file. Start Ollama and make sure the configured model is available.

For the assessment setup, the expected model is:

```text
qwen3
```

Run Ingestion

Confirm the source PDF exists:

```text
data/physics.pdf
```

Run ingestion:

```powershell
python -m backend.ingest --pdf data/physics.pdf --reset-graph
```

This builds the vector index, keyword index, and graph records.

Launch Backend

```powershell
uvicorn backend.api:app --reload
```

Check:

```text
http://localhost:8000/health
```

Launch Frontend

In a second PowerShell window:

```powershell
cd D:\vanco_assesment\UC3_hybrid_RAG
.\venv\Scripts\activate
streamlit run frontend/app.py
```

Ask Questions

Try reviewer friendly questions:

What is Coulombs Law?
Define Electric Field.
What is Electric Potential?
Explain Amperes Circuital Law.

View Citations

After an answer is generated, review:

Citation list.
Retrieved chunks.
Semantic, keyword, and graph evidence.
Final context sent to the model.

Unsupported questions should return:

```text
Information not found in the source document.
```

Troubleshooting

Issue: What To Check
Backend fails: Confirm dependencies installed and .env values are set.
No answers: Confirm ingestion completed and ChromaDB/BM25 files exist.
Graph retrieval empty: Confirm Neo4j is running before ingestion.
LLM unavailable: Confirm Ollama is running and qwen3 is installed.
Missing citations: Re run ingestion and inspect retrieved chunk metadata.
