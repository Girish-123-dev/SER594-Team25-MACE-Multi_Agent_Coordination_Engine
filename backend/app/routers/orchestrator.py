from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.routers.auth import get_current_user

router = APIRouter()


class OrchestratorRequest(BaseModel):
    message: str


class OrchestratorResponse(BaseModel):
    reply: str
    tasks: list[dict] = []
    conflicts: list[dict] = []


@router.post("/run", response_model=OrchestratorResponse)
async def run_orchestrator(body: OrchestratorRequest, user=Depends(get_current_user)):
    # TODO: Wire up LangGraph orchestrator, intent parser, task router, conflict detector
    return OrchestratorResponse(
        reply=f"[MACE stub] Received: {body.message}",
        tasks=[],
        conflicts=[],
    )
