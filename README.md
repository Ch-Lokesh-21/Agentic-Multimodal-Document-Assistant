# Research Paper Assistance


## This project helps researchers and engineers quickly extract, search, and query content from research papers (PDFs). Core flows: upload PDFs, auto-extract text and images, generate chunked embeddings, run semantic search, and produce concise LLM-backed answers with citation snippets.

Tech stack
- Backend: Python 3.12, FastAPI, Uvicorn
- Frontend: React (v19) + Vite + TypeScript + Tailwind CSS
- Database: MongoDB (users, sessions, metadata)
- Vector store: ChromaDB 
- ML: LangChain integration
- Auth: JWT access tokens + HTTP-only refresh cookie

Installation 
Place backend environment variables in `backend/.env` and frontend variables in `frontend/.env`.1. Backend (PowerShell):
```powershell
cd backend
python -m venv .venv
. .venv\Scripts\Activate
pip install -r requirements.txt
# create backend/.env 
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
2. Frontend:
```bash
cd frontend
npm install
# create frontend/.env 
npm run dev
```

