Setup Instructions

Python Version

Use Python 3.11 for the assessment run. A recent Python 3.x version should also work, but 3.11 is the recommended baseline for this setup.

Check the installed version:

```powershell
python --version
```

Run all commands from the project root. The expected root contains backend/, frontend/, data/, and requirements.txt.

Create Venv

Create a virtual environment from the project root:

```powershell
python -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\activate
```

On Linux or macOS, activate it with:

```bash
source venv/bin/activate
```

Keep the virtual environment inside the project folder. The existing scripts and commands assume dependencies are installed into the active environment.

Install Requirements

Install the Python dependencies:

```powershell
pip install -r requirements.txt
```

This installs FastAPI, Streamlit, ChromaDB, sentence transformers, BM25 support, Neo4j support, PDF parsers, and LLM client packages.

After installation, keep the environment activated for ingestion, backend startup, and Streamlit startup.

Configure .env

Create a .env file in the project root. Keep the source PDF at data/physics.pdf.

Use these values as the base configuration:

```env
PDF_PATH=data/physics.pdf
SOURCE_NAME=NCERT_Physics_Part1.pdf
CHUNKS_PATH=data/chunks.json
CHROMA_PATH=chroma_db
CHROMA_COLLECTION=ncert_physics
BM25_INDEX_PATH=data/bm25_index.pkl
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3
```

The project also supports other LLM providers through environment variables, but the assessment configuration uses Ollama and Qwen3.

Configure Neo4j

Start a local Neo4j database or use Neo4j Aura. Add the connection details to .env:

```env
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
NEO4J_REQUIRED=true
```

Neo4j is used by the graph retrieval path, so it should be available before ingestion.

For a local database, the Neo4j browser is usually available at http://localhost:7474. Confirm the password in .env matches the running database.

Configure Ollama

Install Ollama and make sure it is running locally.

Pull Qwen3:

```powershell
ollama pull qwen3
```

The backend calls Ollama at http://localhost:11434 when LLM_PROVIDER=ollama.

Keep Ollama running while asking questions. The model name in .env must match the model pulled by Ollama.

Run Ingestion

Run ingestion after the PDF, Neo4j, and Ollama settings are ready:

```powershell
python -m backend.ingest --pdf data/physics.pdf --reset-graph
```

This creates chunks, the ChromaDB collection, the BM25 index, and the Neo4j graph.

The generated files are stored under data/, chroma_db/, and Neo4j. Run this again only when the source PDF or ingestion settings change.

Run Backend

Start the FastAPI backend:

```powershell
uvicorn backend.api:app --reload
```

The API runs at http://localhost:8000.

You can check the backend with:

```powershell
curl http://localhost:8000/health
```

Run Streamlit

Open a second terminal, activate the virtual environment, and start the frontend:

```powershell
streamlit run frontend/app.py
```

Use the Streamlit page to ask questions, review retrieved chunks, and confirm citations.

The default API URL in the app is http://localhost:8000. Keep the backend terminal open while using the frontend.
