# Pharma Compliance

Nomora now has:
- a React/Vite frontend
- a FastAPI backend
- a local RAG + compliance + risk + recommendations pipeline

## Local Run

### 1. Backend
From `C:\Users\Parth Mudgal\OneDrive\Documents\SRM\pharma-compliance`:

```powershell
pip install -r requirements.txt
uvicorn src.api_app:app --host 127.0.0.1 --port 8000 --app-dir .
```

Available backend endpoints:
- `GET /health`
- `POST /api/analyze`
- `POST /api/chat`

### 2. Frontend
From `C:\Users\Parth Mudgal\OneDrive\Documents\SRM\pharma-compliance`:

```powershell
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`.

## RAG Pipeline Scripts

- `src/extract_text.py`
- `src/extract_requirements.py`
- `src/chunk_documents.py`
- `src/build_index.py`
- `src/retrieve_chunks.py`
- `src/rag_answer.py`
- `src/match_requirements.py`
- `src/score_risk.py`
- `src/generate_recommendations.py`

## Current Dynamic Flow

1. Frontend collects company data and selected guidelines.
2. Frontend sends data to `POST /api/analyze`.
3. Backend runs:
   - compliance assessment
   - risk scoring
   - recommendations
4. Frontend renders the live dashboard.
5. Copilot questions go to `POST /api/chat`.

## Deployment Note

For deployment, host:
- frontend as a static Vite site
- backend as a Python web service

### Render deployment

This repo now includes:
- `render.yaml`

Backend service:
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn src.api_app:app --host 0.0.0.0 --port $PORT --app-dir .`
- Health Check Path: `/health`

Frontend service:
- Build Command: `npm install && npm run build`
- Publish Directory: `dist`

Important:
- Set frontend environment variable `VITE_API_BASE_URL` to your deployed backend URL
- Example:
  - `https://nomora-backend.onrender.com`

Later, you can add:
- persistent database storage
- persistent vector store
- saved company sessions
