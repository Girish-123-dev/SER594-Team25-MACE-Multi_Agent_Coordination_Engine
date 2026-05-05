"""Base agent interface for MACE multi-agent system."""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AgentResult:
    """Result from an agent execution."""

    def __init__(self, response: str, steps: list[dict] | None = None, tools_used: list[str] | None = None):
        self.response = response
        self.steps = steps or []
        self.tools_used = tools_used or []

    def to_dict(self) -> dict:
        return {
            "response": self.response,
            "steps": self.steps,
            "tools_used": self.tools_used,
            "num_steps": len(self.steps),
        }


class BaseAgent(ABC):
    """Abstract base class for all MACE agents."""

    name: str = "base"
    description: str = "Base agent"

    @abstractmethod
    def execute(self, intent: dict, context: dict | None = None) -> AgentResult:
        """Execute the agent's workflow given a parsed intent."""
        ...

    def _log_step(self, step_name: str, details: str) -> dict:
        """Log and return a step record."""
        step = {"tool": step_name, "details": details}
        logger.info("[%s] Step: %s — %s", self.name, step_name, details)
        return step
