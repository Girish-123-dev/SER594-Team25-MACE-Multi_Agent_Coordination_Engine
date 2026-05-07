# Design Decisions, Trade-offs & Lessons Learned

## Design Decisions

### 1. Google Gemini over Claude / OpenAI

We chose the **Google Gemini API** (`gemini-2.5-flash-lite`) as our LLM provider.

- **Reason:** Free-tier availability for a student project, structured JSON output support, and a unified Python SDK (`google-genai`).
- **Abstraction:** We built a `BaseLLMService` abstract class so the provider can be swapped by implementing a single `complete()` method. Switching to OpenAI or Claude requires only a new subclass — no orchestrator changes.
- **File:** `backend/app/services/llm.py`

### 2. SQLite over PostgreSQL

We use **SQLite** for all relational data (users, tasks, conversations, conflicts).

- **Reason:** Zero-config, file-based, no separate server process, sufficient for demo-scale workloads.
- **Persistence:** The database file is stored in a Docker volume (`mace-data`) so it survives container restarts.
- **Trade-off:** SQLite has limited concurrency (single-writer). For a production system with many concurrent users, we would switch to PostgreSQL.
- **File:** `backend/app/services/database.py`

### 3. FAISS Inner-Product Index

We use `faiss.IndexFlatIP` (inner-product) rather than a cosine-specific index.

- **Reason:** Our embeddings are L2-normalized (via `normalize_embeddings=True` in sentence-transformers), which makes inner-product equivalent to cosine similarity. FAISS is optimized for inner-product operations.
- **Trade-off:** `IndexFlatIP` is a brute-force index. For millions of vectors, we would switch to `IndexIVFFlat` or `IndexHNSW`. At our scale (hundreds of intents), brute-force is fast enough and simpler.
- **File:** `backend/app/memory/faiss_store.py`

### 4. Sentence-Transformers (`all-MiniLM-L6-v2`)

We chose **all-MiniLM-L6-v2** as our embedding model.

- **Reason:** Lightweight (~80 MB), fast CPU inference, produces high-quality 384-dimensional embeddings. No GPU required.
- **Trade-off:** Larger models (e.g., `all-mpnet-base-v2`, 768-dim) produce higher-quality embeddings but are 3× larger and slower. For intent deduplication and knowledge retrieval, MiniLM is sufficient.
- **File:** `backend/app/memory/embeddings.py`

### 5. Linear Pipeline over LangGraph State Graph

The original plan specified a LangGraph state graph with conditional edges. We implemented a **linear pipeline** instead.

- **Reason:** The orchestration flow is naturally sequential (check duplicates → parse intent → route → execute → save). A state graph adds complexity without benefit when there are no parallel branches or cycles.
- **Trade-off:** A state graph would enable parallel agent execution and more complex conditional flows. Our linear pipeline is easier to test, debug, and reason about.
- **Compromise:** We kept `langgraph` in dependencies for future extensibility but the current orchestrator uses a straightforward function pipeline.
- **File:** `backend/app/orchestrator/pipeline.py`

### 6. JWT Authentication with bcrypt

We use **JWT tokens** for stateless authentication and **bcrypt** for password hashing.

- **Reason:** JWT allows the frontend to include the token in every request header without server-side session storage. bcrypt is the industry standard for password hashing with automatic salting.
- **Configuration:** Token expiration is set to 60 minutes. The JWT secret is loaded from `.env` (never hardcoded).
- **File:** `backend/app/routers/auth.py`

### 7. Two Specialized Agents (Support + Domain)

We implemented exactly **two agents** rather than many.

- **Reason:** Two agents are sufficient to demonstrate all coordination patterns (routing, deduplication, conflict detection, memory sharing). Each agent has 4-5 distinct tools in its workflow, satisfying the "3+ tools" requirement.
- **Trade-off:** More agent types (DevOps, Security, HR) would showcase larger-scale coordination but add implementation scope without demonstrating new architectural patterns.
- **Files:** `backend/app/agents/support_agent.py`, `backend/app/agents/domain_agent.py`

### 8. Docker Compose Deployment

We deploy with **Docker Compose** (two services: backend + frontend).

- **Reason:** Reproducible single-command deployment (`docker compose up --build`). No cloud provider lock-in. Works on any machine with Docker installed.
- **Trade-off:** Not a public URL by default. For production, we would push images to a container registry and deploy to GCP Cloud Run or AWS ECS.
- **File:** `docker-compose.yml`

---

## Trade-offs Summary

| Decision | Chose | Over | Why |
|----------|-------|------|-----|
| LLM Provider | Gemini (free tier) | Claude / OpenAI | Cost, student-friendly, good JSON output |
| Database | SQLite | PostgreSQL | Zero-config, sufficient for demo scale |
| Vector Index | FAISS brute-force | FAISS IVF / HNSW | Simpler, fast enough at our scale |
| Embedding Model | MiniLM-L6-v2 (384-dim) | mpnet-base-v2 (768-dim) | Smaller, faster, no GPU needed |
| Orchestration | Linear pipeline | LangGraph state graph | Simpler to test and debug |
| Agent Count | 2 agents | Many agents | Sufficient to demonstrate coordination |
| Deployment | Docker Compose | Cloud Run | Portable, no cloud costs |

---

## Lessons Learned

### 1. LLM Output Is Not Always Valid JSON

**Problem:** Gemini frequently wraps JSON output in markdown code fences (`` ```json ... ``` ``) even when explicitly instructed not to.

**Solution:** We added a fallback parser that strips markdown fences using regex before attempting `json.loads()`. We also implemented a complete fallback intent object when parsing fails entirely.

**Takeaway:** Never trust an LLM to produce exact output format. Always implement defensive parsing with fallbacks.

### 2. Embedding Model Loading Time Matters

**Problem:** The first request after startup took 5-10 seconds because `sentence-transformers` downloads and loads the model on first use.

**Solution:** We use a lazy singleton pattern — the model is loaded once on the first call and reused for all subsequent requests. In Docker, the model is cached in the image layer.

**Takeaway:** Heavy ML model initialization should be deferred and cached, not done on every request.

### 3. FAISS Index Persistence Requires Explicit Saves

**Problem:** FAISS indices are in-memory by default. Container restarts would lose all stored embeddings.

**Solution:** We call `faiss.write_index()` after every `add()` operation and `faiss.read_index()` on startup. The index file is stored in a Docker volume.

**Takeaway:** In-memory data structures need an explicit persistence strategy when running in containers.

### 4. Duplicate Detection Threshold Is Sensitive

**Problem:** A cosine threshold of 0.85 sometimes flags unrelated queries as duplicates if they share common words (e.g., "reset my password" vs "reset my laptop settings").

**Solution:** We made `SIMILARITY_THRESHOLD` configurable via `.env` so it can be tuned per deployment. We also scope duplicate checks to the same user and only "pending" tasks.

**Takeaway:** Similarity thresholds should be configurable, not hardcoded. Scoping (by user, by status) reduces false positives.

### 5. Testing AI Components Requires Mocking

**Problem:** Running tests against a live LLM API is slow, expensive, and non-deterministic. Tests that depend on Gemini responses break when the API changes output format.

**Solution:** All 48 backend tests use mocked LLM responses. The mock returns predictable JSON, making tests fast (~2 seconds) and deterministic.

**Takeaway:** AI-integrated tests should mock the AI layer and test the integration logic, not the AI model itself.

### 6. Monorepo Structure Simplifies Deployment

**Problem:** Separate repositories for frontend and backend add deployment complexity and version synchronization overhead.

**Solution:** A single monorepo with `frontend/`, `backend/`, `tests/`, `eval/`, and `docs/` directories. Docker Compose references both services from the same repo.

**Takeaway:** For small team projects, a monorepo reduces coordination overhead and simplifies CI/CD.
