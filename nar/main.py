
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

from database_service import DatabaseService
from llm_service import LLMService, LLMServiceError

app = FastAPI(
    title="Edge-First Enterprise Knowledge API",
    description="A local RAG system: upload .txt docs, ask questions, get "
                "answers grounded in those docs via a local phi3 model.",
    version="1.0.0",
)

db = DatabaseService()
llm = LLMService()


class QueryRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "chunks_indexed": db.collection.count(),
        "ollama_available": llm.is_available(),
    }


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are accepted.")

    raw_bytes = await file.read()
    text = raw_bytes.decode("utf-8", errors="ignore").strip()
    if not text:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    chunks_stored = db.add_document(text, source=file.filename)

    return {
        "message": "File uploaded and indexed successfully.",
        "filename": file.filename,
        "chunks_stored": chunks_stored,
    }


@app.post("/query")
def query(request: QueryRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    context_chunks = db.query(question, n_results=3)

    try:
        answer = llm.generate_answer(context_chunks, question)
    except LLMServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {
        "question": question,
        "answer": answer,
        "sources": [
            {"source": c["source"], "distance": c["distance"]}
            for c in context_chunks
        ],
    }
