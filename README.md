# MACE — Multi-Agent Coordination Engine

**SER 594: AI for Software Engineers — Team 25**

MACE is a multi-agent orchestration system that coordinates specialized AI agents through a central Orchestrator. A user types a natural-language request into a web UI; the system parses intent using an LLM, routes subtasks to the right agent, detects conflicts (duplicate intents, resource clashes, dependency chains), and maintains a shared memory layer so agents coordinate rather than collide.

## Team

| Name | GitHub | Responsibilities |
|------|--------|-----------------|
| Akash Manilal Agarwal | [@AkashAgarwalSER515](https://github.com/AkashAgarwalSER515) | Orchestrator, LangGraph integration |
| Arpit Anil Jaiswal | [@ajaisw43](https://github.com/ajaisw43) | Support Agent, Auth |
| Girish Subhash Nalawade | [@Girish-123-dev](https://github.com/Girish-123-dev) | Domain Agent, FAISS |
| Anmol Sudhir Monde | [@AnmolMonde](https://github.com/AnmolMonde) | Frontend (React), Evaluation |

## Architecture

> Full Mermaid diagram: [docs/architecture.mmd](docs/architecture.mmd)

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
│                │  └────────────┘ └──────────┘ └────────┘ │  │
│                └──────────┬──────────────┬───────────────┘  │
│                           │              │                   │
│                     ┌─────▼──────┐ ┌─────▼────────────┐     │
│                     │  Support   │ │  Domain Agent    │     │
│                     │  Agent     │ │  (pluggable)     │     │
│                     └─────┬──────┘ └─────┬────────────┘     │
│                           └──────┬───────┘                   │
│                                  ▼                           │
│                     ┌────────────────────────┐               │
│                     │    Shared Memory       │               │
│                     │  • SQLite (tasks, auth)│               │
│                     │  • FAISS (embeddings)  │               │
│                     └────────────────────────┘               │
└──────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, React Router, Axios |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| AI / ML | Anthropic Claude API, FAISS (faiss-cpu), Sentence-Transformers |
| Database | SQLite (relational) + FAISS index (vector) |
| Auth | JWT (PyJWT + bcrypt) |
| Deployment | Docker & Docker Compose |
| CI | GitHub Actions |
| Formatting | Black (Python), Prettier (JS) |

## Project Structure

```
├── frontend/               # React app (Vite)
│   ├── src/
│   │   ├── pages/          # Login, Register, Dashboard
│   │   ├── services/       # Axios API client
│   │   └── components/     # Spinner, reusable UI
│   ├── package.json
│   └── Dockerfile
├── backend/                # FastAPI server + AI logic
│   ├── app/
│   │   ├── routers/        # auth, orchestrator, health
│   │   ├── services/       # database, LLM wrapper
│   │   ├── orchestrator/   # Intent parser, task router, conflict detector, pipeline
│   │   ├── memory/         # FAISS store, sentence-transformer embeddings
│   │   ├── agents/         # (M3: Support Agent, Domain Agent)
│   │   └── models/         # Pydantic schemas
│   ├── requirements.txt
│   └── Dockerfile
├── tests/
│   └── backend/            # 25 pytest tests (API, DB, FAISS, LLM)
├── docs/
│   ├── architecture.mmd    # Mermaid architecture diagram
│   └── PROJECT_PLAN.txt    # Full project plan
├── eval/                   # (M3/M4: evaluation scripts)
├── .github/workflows/ci.yml
├── docker-compose.yml
├── pyproject.toml          # Black config
├── .env.example
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 20+ / npm 10+
- Git
- Docker & Docker Compose (optional, for containerized run)

### 1. Clone the repository

```bash
git clone https://github.com/Girish-123-dev/SER594-Team25-MACE-Multi_Agent_Coordination_Engine.git
cd SER594-Team25-MACE-Multi_Agent_Coordination_Engine
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env and set your ANTHROPIC_API_KEY
```

### 3. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload       # http://localhost:8000
```

### 4. Frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev                         # http://localhost:5173
```

### 5. Docker (alternative)

```bash
docker compose up --build
# Frontend → http://localhost:3000    Backend API → http://localhost:8000
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude | *(required)* |
| `MODEL_NAME` | Claude model identifier | `claude-sonnet-4-20250514` |
| `DB_PATH` | SQLite database file | `data/mace.db` |
| `FAISS_INDEX_PATH` | FAISS index directory | `data/faiss_index` |
| `SIMILARITY_THRESHOLD` | Duplicate-intent cosine threshold (0–1) | `0.85` |
| `MAX_ORCHESTRATION_CYCLES` | Max orchestrator iterations | `10` |
| `JWT_SECRET` | Secret key for JWT signing | `change-me-in-production` |
| `LOG_LEVEL` | Python logging level | `INFO` |

> Never commit `.env`. It is already in `.gitignore`.

## Running Tests

```bash
# From the project root
python3 -m pytest tests/backend/ -v
```

25 tests across 4 files:

| File | Tests | Covers |
|------|-------|--------|
| `test_api.py` | 9 | Health, register, login, auth, orchestrator endpoints |
| `test_database.py` | 6 | User CRUD, task CRUD |
| `test_faiss.py` | 6 | Add/search, duplicates, persist/reload, embedding dimensions |
| `test_llm.py` | 4 | LLM response, JSON parsing, error handling, token tracking |

CI runs automatically on every push and pull request via GitHub Actions (`.github/workflows/ci.yml`).

## How to Authenticate

1. **Register** — Go to `http://localhost:5173/register` and create an account.
2. **Login** — Go to `http://localhost:5173/login` and enter your credentials. A JWT token is stored automatically.
3. **Dashboard** — After login you are redirected to `/dashboard`. All API calls include the token via `Authorization: Bearer <token>`.
4. **Two-user sessions** — Log out, register a second user, and log in. Each user sees only their own task history.

**curl examples:**

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","email":"demo@test.com","password":"pass123"}'

# Login (returns access_token)
curl -X POST http://localhost:8000/api/auth/login \
  -d "username=demo&password=pass123"

# Authenticated request
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/auth/me
```

## AI Technique #1 — LLM API Integration (Anthropic Claude)

The first AI technique is **LLM API Integration** using the Anthropic Claude API for intent parsing.

**Capabilities:**
- Parses natural-language messages into structured JSON (intent type, entities, priority, required agents)
- Structured output parsing with JSON schema enforcement
- 3× retry with exponential backoff on rate-limit and server errors
- Tracks input/output tokens and latency per request
- Swappable LLM backend (`BaseLLMService` ABC → `AnthropicService`)

**Usage:**
1. Set `ANTHROPIC_API_KEY` in `.env`
2. Start backend and frontend (see Setup above)
3. Register, log in, then type a message on the Dashboard — e.g. *"I forgot my password, please help"*
4. The pipeline will: check FAISS for duplicate intents → call Claude to parse intent → route to the correct agent → save task to SQLite → store embedding in FAISS → return the result

**Key files:**
- `backend/app/services/llm.py` — Claude API wrapper (retries, token tracking)
- `backend/app/orchestrator/intent.py` — Intent parser (Claude prompt + JSON extraction)
- `backend/app/orchestrator/pipeline.py` — Orchestration pipeline
- `backend/app/orchestrator/router.py` — Task routing logic
- `backend/app/orchestrator/conflict.py` — FAISS duplicate-intent detection
- `backend/app/memory/faiss_store.py` — FAISS vector store
- `backend/app/memory/embeddings.py` — Sentence-transformer embedding (all-MiniLM-L6-v2, 384-dim)
