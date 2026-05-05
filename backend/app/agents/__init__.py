"""MACE Agent registry."""

from app.agents.support_agent import SupportAgent
from app.agents.domain_agent import DomainAgent
from app.agents.base import BaseAgent, AgentResult

_agents: dict[str, BaseAgent] = {
    "support": SupportAgent(),
    "domain": DomainAgent(),
}


def get_agent(name: str) -> BaseAgent:
    """Get an agent by name. Falls back to support agent."""
    return _agents.get(name, _agents["support"])


def list_agents() -> list[str]:
    """Return list of available agent names."""
    return list(_agents.keys())
