# MACE — Multi-Agent Coordination Engine

MACE is a prototype multi-agent orchestration system that coordinates specialized AI agents — a Support/Helpdesk Agent and a pluggable Domain Agent — through a central Orchestrator. The Orchestrator decomposes user intent into subtasks, routes them to the right agent, detects conflicts (duplicate intents, resource clashes, sequential dependencies), resolves them via rule-based or LLM-powered arbitration, and maintains a shared memory layer so agents work as a coordinated unit rather than isolated silos.

## Team

| Name | GitHub | Responsibilities |
|------|--------|-----------------|
| Akash Manilal Agarwal | [@AkashAgarwalSER515](https://github.com/AkashAgarwalSER515) | Orchestrator, LangGraph integration |
| Arpit Anil Jaiswal | [@ajaisw43](https://github.com/ajaisw43) | Support Agent, Auth |
| Girish Subhash Nalawade | [@Girish-123-dev](https://github.com/Girish-123-dev) | Domain Agent, FAISS |
| Anmol Sudhir Monde | [@AnmolMonde](https://github.com/AnmolMonde) | Frontend (React), Evaluation |

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     React Frontend (Vite)                    │
│    Login / Register ──── Dashboard ──── Task History         │
└──────────────────────────┬───────────────────────────────────┘
                           │  REST API (JSON)
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                            │
│                                                              │
│  ┌──────────┐  ┌──────────────────────────────────────────┐  │
│  │  Auth    │  │            Orchestrator                  │  │
│  │  (JWT)   │  │                                          │  │
│  └──────────┘  │  ┌────────────┐ ┌──────────┐ ┌────────┐ │  │
│                │  │ Intent     │→│  Task    │→│Conflict│ │  │
│                │  │ Parser     │ │  Router  │ │Detector│ │  │
│                │  └────────────┘ └──────────┘ └───┬────┘ │  │
│                │                              ┌───▼────┐ │  │
│                │                              │Arbitra-│ │  │
│                │                              │tion    │ │  │
│                │                              └────────┘ │  │
│                └──────────┬──────────────┬───────────────┘  │
│                           │              │                   │
│                     ┌─────▼──────┐ ┌─────▼────────────┐     │
│                     │  Support   │ │  Custom Domain   │     │
│                     │  Agent     │ │  Agent           │     │
│                     │  • Tickets │ │  • Pluggable     │     │
│                     │  • FAQs    │ │  • Domain tasks  │     │
│                     └─────┬──────┘ └─────┬────────────┘     │
│                           └──────┬───────┘                   │
│                                  ▼                           │
│                     ┌────────────────────────┐               │
│                     │    Shared Memory       │               │
│                     │  • SQLite (tasks, auth)│               │
│                     │  • FAISS (embeddings)  │               │
│                     │  • Conflict Log        │               │
│                     └────────────────────────┘               │
└──────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, React Router, Axios |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| AI / ML | Anthropic Claude, LangGraph, FAISS, Sentence-Transformers |
| Database | SQLite (relational) + FAISS (vector) |
| Auth | JWT (PyJWT + bcrypt) |
| Deployment | Docker & Docker Compose |
| CI | GitHub Actions |

## Project Structure

```
├── frontend/               # React app (Vite)
│   ├── src/
│   │   ├── pages/          # Login, Register, Dashboard
│   │   ├── services/       # Axios API client
│   │   └── components/     # Reusable UI components
│   ├── package.json
│   └── Dockerfile
├── backend/                # FastAPI server + AI logic
│   ├── app/
│   │   ├── routers/        # auth, orchestrator, health
│   │   ├── services/       # database, LLM wrappers
│   │   ├── agents/         # Support Agent, Domain Agent
│   │   ├── orchestrator/   # Intent parser, router, conflict detector
│   │   ├── memory/         # Shared memory layer
│   │   └── models/         # Pydantic schemas
│   ├── requirements.txt
│   └── Dockerfile
├── tests/                  # pytest (backend) + vitest (frontend)
├── eval/                   # Evaluation scripts + metrics
├── docs/                   # Proposal, architecture diagrams
├── .github/workflows/      # CI pipeline
├── docker-compose.yml
├── .env.example
└── README.md
```

## Setup Instructions

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 20+ |
| npm | 10+ |
| Git | latest |
| Docker & Docker Compose | latest (optional) |

### 1. Clone the repository

```bash
git clone https://github.com/Girish-123-dev/SER594-Team25-MACE-Multi_Agent_Coordination_Engine.git
cd SER594-Team25-MACE-Multi_Agent_Coordination_Engine
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

### 3. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # macOS / Linux
pip install -r requirements.txt
uvicorn app.main:app --reload   # Runs on http://localhost:8000
```

### 4. Frontend setup (separate terminal)

```bash
cd frontend
npm install
npm run dev                     # Runs on http://localhost:5173
```

### 5. Alternative — Run with Docker

```bash
docker compose up --build
# Frontend: http://localhost:3000   Backend API: http://localhost:8000
```

## Environment Variables

See [.env.example](.env.example):

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude |
| `MODEL_NAME` | Model identifier (default: `claude-sonnet-4-20250514`) |
| `DB_PATH` | SQLite database path |
| `FAISS_INDEX_PATH` | FAISS index directory |
| `SIMILARITY_THRESHOLD` | Deduplication threshold (0–1) |
| `MAX_ORCHESTRATION_CYCLES` | Max orchestrator iterations |
| `JWT_SECRET` | Secret for JWT signing |
| `LOG_LEVEL` | Logging level |

> **Note:** Never commit your `.env` file. The `.gitignore` already excludes it.

## Running Tests

```bash
# Backend tests
cd backend && pytest ../tests/backend/ -v

# Frontend tests
cd frontend && npm test
```

## Running the Evaluation Suite

```bash
# (scripts will be added in eval/ during M3/M4)
python eval/run_eval.py
```

## Deployment

- **Docker:** `docker compose up --build` — Frontend at `:3000`, API at `:8000`
- **Production URL:** TBD (will be added when deployed)

## License

TBD
