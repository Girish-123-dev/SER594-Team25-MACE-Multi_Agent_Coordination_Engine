import logging

from app.memory.faiss_store import get_faiss_store
from app.config import settings

logger = logging.getLogger(__name__)


def check_duplicate_intent(user_message: str, user_id: int) -> dict | None:
    store = get_faiss_store()
    duplicates = store.find_duplicates(user_message)

    for dup in duplicates:
        if dup.get("user_id") == user_id and dup.get("status") == "pending":
            logger.info(
                "Duplicate intent detected (score=%.3f): '%s' matches existing '%s'",
                dup["score"],
                user_message[:50],
                dup.get("text", "")[:50],
            )
            return {
                "is_duplicate": True,
                "existing_task_id": dup.get("task_id"),
                "similarity_score": dup["score"],
                "existing_text": dup.get("text", ""),
            }

    return None


def store_intent(user_message: str, user_id: int, task_id: int):
    store = get_faiss_store()
    store.add(
        text=user_message,
        metadata={"user_id": user_id, "task_id": task_id, "status": "pending"},
    )
    logger.info("Stored intent embedding (task_id=%d, total=%d)", task_id, store.total_vectors)
