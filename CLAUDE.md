# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Ghibli Video Studio** — a multi-agent AI system that transforms simple themes into complete Studio Ghibli-style video plans (concept, script, visuals, YouTube metadata). The frontend is a React app with a Ghibli-themed UI; the backend is a Python FastAPI + LangGraph pipeline.

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.11, FastAPI, LangGraph, LangChain (Google Gemini `gemini-2.0-flash`), Pydantic |
| Frontend | React 19, Vite, inline styles (no CSS framework) |
| AI | Google Vertex AI (Imagen 3 for images, Cloud TTS for audio, Gemini for agents) |
| Video | MoviePy for assembly |
| Storage | Google Cloud Storage |
| Deploy | Dockerfile → Cloud Run (backend); Firebase Hosting (frontend) |

## Architecture

### Backend: LangGraph Pipeline (`backend/`)

A **sequential LangGraph workflow** with 5 agent nodes, each updating shared `GraphState`:

```
concept → script → visuals → metadata → production → END
```

- **`backend/state.py`** — `GraphState` TypedDict: `topic`, `concept`, `script`, `visuals`, `metadata`, `image_urls`, `audio_urls`, `video_url`, `logs`, `status`, `messages`.
- **`backend/orchestrator.py`** — Creates and compiles the `StateGraph`. Entry point for the pipeline.
- **`backend/main.py`** — FastAPI app. `POST /generate` accepts `{topic}`, invokes the graph via `.astream()`, returns SSE event stream.
- **`backend/agents/base.py`** — `BaseAgent` class wraps `ChatGoogleGenerativeAI` with persona prompt and optional tool binding.
- **`backend/agents/`** — Five agents: `ConceptAgent`, `ScriptAgent`, `VisualAgent`, `MetadataAgent`, `ProductionAgent`. Each implements `execute(state) -> state`.
- **`backend/tools/`** — `ghibli_tools.py` (Ghibli style guide, YouTube SEO check), `production_tools.py` (Imagen 3 generation, Google TTS, MoviePy stitching, GCS upload).

### Frontend: React Dashboard (`src/`)

- **`src/GhibliAutomation.jsx`** — Single-component app with 3 phases: input → pipeline (SSE streaming) → results. Calls the Cloud Run endpoint at `https://ghibli-backend-bskf4s232a-uc.a.run.app/generate`.
- **`src/main.jsx`** — React entry point. No router — single page.

### Deploy

- Backend: `Dockerfile` → `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` → Cloud Run
- Frontend: `vite build` → Firebase Hosting (`firebase.json` rewrites to `index.html`)

## Commands

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Set GOOGLE_API_KEY (and optionally create .env)
python -m backend.main          # or: PYTHONPATH=. uvicorn backend.main:app --reload --port 8000
```

### Frontend
```bash
npm install
npm run dev                     # Vite dev server
npm run build                   # Production build → dist/
npm run preview                 # Preview production build
```

### Deploy
```bash
# Frontend → Firebase
firebase deploy --only hosting

# Backend → Cloud Run (via Dockerfile)
docker build -t ghibli-backend .
```

## Key Design Notes

- Backend runs on Cloud Run with `$PORT` env var (Dockerfile CMD).
- Frontend hardcodes the Cloud Run backend URL in `src/GhibliAutomation.jsx` line 152. Update this if the endpoint changes.
- Production agent hardcodes GCP project ID `ghibli-studio-1775332583` and bucket `ghibli-assets-1775332583` in `backend/tools/production_tools.py` and `backend/agents/production_agent.py`.
- Environment variables needed: `GOOGLE_API_KEY` (for Gemini/Vertex AI). `python-dotenv` is used.
- Google Cloud Text-to-Speech package may have installation issues — it was renamed from `google-cloud-texttospeech` in some distros. If pip fails, try `google-cloud-texttospeech` as the distro name.
