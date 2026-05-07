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

> Full Mermaid diagram: [docs/architecture.mmd](docs/architecture.mmd) | PDF export: [docs/Architecture_Diagram.pdf](docs/Architecture_Diagram.pdf)

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
| AI / ML | Google Gemini API (e.g. Flash-Lite), FAISS (faiss-cpu), Sentence-Transformers |
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
│   │   ├── memory/         # FAISS store, sentence-transformer embeddings, conversation memory
│   │   ├── agents/         # Support Agent, Domain Agent (multi-step workflows)
│   │   └── models/         # Pydantic schemas
│   ├── requirements.txt
│   └── Dockerfile
├── tests/
│   └── backend/            # 48 pytest tests (API, DB, FAISS, LLM, Pipeline, Agents, Conversation)
├── docs/
│   ├── architecture.mmd       # Mermaid architecture diagram
│   ├── Architecture_Diagram.pdf  # Exported architecture diagram
│   ├── DESIGN.md              # Design decisions, trade-offs, lessons learned
│   └── PROJECT_PLAN.txt       # Full project plan
├── eval/                      # Evaluation suite
│   ├── run_eval.py            # Automated evaluation script (5 metrics)
│   ├── results.json           # Latest evaluation results
│   └── README.md              # Evaluation methodology documentation
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
# Edit .env and set your GEMINI_API_KEY (from Google AI Studio)
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
| `GEMINI_API_KEY` | Google AI Studio API key for Gemini | *(required)* |
| `GOOGLE_API_KEY` | Alternative env name for the same Gemini key | *(optional)* |
| `MODEL_NAME` | Gemini model id | `gemini-2.5-flash-lite` |
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

48 tests across 7 files:

| File | Tests | Covers |
|------|-------|--------|
| `test_api.py` | 12 | Health, register, login, auth, orchestrator endpoints, history |
| `test_database.py` | 6 | User CRUD, task CRUD |
| `test_faiss.py` | 6 | Add/search, duplicates, persist/reload, embedding dimensions |
| `test_llm.py` | 4 | LLM response, JSON parsing, error handling, token tracking |
| `test_pipeline.py` | 7 | Task routing, full pipeline execution, duplicate detection |
| `test_agents.py` | 8 | Agent registry, support agent, domain agent, escalation logic |
| `test_conversation.py` | 5 | Conversation memory, context retrieval, user isolation |

Frontend tests (5 tests):
```bash
cd frontend && npm test
```

CI runs automatically on every push and pull request via GitHub Actions (`.github/workflows/ci.yml`).

## Evaluation

The evaluation suite computes 5 quantitative metrics with baseline comparisons. Full methodology is documented in [`eval/README.md`](eval/README.md).

```bash
# Offline metrics (no running server needed)
python3 eval/run_eval.py

# Include live API latency measurement (requires running backend)
python3 eval/run_eval.py --live
```

**Latest Results:**

| Metric | Result |
|--------|--------|
| Duplicate Detection Precision | **1.0** (no false positives) |
| Duplicate Detection Recall | **0.6** (3/5 duplicates caught at threshold 0.85) |
| Duplicate Detection F1 | **0.75** |
| Embedding Separability Gap | **+0.175** (support) / **+0.133** (domain) vs inter-class |
| Intent Routing Accuracy | **100%** (8/8 correct) |
| Agent Tool-Step Consistency | **Both agents consistent** (4 steps each) |
| Response Latency p50 | ~9.4s (end-to-end including LLM call) |
| Error Rate | 20% (1/5 requests) |

**Baseline comparison:** Without MACE, duplicate requests are always reprocessed (recall=0%), all tasks go to a single agent (routing accuracy ~50%), and follow-up messages lose all context. See [`eval/results.json`](eval/results.json) for full details.

## Design Decisions & Lessons Learned

See [`docs/DESIGN.md`](docs/DESIGN.md) for detailed documentation of:
- Design decisions (LLM provider choice, database, index type, pipeline architecture)
- Trade-offs (simplicity vs. sophistication, SQLite vs. distributed DB, 2 agents vs. many)
- Lessons learned (LLM output parsing, model loading, FAISS persistence, threshold tuning, testing AI components)

## How to Authenticate

1. **Register** — Go to `http://localhost:5173/register` and create an account.
2. **Login** — Go to `http://localhost:5173/login` and enter your credentials. A JWT token is stored automatically.
3. **Dashboard** — After login you are redirected to `/dashboard`. All API calls include the token via `Authorization: Bearer <token>`.
4. **Two-user sessions** — Log out, register a second user, and log in. Each user sees only their own task history.

## AI Technique #1 — LLM API Integration (Google Gemini)

**LLM API Integration** using the Google Gemini API (default: **gemini-2.5-flash-lite**) for intent parsing and agent reasoning.

**Capabilities:**
- Parses natural-language messages into structured JSON (intent type, entities, priority, required agents)
- Structured output parsing with JSON schema enforcement
- 3× retry with exponential backoff on rate-limit and server errors
- Tracks input/output tokens and latency per request
- Swappable LLM backend (`BaseLLMService` ABC → `GeminiService`)

**Key files:**
- `backend/app/services/llm.py` — Gemini API wrapper (retries, token tracking)
- `backend/app/orchestrator/intent.py` — Intent parser (LLM prompt + JSON extraction)

---

## AI Technique #2 — Vector Search / Embeddings (FAISS + Sentence-Transformers)

**Custom embedding pipeline** using `all-MiniLM-L6-v2` (384-dim) and FAISS for duplicate intent detection and knowledge retrieval.

**Capabilities:**
- Embeds user messages into dense vectors using sentence-transformers
- Indexes vectors in a FAISS inner-product index for fast similarity search
- Detects duplicate intents (configurable cosine threshold, default 0.85)
- Persists index to disk and reloads on startup
- Agents use semantic search to retrieve relevant past interactions

**Key files:**
- `backend/app/memory/embeddings.py` — Sentence-transformer embedding model
- `backend/app/memory/faiss_store.py` — FAISS vector store (add, search, find_duplicates, persist)
- `backend/app/orchestrator/conflict.py` — Duplicate detection using FAISS

---

## AI Technique #3 — AI Agents / Multi-Step Workflows

**Two specialized agents** (Support Agent, Domain Agent) that execute multi-step workflows with 4+ tools each.

**Support Agent** (handles support tickets, FAQs, escalations):
1. `knowledge_lookup` — searches FAISS for similar resolved tickets
2. `classify_priority` — uses LLM to classify/confirm priority
3. `generate_response` — generates contextual response using LLM + retrieved context
4. `escalation_check` — determines if human escalation is needed

**Domain Agent** (handles domain lookups and knowledge synthesis):
1. `extract_entities` — uses LLM to extract structured entities from query
2. `semantic_search` — deep search of FAISS knowledge base with entity enrichment
3. `synthesize_answer` — uses LLM to synthesize information from multiple sources
4. `validate_response` — self-critique loop to validate answer quality
5. `refine_response` — (conditional) refines answer if validation fails

**Key files:**
- `backend/app/agents/base.py` — Abstract base agent class
- `backend/app/agents/support_agent.py` — Support agent with 4 tools
- `backend/app/agents/domain_agent.py` — Domain agent with 5 tools
- `backend/app/agents/__init__.py` — Agent registry and lookup

---

## AI Technique #4 — Memory / Conversation Management

**Persistent conversation history** with automatic summarization when context exceeds threshold.

**Capabilities:**
- Stores per-user conversation history (user + assistant messages)
- Summarizes old messages using LLM when history exceeds 20 messages
- Provides context (summary + recent messages) to agents for continuity
- User isolation — each user has their own conversation state
- Persists across sessions via SQLite

**Key files:**
- `backend/app/memory/conversation.py` — ConversationMemory class with summarization
- `backend/app/routers/orchestrator.py` — `/history` endpoint for conversation retrieval

---

## How to Use Each Feature

1. **Register** — Go to `http://localhost:5173/register` and create an account.
2. **Login** — Go to `http://localhost:5173/login` and enter your credentials. A JWT token is stored automatically.
3. **Submit a Task** — On the Dashboard, type a natural-language request (e.g., *"I forgot my password"* or *"How do I configure VPN access?"*). The system will:
   - Check for duplicate intents via FAISS
   - Parse intent using Gemini (structured JSON output)
   - Route to the appropriate agent (Support or Domain)
   - Execute the agent's multi-step workflow
   - Store the interaction in conversation memory
   - Return the result with agent steps and tool usage
4. **View Task History** — The Dashboard displays all your past tasks with their status, assigned agent, and result.
5. **Conversation Memory** — The system remembers prior interactions. Ask follow-up questions and the agents will have context from your previous requests.
6. **Two-user sessions** — Log out, register a second user, and log in. Each user sees only their own data.

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

# Run orchestrator
curl -X POST http://localhost:8000/api/orchestrator/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"message":"I need help resetting my password"}'

# Get task history
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/orchestrator/tasks

# Get conversation history
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/orchestrator/history
```

---

## Deployment

The system is deployed and reproducible locally via Docker Compose.

```bash
docker compose up --build
# Frontend → http://localhost:3000
# Backend API → http://localhost:8000
# Health check → http://localhost:8000/health
```

The `docker-compose.yml` bundles:
- **backend** — FastAPI + Uvicorn (Python 3.11)
- **frontend** — React (Vite build) served via Nginx

Data is persisted via a Docker volume (`mace-data`).
