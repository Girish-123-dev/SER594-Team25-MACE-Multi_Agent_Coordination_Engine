import logging

from app.orchestrator.intent import parse_intent
from app.orchestrator.router import route_task
from app.orchestrator.conflict import check_duplicate_intent, store_intent
from app.services.database import Database

logger = logging.getLogger(__name__)


def run_orchestration(user_message: str, user_id: int, db: Database) -> dict:
    duplicate = check_duplicate_intent(user_message, user_id)
    if duplicate and duplicate.get("is_duplicate"):
        logger.info("Request is a duplicate of task_id=%s", duplicate["existing_task_id"])
        return {
            "reply": (
                f"This request is similar to an existing task "
                f"(similarity: {duplicate['similarity_score']:.0%}). "
                f"We're already working on it."
            ),
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

    intent_result = parse_intent(user_message)
    parsed = intent_result["parsed_intent"]
    llm_usage = intent_result["llm_usage"]

    assigned_agent = route_task(parsed)

    task_id = db.create_task(
        user_id=user_id,
        intent=user_message,
        assigned_agent=assigned_agent,
    )

    store_intent(user_message, user_id, task_id)

    result_text = (
        f"Task #{task_id} created and assigned to {assigned_agent} agent.\n"
        f"Intent: {parsed.get('intent_type', 'unknown')} | "
        f"Priority: {parsed.get('priority', 'medium')} | "
        f"Summary: {parsed.get('summary', user_message[:100])}"
    )
    db.update_task(task_id, status="completed", result=result_text)

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
            }
        ],
        "conflicts": [],
        "llm_usage": llm_usage,
    }
