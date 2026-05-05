import logging

from app.orchestrator.intent import parse_intent
from app.orchestrator.router import route_task
from app.orchestrator.conflict import check_duplicate_intent, store_intent
from app.agents import get_agent
from app.memory.conversation import get_conversation_memory
from app.services.database import Database

logger = logging.getLogger(__name__)


def run_orchestration(user_message: str, user_id: int, db: Database) -> dict:
    # Get conversation memory for context
    memory = get_conversation_memory(db)
    memory.add_message(user_id, "user", user_message)
    conv_context = memory.get_context(user_id)

    # Step 1: Check for duplicate intents via FAISS
    duplicate = check_duplicate_intent(user_message, user_id)
    if duplicate and duplicate.get("is_duplicate"):
        logger.info("Request is a duplicate of task_id=%s", duplicate["existing_task_id"])
        reply = (
            f"This request is similar to an existing task "
            f"(similarity: {duplicate['similarity_score']:.0%}). "
            f"We're already working on it."
        )
        memory.add_message(user_id, "assistant", reply)
        return {
            "reply": reply,
            "tasks": [],
            "conflicts": [
                {
                    "type": "duplicate_intent",
                    "similarity": duplicate["similarity_score"],
                    "existing_task_id": duplicate["existing_task_id"],
                    "resolution": "merged_with_existing",
                }
            ],
        }

    # Step 2: Parse intent using LLM with structured output
    intent_result = parse_intent(user_message)
    parsed = intent_result["parsed_intent"]
    llm_usage = intent_result["llm_usage"]

    # Step 3: Route to appropriate agent
    assigned_agent = route_task(parsed)

    # Step 4: Create task record
    task_id = db.create_task(
        user_id=user_id,
        intent=user_message,
        assigned_agent=assigned_agent,
    )

    # Step 5: Store intent embedding in FAISS for future duplicate detection
    store_intent(user_message, user_id, task_id)

    # Step 6: Execute agent workflow
    agent = get_agent(assigned_agent)
    agent_result = agent.execute(parsed, context=conv_context)

    # Step 7: Build result and update task
    result_text = (
        f"[{assigned_agent.upper()} AGENT] Task #{task_id}\n"
        f"Intent: {parsed.get('intent_type', 'unknown')} | "
        f"Priority: {parsed.get('priority', 'medium')}\n\n"
        f"{agent_result.response}"
    )
    db.update_task(task_id, status="completed", result=result_text)

    # Store assistant response in conversation memory
    memory.add_message(user_id, "assistant", agent_result.response)

    return {
        "reply": result_text,
        "tasks": [
            {
                "task_id": task_id,
                "intent_type": parsed.get("intent_type"),
                "assigned_agent": assigned_agent,
                "priority": parsed.get("priority"),
                "summary": parsed.get("summary"),
                "entities": parsed.get("entities", []),
                "status": "completed",
                "agent_steps": agent_result.steps,
                "tools_used": agent_result.tools_used,
            }
        ],
        "conflicts": [],
        "llm_usage": llm_usage,
    }
