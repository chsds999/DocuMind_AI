import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .settings import settings
from .schemas import IngestResponse, AskRequest, AskResponse, Citation
from .rag import ingest_pdf, retrieve, generate_answer


app = FastAPI(title="Document Q&A")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "./storage/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    # size check (best effort)
    max_bytes = settings.max_upload_mb * 1024 * 1024

    temp_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(temp_path, "wb") as f:
        size = 0
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                f.close()
                os.remove(temp_path)
                raise HTTPException(status_code=413, detail="File too large.")
            f.write(chunk)

    doc_id, pages, chunks = ingest_pdf(temp_path)

    # Optional: remove uploaded file after ingest
    try:
        os.remove(temp_path)
    except Exception:
        pass

    return IngestResponse(doc_id=doc_id, pages=pages, chunks=chunks)


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    contexts = retrieve(payload.doc_id, payload.question, k=payload.k)
    answer, citations = generate_answer(payload.question, contexts)
    return AskResponse(
        answer=answer,
        citations=[Citation(**c) for c in citations],
        used_chunks=len(contexts),
    )
