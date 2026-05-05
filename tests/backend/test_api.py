import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

# Add backend to path so `app` package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.main import app  # noqa: E402
from app.services.llm import LLMResponse  # noqa: E402

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_register_user():
    u = uuid.uuid4().hex[:8]
    resp = client.post("/api/auth/register", json={
        "username": f"testuser1_{u}",
        "email": f"test1_{u}@example.com",
        "password": "securepassword123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == f"testuser1_{u}"


def test_register_duplicate_username():
    client.post("/api/auth/register", json={
        "username": "dupeuser",
        "email": "dupe1@example.com",
        "password": "password123",
    })
    resp = client.post("/api/auth/register", json={
        "username": "dupeuser",
        "email": "dupe2@example.com",
        "password": "password123",
    })
    assert resp.status_code == 400


def test_login_success():
    client.post("/api/auth/register", json={
        "username": "loginuser",
        "email": "login@example.com",
        "password": "password123",
    })
    resp = client.post("/api/auth/login", data={
        "username": "loginuser",
        "password": "password123",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password():
    client.post("/api/auth/register", json={
        "username": "wrongpw",
        "email": "wrongpw@example.com",
        "password": "password123",
    })
    resp = client.post("/api/auth/login", data={
        "username": "wrongpw",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


def test_me_authenticated():
    client.post("/api/auth/register", json={
        "username": "meuser",
        "email": "me@example.com",
        "password": "password123",
    })
    login = client.post("/api/auth/login", data={
        "username": "meuser",
        "password": "password123",
    })
    token = login.json()["access_token"]
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "meuser"


def test_me_unauthenticated():
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_orchestrator_requires_auth():
    resp = client.post("/api/orchestrator/run", json={"message": "hello"})
    assert resp.status_code == 401


def test_tasks_requires_auth():
    resp = client.get("/api/orchestrator/tasks")
    assert resp.status_code == 401


def test_history_requires_auth():
    resp = client.get("/api/orchestrator/history")
    assert resp.status_code == 401


@patch("app.orchestrator.pipeline.get_agent")
@patch("app.orchestrator.pipeline.parse_intent")
@patch("app.orchestrator.pipeline.check_duplicate_intent")
def test_orchestrator_run_with_mock(mock_dup, mock_parse, mock_agent):
    """Test the orchestrator endpoint end-to-end with mocked LLM."""
    mock_dup.return_value = None
    mock_parse.return_value = {
        "parsed_intent": {
            "intent_type": "support_ticket",
            "summary": "Test task",
            "entities": [],
            "priority": "medium",
            "requires_agents": ["support"],
            "has_dependency": False,
        },
        "llm_usage": {"input_tokens": 10, "output_tokens": 20, "model": "test", "latency_ms": 50},
    }
    mock_agent_instance = MagicMock()
    mock_agent_instance.execute.return_value = MagicMock(
        response="Task handled successfully.",
        steps=[{"tool": "generate_response", "details": "done"}],
        tools_used=["knowledge_lookup", "generate_response"],
    )
    mock_agent.return_value = mock_agent_instance

    # Register and login
    u = uuid.uuid4().hex[:8]
    client.post("/api/auth/register", json={
        "username": f"orchuser_{u}",
        "email": f"orch_{u}@example.com",
        "password": "password123",
    })
    login = client.post("/api/auth/login", data={
        "username": f"orchuser_{u}",
        "password": "password123",
    })
    token = login.json()["access_token"]

    # Run orchestrator
    resp = client.post(
        "/api/orchestrator/run",
        json={"message": "Help me with my account"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert "tasks" in data
    assert len(data["tasks"]) >= 1


@patch("app.agents.support_agent.get_llm_service")
@patch("app.agents.support_agent.get_faiss_store")
@patch("app.orchestrator.intent.get_llm_service")
def test_orchestrator_with_auth(mock_intent_llm, mock_faiss, mock_agent_llm):
    # Mock intent parser LLM
    mock_llm = MagicMock()
    mock_intent_llm.return_value = mock_llm
    mock_llm.complete.return_value = LLMResponse(
        content="{}",
        parsed={
            "intent_type": "support_ticket",
            "summary": "Create a support ticket",
            "entities": [],
            "priority": "medium",
            "requires_agents": ["support"],
            "has_dependency": False,
        },
        input_tokens=10,
        output_tokens=20,
        model="gemini-2.5-flash-lite",
        latency_ms=50.0,
    )

    # Mock FAISS store for agent
    mock_faiss_instance = MagicMock()
    mock_faiss_instance.search.return_value = []
    mock_faiss.return_value = mock_faiss_instance

    # Mock agent LLM
    mock_agent_llm_instance = MagicMock()
    mock_agent_llm.return_value = mock_agent_llm_instance
    mock_agent_llm_instance.complete.return_value = LLMResponse(
        content="I can help you with that.",
        parsed={"priority": "medium", "reason": "standard request"},
        input_tokens=10,
        output_tokens=20,
        model="test-model",
        latency_ms=50.0,
    )

    client.post("/api/auth/register", json={
        "username": "orchuser",
        "email": "orch@example.com",
        "password": "password123",
    })
    login = client.post("/api/auth/login", data={
        "username": "orchuser",
        "password": "password123",
    })
    token = login.json()["access_token"]
    resp = client.post(
        "/api/orchestrator/run",
        json={"message": "Create a support ticket"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "reply" in resp.json()
