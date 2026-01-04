# Document Q&A (PDF) — RAG Demo

Upload a PDF, index it into a local vector DB (Chroma), then ask questions grounded in the PDF text.

## Prereqs
- Python 3.10+
- Node 18+
- OpenAI API key

## Backend setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt

cp .env.example .env
# edit .env with OPENAI_API_KEY

uvicorn app.main:app --reload --port 8000
