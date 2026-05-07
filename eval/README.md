# Evaluation

This directory contains the evaluation suite for MACE. All metrics are computed automatically by `run_eval.py` and written to `results.json`.

## Quick Start

```bash
# From project root — offline metrics (no running server needed)
python eval/run_eval.py

# With live latency measurement (requires running backend + GEMINI_API_KEY)
python eval/run_eval.py --live
```

## Metrics Computed

### Metric 1: Duplicate Detection Precision & Recall

Evaluates the FAISS vector-similarity pipeline for detecting semantically duplicate user requests.

- **Method:** Embeds 10 query pairs (5 true duplicates, 5 non-duplicates) using `all-MiniLM-L6-v2`, computes cosine similarity, and classifies as duplicate if similarity ≥ 0.85.
- **Measures:** Precision, Recall, F1 Score, Accuracy.
- **Baseline:** No deduplication — every request is processed independently (recall = 0%).

### Metric 2: Embedding Quality (Separability)

Measures whether the embedding model can distinguish support-type queries from domain-type queries.

- **Method:** Computes average pairwise cosine similarity within each category (intra-class) and across categories (inter-class).
- **Measures:** Intra-class similarity (support), intra-class similarity (domain), inter-class similarity, separation gap.
- **Interpretation:** Higher intra-class and lower inter-class similarity indicates good separability.

### Metric 3: Intent Routing Accuracy

Evaluates the rule-based task router against known expected assignments.

- **Method:** Feeds 8 pre-classified intent objects through `route_task()` and checks the assigned agent.
- **Measures:** Accuracy (correct / total).
- **Baseline:** Single-agent system with no routing — 50% accuracy at best.

### Metric 4: Agent Tool-Step Consistency

Verifies that each agent executes the expected number of tool steps in its multi-step workflow.

- **Method:** Runs each agent with mocked LLM responses and checks step count and tool names.
- **Measures:** Step count per agent, tool name correctness, overall consistency.

### Metric 5: Response Latency (Live)

Measures end-to-end response time for the full orchestration pipeline.

- **Method:** Sends 5 real requests to the live API, measures wall-clock time per request.
- **Measures:** p50, p95, mean, min, max latency (ms), error rate.
- **Requires:** Running backend with a valid `GEMINI_API_KEY`.

### Baseline Comparison

Compares MACE against a naive baseline (no coordination layer):

| Aspect | Baseline (No Coordination) | MACE |
|--------|---------------------------|------|
| Duplicate Detection | None — all duplicates reprocessed | FAISS cosine similarity (threshold ≥ 0.85) |
| Intent Routing | Single agent handles everything | LLM intent parsing + rule-based multi-agent routing |
| Conversation Memory | Stateless — each request isolated | Per-user history with LLM auto-summarization |

## Output

Results are written to `eval/results.json` with full detail for each metric including per-pair/per-case breakdowns.

## Test Coverage

Run from the project root:

```bash
# Backend tests (48 tests)
python3 -m pytest tests/backend/ -v

# Frontend tests (5 tests)
cd frontend && npm test
```

| Test File | Tests | Covers |
|-----------|-------|--------|
| `test_api.py` | 12 | Health, register, login, auth, orchestrator endpoints, history |
| `test_database.py` | 6 | User CRUD, task CRUD |
| `test_faiss.py` | 6 | Add/search, duplicates, persist/reload, embedding dimensions |
| `test_llm.py` | 4 | LLM response, JSON parsing, error handling, token tracking |
| `test_pipeline.py` | 7 | Task routing, full pipeline execution, duplicate detection |
| `test_agents.py` | 8 | Agent registry, support agent, domain agent, escalation logic |
| `test_conversation.py` | 5 | Conversation memory, context retrieval, user isolation |
