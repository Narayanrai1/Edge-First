# Edge-First Enterprise Knowledge API

A local **RAG** (Retrieval-Augmented Generation) service built with Python and FastAPI. Upload text documents, ask questions, and get intelligent answers grounded in your uploaded documents — all running entirely on your machine with no cloud dependencies.

## Features

- **Document Upload**: Upload `.txt` files and automatically index them for searching
- **Semantic Search**: Find relevant document chunks using vector embeddings
- **RAG-Powered Q&A**: Get contextual answers using a local LLM (phi3 via Ollama)
- **REST API**: Simple HTTP endpoints for integration with other applications
- **100% Local**: No external APIs or cloud services required
- **Graceful Degradation**: Document upload and search work without Ollama; query generation fails gracefully with helpful error messages

## Tech Stack

- **Framework**: FastAPI + Uvicorn
- **Vector Database**: ChromaDB (local, persistent)
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **LLM**: Phi3 via Ollama
- **Language**: Python 3.9+

## Prerequisites

| Tool | Purpose | Verify |
|------|---------|--------|
| Python 3.9+ | Runtime environment | `python3 --version` |
| Ollama | LLM server (required for `/query` endpoint) | `ollama --version` |

**Note**: Document upload and retrieval work without Ollama. Only the `/query` endpoint requires it to generate answers.

## Installation

### 1. Set Up Python Environment

```bash
# Navigate to project directory
cd path\to\project

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
venv\Scripts\Activate.ps1

# If using Command Prompt instead:
# venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

**First-time setup note**: ChromaDB will download an ~80MB embedding model (`all-MiniLM-L6-v2`) and cache it to `%USERPROFILE%\.cache\chroma\` on first run.

### 2. Install and Start Ollama (for answer generation)

```bash
# Download and install Ollama for Windows from:
# https://ollama.ai/download/windows

# After installation, start the Ollama server (leave running in a separate terminal)
ollama serve

# In another PowerShell/Command Prompt terminal, pull the phi3 model (~2.3GB, one-time download)
ollama pull phi3

# Verify Ollama is running (should show the server listening)
# You should see: "Listening on [::]:11434"
```

> Ollama installer will add the command to your PATH. You may need to restart PowerShell after installation.

## Running the Server

```bash
# Make sure you're in the project directory
cd path\to\project

# Activate virtual environment (if not already active)
venv\Scripts\Activate.ps1

# Start the development server (with auto-reload)
uvicorn main:app --reload

# Or use for production:
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

View interactive API documentation at `http://localhost:8000/docs` (Swagger UI)

**Tip**: Open two PowerShell/Command Prompt windows:
1. One for Ollama: `ollama serve`
2. Another for the FastAPI server: activate venv and run `uvicorn main:app --reload`

## API Endpoints

### 1. Health Check
```
GET /health
```
Returns server status and statistics.

**Response:**
```json
{
  "status": "ok",
  "chunks_indexed": 42,
  "ollama_available": true
}
```

### 2. Upload Document
```
POST /upload
```
Upload a `.txt` file to index.

**Request**: Multipart form data with `file` field

**Response:**
```json
{
  "message": "File uploaded and indexed successfully.",
  "filename": "document.txt",
  "chunks_stored": 15
}
```

### 3. Query Knowledge Base
```
POST /query
```
Ask a question and get answers from indexed documents.

**Request:**
```json
{
  "question": "What is the company's return policy?"
}
```

**Response:**
```json
{
  "question": "What is the company's return policy?",
  "answer": "The company offers a 30-day return policy...",
  "sources": [
    {
      "source": "policies.txt",
      "distance": 0.15
    }
  ]
}
```

## Project Structure

```
nar/
├── main.py                    # FastAPI app definition and routes
├── database_service.py        # ChromaDB integration and document handling
├── llm_service.py             # Ollama LLM integration
├── requirements.txt           # Python dependencies
├── chroma_store/              # Persistent vector database storage
├── README.md                  # This file
└── sample.txt                 # Example document for testing
```

## How It Works

1. **Document Ingestion**: When you upload a `.txt` file, it's split into overlapping chunks (500 chars, 50-char overlap)
2. **Embedding**: Each chunk is converted to vector embeddings using a local sentence transformer model
3. **Storage**: Chunks and embeddings are stored in ChromaDB for fast similarity search
4. **Query Processing**: When you ask a question:
   - The question is converted to embeddings
   - Top 3 similar chunks are retrieved from the database
   - Chunks are sent as context to the phi3 LLM
   - LLM generates a grounded answer based on the provided context
5. **Response**: Answer returned with source document references and similarity scores

## Troubleshooting

### Ollama Connection Error
If you see "Could not reach the Ollama server", ensure:
- Ollama is installed: `brew install ollama` (or download from ollama.ai)
- Ollama server is running: `ollama serve` in a separate terminal
- The phi3 model is pulled: `ollama pull phi3`

### Empty Upload Error
- Ensure your `.txt` file is not empty and contains text
- File must be UTF-8 encoded

### Slow First Request
- First run downloads the embedding model (~80MB)
- Ollama's first LLM inference takes extra time (~30-60s)
- Subsequent requests are faster

## Development

### Run in Development Mode
```bash
uvicorn main:app --reload
```
The server will auto-restart on file changes.

# Windows PowerShell
Remove-Item -Recurse -Force chroma_store\

# Or using Command Prompt
rmdir /s /q chroma_storetation
Open `http://localhost:8000/docs` for interactive Swagger UI

### Clear the Knowledge Base
To reset the indexed documents:
```bash
rm -rf chroma_store/
```

## Performance Notes

- **Chunk Size**: 500 characters with 50-character overlap (configurable in `database_service.py`)
- **Search Results**: Returns top 3 most relevant chunks per query
- **LLM Model**: Phi3 runs locally; response time depends on your hardware
- **Embedding Model**: All-MiniLM-L6-v2 (local, ~80MB)

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

---

## Run

```bash
cd /Users/nar
./venv/bin/uvicorn main:app --reload
```

- `main:app` = the `app` object inside `main.py`.
- `--reload` = hot reload on file changes (≈ `nodemon`).
- Server runs at **http://localhost:8000**
- **Interactive docs (auto-generated): http://localhost:8000/docs** — test every
  endpoint from the browser, no curl needed.

---

## Try it

A demo document `sample.txt` (a fake remote-work policy) is included.

```bash
# 1. Health / readiness check
curl http://localhost:8000/health
# → {"status":"ok","chunks_indexed":0,"ollama_available":false}

# 2. Upload + index a .txt file
curl -X POST http://localhost:8000/upload -F "file=@sample.txt"
# → {"message":"File uploaded and indexed successfully.","filename":"sample.txt","chunks_stored":3}

# 3. Ask a question (needs Ollama running with phi3 pulled)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many days per week can I work remotely?"}'
# → {"question":"...","answer":"...up to three days per week.","sources":[...]}
```

If Ollama isn't running, step 3 returns a clean **503** explaining what to start
(retrieval still works — only generation needs the LLM).

---

## API reference

| Method | Path | Body | Returns |
|--------|------|------|---------|
| `GET`  | `/health` | — | status, indexed chunk count, Ollama reachability |
| `POST` | `/upload` | multipart form, field `file` (a `.txt`) | filename + chunks stored |
| `POST` | `/query`  | JSON `{"question": "..."}` | `{question, answer, sources}` |

---

## Project layout

```
nar/
├── requirements.txt      # dependency manifest  (≈ package.json)
├── main.py               # FastAPI app + routes (≈ app.js)
├── database_service.py   # ChromaDB: chunk → embed → store → retrieve top-3
├── llm_service.py        # Ollama/phi3: build prompt → generate → error handling
├── sample.txt            # demo document for /upload
├── venv/                 # virtual environment  (≈ node_modules, git-ignored)
└── chroma_store/         # persisted vector DB  (created on first upload)
```

How `/query` works: question → retrieve top-3 relevant chunks from ChromaDB →
build a prompt that tells phi3 to answer *only* from that context → return the
answer with its sources.

---

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `/query` → 503 "Could not reach the Ollama server" | Run `ollama serve`. |
| `/query` → 503 "model 'phi3' is not available" | Run `ollama pull phi3`. |
| First `/upload` hangs for a while | One-time embedding-model download; speed depends on your network. Cached afterward. |
| `/upload` → 400 "Only .txt files are accepted" | Endpoint only accepts `.txt`. |
| `NotOpenSSLWarning` / `Failed to send telemetry event` on startup | Harmless noise (LibreSSL warning; Chroma's anonymous telemetry). Ignore. |
