"""Tests for the agent system — SupportAgent and DomainAgent."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.agents.base import AgentResult  # noqa: E402
from app.agents.support_agent import SupportAgent  # noqa: E402
from app.agents.domain_agent import DomainAgent  # noqa: E402
from app.agents import get_agent, list_agents  # noqa: E402
from app.services.llm import LLMResponse  # noqa: E402


def _mock_llm_response(content: str, parsed: dict | None = None):
    return LLMResponse(
        content=content,
        parsed=parsed,
        input_tokens=10,
        output_tokens=20,
        model="test-model",
        latency_ms=100.0,
    )


def test_list_agents():
    agents = list_agents()
    assert "support" in agents
    assert "domain" in agents


def test_get_agent_support():
    agent = get_agent("support")
    assert agent.name == "support"


def test_get_agent_domain():
    agent = get_agent("domain")
    assert agent.name == "domain"


def test_get_agent_fallback():
    agent = get_agent("nonexistent")
    assert agent.name == "support"


@patch("app.agents.support_agent.get_llm_service")
@patch("app.agents.support_agent.get_faiss_store")
def test_support_agent_execute(mock_store, mock_llm_svc):
    # Mock FAISS store
    mock_store_instance = MagicMock()
    mock_store_instance.search.return_value = [
        {"text": "password reset ticket", "score": 0.8, "task_id": 1}
    ]
    mock_store.return_value = mock_store_instance

    # Mock LLM service
    mock_llm = MagicMock()
    mock_llm.complete.side_effect = [
        _mock_llm_response('{"priority": "medium", "reason": "standard request"}',
                           parsed={"priority": "medium", "reason": "standard request"}),
        _mock_llm_response("I can help you reset your password. Please go to settings."),
    ]
    mock_llm_svc.return_value = mock_llm

    agent = SupportAgent()
    result = agent.execute({
        "intent_type": "support_ticket",
        "summary": "I need to reset my password",
        "entities": ["password"],
        "priority": "medium",
    })

    assert isinstance(result, AgentResult)
    assert len(result.tools_used) >= 3
    assert "knowledge_lookup" in result.tools_used
    assert "generate_response" in result.tools_used
    assert "escalation_check" in result.tools_used


@patch("app.agents.domain_agent.get_llm_service")
@patch("app.agents.domain_agent.get_faiss_store")
def test_domain_agent_execute(mock_store, mock_llm_svc):
    # Mock FAISS store
    mock_store_instance = MagicMock()
    mock_store_instance.search.return_value = [
        {"text": "VPN configuration guide", "score": 0.75}
    ]
    mock_store.return_value = mock_store_instance

    # Mock LLM service
    mock_llm = MagicMock()
    mock_llm.complete.side_effect = [
        _mock_llm_response(
            '{"entities": [{"name": "VPN", "type": "system", "relevance": "high"}]}',
            parsed={"entities": [{"name": "VPN", "type": "system", "relevance": "high"}]},
        ),
        _mock_llm_response("Here is how to configure VPN access..."),
        _mock_llm_response(
            '{"quality_score": 0.85, "issues": [], "is_acceptable": true}',
            parsed={"quality_score": 0.85, "issues": [], "is_acceptable": True},
        ),
    ]
    mock_llm_svc.return_value = mock_llm

    agent = DomainAgent()
    result = agent.execute({
        "intent_type": "domain_lookup",
        "summary": "How do I configure VPN access?",
        "entities": ["VPN"],
        "priority": "medium",
    })

    assert isinstance(result, AgentResult)
    assert len(result.tools_used) >= 3
    assert "extract_entities" in result.tools_used
    assert "semantic_search" in result.tools_used
    assert "synthesize_answer" in result.tools_used
    assert "validate_response" in result.tools_used


def test_support_agent_escalation_check_high_priority():
    agent = SupportAgent()
    intent = {"intent_type": "escalation", "summary": "System is down", "entities": ["system"]}
    assert agent._escalation_check(intent, {"priority": "high"}) is True


def test_support_agent_no_escalation_low_priority():
    agent = SupportAgent()
    intent = {"intent_type": "faq_query", "summary": "How to change theme", "entities": ["theme"]}
    assert agent._escalation_check(intent, {"priority": "low"}) is False
