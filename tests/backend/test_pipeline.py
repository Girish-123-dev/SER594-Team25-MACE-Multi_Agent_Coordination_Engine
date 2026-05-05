"""Tests for the orchestrator pipeline and agent execution."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.orchestrator.pipeline import run_orchestration  # noqa: E402
from app.orchestrator.router import route_task  # noqa: E402
from app.services.database import Database  # noqa: E402
from app.services.llm import LLMResponse  # noqa: E402


@pytest.fixture
def db(tmp_path):
    return Database(str(tmp_path / "test_pipeline.db"))


def _mock_llm_response(content: str, parsed: dict | None = None):
    return LLMResponse(
        content=content,
        parsed=parsed,
        input_tokens=10,
        output_tokens=20,
        model="test-model",
        latency_ms=100.0,
    )


def test_route_task_support_ticket():
    parsed = {"intent_type": "support_ticket", "requires_agents": ["support"]}
    assert route_task(parsed) == "support"


def test_route_task_domain_lookup():
    parsed = {"intent_type": "domain_lookup", "requires_agents": ["domain"]}
    assert route_task(parsed) == "domain"


def test_route_task_multi_step():
    parsed = {"intent_type": "multi_step", "requires_agents": ["support", "domain"]}
    assert route_task(parsed) == "both"


def test_route_task_general_defaults_to_support():
    parsed = {"intent_type": "general", "requires_agents": []}
    assert route_task(parsed) == "support"


def test_route_task_faq_query():
    parsed = {"intent_type": "faq_query", "requires_agents": ["support"]}
    assert route_task(parsed) == "support"


@patch("app.orchestrator.pipeline.get_conversation_memory")
@patch("app.orchestrator.pipeline.get_agent")
@patch("app.orchestrator.pipeline.store_intent")
@patch("app.orchestrator.pipeline.check_duplicate_intent")
@patch("app.orchestrator.pipeline.parse_intent")
def test_full_pipeline_execution(mock_parse, mock_dup, mock_store, mock_agent, mock_memory, db):
    # Setup mocks
    mock_dup.return_value = None
    mock_parse.return_value = {
        "parsed_intent": {
            "intent_type": "support_ticket",
            "summary": "Reset my password",
            "entities": ["password"],
            "priority": "medium",
            "requires_agents": ["support"],
            "has_dependency": False,
        },
        "llm_usage": {"input_tokens": 10, "output_tokens": 20, "model": "test", "latency_ms": 50},
    }

    mock_agent_instance = MagicMock()
    mock_agent_instance.execute.return_value = MagicMock(
        response="Password reset initiated.",
        steps=[{"tool": "knowledge_lookup", "details": "Found 2 similar issues"}],
        tools_used=["knowledge_lookup", "generate_response"],
    )
    mock_agent.return_value = mock_agent_instance

    mock_memory_instance = MagicMock()
    mock_memory_instance.get_context.return_value = {"summary": None, "recent_messages": []}
    mock_memory.return_value = mock_memory_instance

    # Create a user first
    uid = db.create_user("pipelineuser", "pipeline@test.com", "hash")

    # Run
    result = run_orchestration("Reset my password", uid, db)

    assert "reply" in result
    assert "tasks" in result
    assert len(result["tasks"]) == 1
    assert result["tasks"][0]["assigned_agent"] == "support"
    assert result["tasks"][0]["status"] == "completed"
    assert result["conflicts"] == []


@patch("app.orchestrator.pipeline.get_conversation_memory")
@patch("app.orchestrator.pipeline.check_duplicate_intent")
def test_pipeline_duplicate_detection(mock_dup, mock_memory, db):
    mock_dup.return_value = {
        "is_duplicate": True,
        "existing_task_id": 42,
        "similarity_score": 0.92,
        "existing_text": "Reset password",
    }

    mock_memory_instance = MagicMock()
    mock_memory_instance.get_context.return_value = {"summary": None, "recent_messages": []}
    mock_memory.return_value = mock_memory_instance

    uid = db.create_user("dupuser", "dup@test.com", "hash")
    result = run_orchestration("Reset my password please", uid, db)

    assert "similar to an existing task" in result["reply"]
    assert len(result["conflicts"]) == 1
    assert result["conflicts"][0]["type"] == "duplicate_intent"
