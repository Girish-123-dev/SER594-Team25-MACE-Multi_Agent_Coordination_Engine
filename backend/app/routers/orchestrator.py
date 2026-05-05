import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.routers.auth import get_current_user
from app.services.database import get_db, Database
from app.orchestrator.pipeline import run_orchestration
from app.memory.conversation import get_conversation_memory

logger = logging.getLogger(__name__)
router = APIRouter()


class OrchestratorRequest(BaseModel):
    message: str


class OrchestratorResponse(BaseModel):
    reply: str
    tasks: list[dict] = []
    conflicts: list[dict] = []


@router.post("/run", response_model=OrchestratorResponse)
async def run_orchestrator(
    body: OrchestratorRequest,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    try:
        result = run_orchestration(body.message, user["id"], db)
        return OrchestratorResponse(
            reply=result["reply"],
            tasks=result.get("tasks", []),
            conflicts=result.get("conflicts", []),
        )
    except Exception as e:
        logger.exception("Orchestration failed")
        raise HTTPException(status_code=500, detail=f"Orchestration error: {str(e)}")


@router.get("/tasks")
async def get_tasks(user=Depends(get_current_user), db: Database = Depends(get_db)):
    rows = db.get_tasks_by_user(user["id"])
    return [
        {
            "id": r["id"],
            "intent": r["intent"],
            "status": r["status"],
            "assigned_agent": r["assigned_agent"],
            "result": r["result"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


@router.get("/history")
async def get_conversation_history(user=Depends(get_current_user), db: Database = Depends(get_db)):
    """Get conversation history for the current user."""
    memory = get_conversation_memory(db)
    history = memory.get_history(user["id"], limit=50)
    context = memory.get_context(user["id"])
    return {
        "messages": history,
        "summary": context.get("summary"),
        "total_messages": context.get("total_messages", 0),
    }
