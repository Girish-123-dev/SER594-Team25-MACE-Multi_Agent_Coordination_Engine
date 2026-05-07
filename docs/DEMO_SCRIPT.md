# MACE Demo Video Script — Team 25

**Target Duration:** 12–14 minutes  
**Speakers:** Akash, Girish, Arpit, Anmol  
**Rule:** Each member introduces themselves on camera (name + face visible).

---

## SECTION 1 — Use Case Walkthrough (~3 min)

**Presenter: Akash**

> *[Camera on — face visible]*
>
> "Hi, I'm **Akash**, and I worked on the orchestration pipeline for MACE. Let me start by explaining the problem we're solving."
>
> "Imagine you're running a growing tech company. Your users submit all kinds of requests — support tickets like 'my laptop keeps crashing', knowledge queries like 'how does B-tree indexing work', and sometimes both in the same message. Today, most systems route everything through a single pipeline. That creates chaos: support requests get treated like research tasks, knowledge queries sit in a ticket queue, and duplicate requests pile up because there's no deduplication."
>
> "Our target user is any organization that deals with a high volume of mixed requests — IT help desks, enterprise support teams, internal knowledge platforms."
>
> "MACE — the Multi-Agent Coordination Engine — solves this. Let me walk you through the primary use case."
>
> "A user opens our web app, registers or logs in, and types a message — say, 'My laptop keeps crashing when I open Excel.' Behind the scenes, MACE does the following:"
>
> "**Step 1 — Duplicate Detection.** Before anything else, we check if this request is semantically similar to something the user already submitted. We use FAISS with sentence-transformer embeddings to do a cosine-similarity check. If the similarity is above 85%, we flag it as a duplicate and tell the user we're already working on it. This prevents redundant work."
>
> "**Step 2 — Intent Parsing.** The message goes to Google Gemini, which classifies the intent — is this a support ticket, a FAQ, an escalation, a domain lookup, or a multi-step task requiring multiple agents? The LLM returns structured JSON with the intent type, priority, entities, and which agents are needed."
>
> "**Step 3 — Routing.** Based on the classified intent, our rule-based router sends the task to the right agent. Support tickets go to the Support Agent, domain lookups go to the Domain Agent, and multi-step requests go to both."
>
> "**Step 4 — Agent Execution.** The assigned agent runs a multi-tool workflow — the Support Agent uses four tools, the Domain Agent uses up to five — including RAG retrieval from our FAISS knowledge base, LLM-powered response generation, and self-validation."
>
> "**Step 5 — Response.** The user gets back a structured response with the agent name, task ID, priority, and the actual answer. All of this is stored in conversation memory for future context."
>
> "That's the full use case — from user input to intelligent, routed, deduplicated response."

---

## SECTION 2 — System Architecture (~3.5 min)

**Presenter: Girish**

> *[Camera on — face visible]*
>
> "Hi, I'm **Girish**, and I built the Domain Agent and the FAISS vector search layer. Let me walk you through our system architecture."
>
> *[Show the architecture diagram — `docs/architecture.mmd` or `Architecture_Diagram.pdf`]*
>
> "MACE has three main layers: Frontend, Backend, and Data."

### Frontend

> "The **frontend** is a React 18 single-page application built with Vite. It has three pages — Login, Register, and the main Dashboard. The Dashboard is where all the action happens — it's a chat interface where users type messages and see agent responses. We serve the built frontend through Nginx in a Docker container on port 3000."
>
> "One important UI feature: we modified the Dashboard to support **concurrent requests**. Instead of a single global loading state that blocks the Send button, each message gets its own unique ID and its own loading spinner. So a user can fire off two queries back-to-back and watch two agents process them in parallel — which is exactly what we'll demo later."

### Backend

> "The **backend** is a Python FastAPI application running with Uvicorn on port 8000. It's organized into four main packages:"
>
> "First, **Routers** — these are FastAPI route handlers. We have three: `auth.py` for registration and login, `health.py` for health checks, and `orchestrator.py` which is the main endpoint that receives user messages."
>
> "Second, the **Orchestrator** — this is the brain of the system. It has four modules:"
> - "`pipeline.py` — the main 7-step orchestration flow that ties everything together"
> - "`intent.py` — the LLM-based intent parser that sends the user message to Gemini with a structured system prompt and gets back JSON with intent type, priority, entities, and required agents"
> - "`router.py` — a deterministic rule-based router that maps intent types to agents. Support tickets, FAQs, and escalations go to the Support Agent. Domain lookups go to the Domain Agent. Multi-step requests with multiple agents go to both"
> - "`conflict.py` — the duplicate detection module that uses FAISS to check for semantically similar past requests before processing"
>
> "Third, the **Agents** — we have two specialized agents that inherit from `BaseAgent`. Each agent runs a multi-tool workflow — I'll let Arpit cover those in the code walkthrough."
>
> "Fourth, the **Services** layer:"
> - "`llm.py` — a swappable LLM service with a `BaseLLMService` abstract class. Our implementation, `GeminiService`, wraps the Google Gemini API with 3x retry logic, exponential backoff, automatic JSON extraction — including handling Gemini's habit of wrapping JSON in markdown fences — and full token usage tracking"
> - "`database.py` — SQLite for user accounts, tasks, and conversation history"

### Data Layer

> "The **data layer** has two components:"
>
> "**SQLite** stores users, tasks, and conversation messages. The conversation memory system tracks per-user history and automatically summarizes old messages using the LLM when the count exceeds 20 — so the context window stays manageable but we don't lose information."
>
> "**FAISS** — Facebook AI Similarity Search — is our vector database. We use `IndexFlatIP` for inner-product (cosine) similarity over 384-dimensional vectors. The embedding model is `all-MiniLM-L6-v2` from Sentence Transformers. Every user message gets embedded and stored in FAISS. This powers two things: duplicate detection in the conflict module, and RAG retrieval in both agents. The index is persisted to disk and loaded on startup."

### Infrastructure

> "Everything runs in Docker Compose — two containers: backend and frontend, with a named volume `mace-data` for persistent storage. The `.env` file holds the Gemini API key, model name, database path, and similarity threshold. One `docker compose up --build` and the entire system is running."

---

## SECTION 3 — Code Walkthrough (~4 min)

**Presenter: Arpit**

> *[Camera on — face visible]*
>
> "Hi, I'm **Arpit**, and I built the Support Agent and the authentication system. Let me walk you through the key code, focusing on AI integration, design patterns, and engineering decisions."

### Design Pattern: Abstract Base Agent

> *[Show `backend/app/agents/base.py`]*
>
> "We start with the **Strategy pattern**. `BaseAgent` is an abstract class with an `execute` method that takes a parsed intent and optional conversation context, and returns an `AgentResult` — which contains the response text, a list of steps the agent took, and the tools it used. Both the Support Agent and Domain Agent inherit from this, so the orchestrator doesn't need to know which agent it's calling — it just calls `execute`. This makes the system extensible: adding a new agent means creating one more subclass."

### Support Agent — Multi-Tool Workflow

> *[Show `backend/app/agents/support_agent.py`]*
>
> "The Support Agent runs a **four-tool workflow**:"
>
> "**Tool 1 — `knowledge_lookup`**: We query the FAISS store for the top 3 similar past issues with a score above 0.3. This is our RAG retrieval step — giving the LLM real context instead of relying purely on parametric knowledge."
>
> "**Tool 2 — `classify_priority`**: We send the user's summary to Gemini with a dedicated priority-classification system prompt. It returns JSON with a priority level — low, medium, or high — and a reason. System outages and security issues get high, feature requests get low. If the LLM call fails, we fall back to the priority from the intent parser."
>
> "**Tool 3 — `generate_response`**: This is the main RAG step. We build a prompt that includes the user's request, extracted entities, and the similar past issues from Tool 1. Gemini generates a contextual support response under 200 words."
>
> "**Tool 4 — `escalation_check`**: We check if the issue is high-priority and involves critical keywords like 'security breach' or 'data loss'. If so, the response gets flagged for human escalation."

### Domain Agent — Five-Tool Workflow with Self-Critique

> *[Show `backend/app/agents/domain_agent.py`]*
>
> "The Domain Agent has **five tools** — and the interesting one is the self-critique loop:"
>
> "**Tool 1 — `extract_entities`**: LLM extracts structured entities from the query — name, type, and relevance."
>
> "**Tool 2 — `semantic_search`**: We search FAISS with the original query AND high-relevance entities. Results are deduplicated and sorted by score. This gives broader coverage than a single-query search."
>
> "**Tool 3 — `synthesize_answer`**: LLM synthesizes a response from all retrieved context."
>
> "**Tool 4 — `validate_response`**: Here's the AI-powered self-critique. We send the generated answer back to Gemini with a validation prompt. It returns a quality score from 0 to 1 and flags any issues."
>
> "**Tool 5 — `refine_response`**: If validation fails — if `is_acceptable` is false — we run a refinement step that takes the issues list and regenerates the answer. This is a form of LLM self-correction that improves output quality."

### LLM Service — Swappable Provider

> *[Show `backend/app/services/llm.py`]*
>
> "The LLM service uses the **Dependency Inversion principle**. `BaseLLMService` is an abstract class. `GeminiService` is our concrete implementation. If we wanted to swap to OpenAI or a local model, we'd just create a new subclass and change one line in `get_llm_service()`."
>
> "Key engineering decisions here: we do 3x retries with exponential backoff for server errors and rate limits. Gemini often wraps JSON in markdown code fences, so we have a regex fallback that strips those. We track input/output tokens and latency for every call — that data flows into our evaluation metrics."

### Authentication

> *[Show `backend/app/routers/auth.py`]*
>
> "Authentication uses **JWT with bcrypt**. Passwords are hashed with bcrypt before storage — never stored in plaintext. On login, we issue a JWT token with a 60-minute expiration. Every protected endpoint — like the orchestrator — requires a valid Bearer token. The `get_current_user` dependency validates the token and extracts the user ID."

### FAISS Duplicate Detection

> *[Show `backend/app/orchestrator/conflict.py` and `backend/app/memory/faiss_store.py`]*
>
> "For chaos reduction, the conflict module is critical. Before any LLM call, we embed the user's message and search FAISS for matches above our 0.85 cosine similarity threshold. If a match is found for the same user, we short-circuit the entire pipeline — no LLM cost, no duplicate work. After processing, we store the new intent embedding so future duplicates are caught. The FAISS index persists to disk, so it survives container restarts."

---

## SECTION 4 — Functional Demo (~3.5 min)

**Presenter: Anmol**

> *[Camera on — face visible]*
>
> "Hi, I'm **Anmol**, and I built the frontend and evaluation framework. Let me show you MACE in action."
>
> *[Share screen — open browser to `http://localhost:3000`]*

### Registration & Login

> "First, I'll register a new account. I'll enter a username, email, and password."
>
> *[Fill in the Register form and submit]*
>
> "We get redirected to Login. I'll log in with the same credentials."
>
> *[Log in — Dashboard appears]*
>
> "We're now on the Dashboard. On the left, we have the task history panel. On the right, the chat interface."

### Demo 1 — Support Agent

> "Let me send a support request: **'My laptop keeps crashing when I open Excel'**."
>
> *[Type and send]*
>
> "You can see a loading spinner appears for this message. Behind the scenes, the orchestrator is: checking for duplicates in FAISS, parsing intent with Gemini — which classifies this as a `support_ticket` — routing it to the Support Agent, and running the four-tool workflow."
>
> *[Response appears]*
>
> "The response shows: `[SUPPORT AGENT] Task #1`, the intent type is `support_ticket`, priority is medium, and the agent gives actionable troubleshooting steps. The task also appears in the task history on the left."

### Demo 2 — Domain Agent

> "Now let me send a domain query: **'Do a domain lookup on how B-tree indexing works in database systems'**."
>
> *[Type and send]*
>
> "This time, Gemini classifies it as `domain_lookup`, and the router sends it to the Domain Agent. The Domain Agent runs its five-tool workflow — entity extraction, semantic search, synthesis, validation, and potentially refinement."
>
> *[Response appears]*
>
> "The response shows `[DOMAIN AGENT]` — different agent, different workflow, same seamless interface."

### Demo 3 — Concurrent Processing

> "Now here's where our concurrency feature shines. I'm going to send **two messages back-to-back** without waiting for the first to finish."
>
> "First: **'I need to reset my VPN password'** — *send* — and immediately: **'Do a domain lookup on how neural networks learn through backpropagation'** — *send*."
>
> *[Type first, send, immediately type second, send]*
>
> "Notice both messages have their own individual loading spinners. Both requests are being processed in parallel on the backend. This is not just a UI trick — FastAPI handles these as concurrent async requests."
>
> *[Both responses come back]*
>
> "The first went to the Support Agent, the second to the Domain Agent. Two different agents, two different workflows, running concurrently."

### Demo 4 — Duplicate Detection (Chaos Reduction)

> "Finally, let me demonstrate our chaos reduction feature. I'll send a very similar request to one I already sent: **'My laptop crashes every time I open Excel'**."
>
> *[Type and send]*
>
> "Look at the response — it says 'This request is similar to an existing task' with a similarity score. The system detected this is a near-duplicate of my first request using FAISS cosine similarity. It didn't waste an LLM call — it short-circuited the pipeline and told me it's already being handled. That's conflict resolution in action."

### Evaluation Results

> "We also built an automated evaluation framework that measures five metrics:"
> - "**Duplicate detection** — precision, recall, and F1 score"
> - "**Embedding quality** — separability between different intent categories"
> - "**Routing accuracy** — whether intents map to the correct agent"
> - "**Agent consistency** — whether each agent executes the expected number of tool steps"
> - "**Response latency** — p50 and p95 latency for live requests"
>
> "In our evaluation run, we achieved 100% routing accuracy, F1 of 0.75 for duplicate detection, and both agents consistently executed their full tool workflows."

---

## CLOSING (~30 sec)

**All members on camera**

> **Akash:** "To summarize — MACE demonstrates how multi-agent coordination with LLM-based intent parsing, vector-based deduplication, and specialized agent workflows can bring order to chaotic request handling."
>
> **Girish:** "The architecture is modular, containerized, and designed for extensibility."
>
> **Arpit:** "Every AI integration — from intent parsing to self-critique — serves a concrete engineering purpose."
>
> **Anmol:** "And as we showed, it works end-to-end with real inputs and real outputs. Thank you."

---

## Quick Reference — Demo Queries

| Query | Expected Agent | Intent Type |
|---|---|---|
| My laptop keeps crashing when I open Excel | Support | support_ticket |
| Do a domain lookup on how B-tree indexing works in database systems | Domain | domain_lookup |
| I need to reset my VPN password | Support | support_ticket |
| Do a domain lookup on how neural networks learn through backpropagation | Domain | domain_lookup |
| My laptop crashes every time I open Excel *(duplicate of #1)* | — (blocked) | duplicate_intent |
