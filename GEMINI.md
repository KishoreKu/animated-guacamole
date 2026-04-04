# 📂 Project Context: Ghibli Video Studio (Pro)

This project is a high-fidelity Studio Ghibli video automation suite. It uses a modular multi-agent system powered by **Python FastAPI**, **LangGraph**, and **Model Context Protocol (MCP)** to transform simple themes into complete video plans.

## 🚀 Project Overview

The system is split into a robust Python backend and a React-based monitoring dashboard.

### 🤖 AI Agents & Orchestration
- **LangGraph Orchestrator:** Manages the stateful flow between specialized agents (Concept → Script → Visuals → Metadata).
- **Tool Calling:** Agents use specialized Python tools (e.g., `youtube_seo_check`, `get_ghibli_style_guide`) to validate and refine their outputs.
- **Specialized Agents:**
  - **Concept Agent:** Weaves magical story concepts and world-building.
  - **Script Agent:** Writes poetic narration and scene layouts.
  - **Visual Agent:** Generates image prompts using the Ghibli Style Guide tool.
  - **Metadata Agent:** Handles YouTube SEO with integrated title validation tools.

### 🛠️ Tech Stack
- **Backend:** Python 3.11+, FastAPI, LangGraph, LangChain, Pydantic.
- **Frontend:** React, TailwindCSS, Server-Sent Events (SSE) for real-time log streaming.
- **AI Integration:** Anthropic Claude 3.5 Sonnet (via Tool Calling).

## 🏗️ Architecture

1.  **React Frontend:** Captures user theme → POST to `/generate`.
2.  **FastAPI Backend:** Initializes a `GraphState` → Triggers the `LangGraph` orchestrator.
3.  **LangGraph Pipeline:**
    - Agents execute sequentially, updating the shared context.
    - Each node's output is streamed back to the frontend via SSE.
4.  **Tool Execution:** Agents autonomously decide when to call integrated tools for validation or style guidance.

## 🛠️ Building and Running

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Create .env with ANTHROPIC_API_KEY
python main.py
```

### 2. Frontend Setup
```bash
# Ensure the React app is configured to point to http://localhost:8000
npm install && npm run dev
```

## 🔑 Development Conventions
- **Agentic Logic:** Keep agent personas and tools modular within `backend/agents/` and `backend/tools/`.
- **State Management:** Use `backend/state.py` to define any new fields required for the context chain.
- **Streaming:** Ensure all graph updates include a log entry to maintain a rich UI experience.

