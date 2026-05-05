"""Support Agent — handles support tickets, FAQ queries, and escalations.

This agent uses a multi-step workflow with 3+ tools:
1. knowledge_lookup — searches the FAISS vector store for similar resolved tickets
2. generate_response — uses LLM to generate a contextual support response
3. classify_priority — re-evaluates and confirms/overrides the priority
4. escalation_check — determines if human escalation is needed
"""

import logging

from app.agents.base import BaseAgent, AgentResult
from app.memory.faiss_store import get_faiss_store
from app.services.llm import get_llm_service

logger = logging.getLogger(__name__)

SUPPORT_SYSTEM_PROMPT = """You are a helpful support agent in the MACE multi-agent system.
Given context from similar past issues and the user's current request, provide a helpful response.
Be concise and actionable. If you cannot resolve the issue, say so clearly.

Respond with plain text (not JSON). Keep your response under 200 words."""

PRIORITY_SYSTEM_PROMPT = """You are a priority classifier. Given a support request, classify its priority.
Respond with ONLY valid JSON: {"priority": "low|medium|high", "reason": "brief reason"}
Consider: system outages and security issues are HIGH, feature requests are LOW, bugs are MEDIUM."""


class SupportAgent(BaseAgent):
    """Agent that handles support tickets through a multi-step workflow."""

    name = "support"
    description = "Handles support tickets, FAQ queries, and escalations"

    def execute(self, intent: dict, context: dict | None = None) -> AgentResult:
        steps = []
        tools_used = []

        # Step 1: Knowledge lookup — search for similar past issues
        similar_issues = self._knowledge_lookup(intent.get("summary", ""))
        steps.append(self._log_step("knowledge_lookup", f"Found {len(similar_issues)} similar past issues"))
        tools_used.append("knowledge_lookup")

        # Step 2: Classify/confirm priority
        priority_result = self._classify_priority(intent)
        steps.append(self._log_step(
            "classify_priority",
            f"Priority: {priority_result.get('priority', 'medium')} — {priority_result.get('reason', 'N/A')}"
        ))
        tools_used.append("classify_priority")

        # Step 3: Generate response using LLM with retrieved context
        response_text = self._generate_response(intent, similar_issues)
        steps.append(self._log_step("generate_response", "Generated support response using LLM"))
        tools_used.append("generate_response")

        # Step 4: Escalation check
        needs_escalation = self._escalation_check(intent, priority_result)
        steps.append(self._log_step(
            "escalation_check",
            f"Escalation needed: {needs_escalation}"
        ))
        tools_used.append("escalation_check")

        # Build final response
        final_response = response_text
        if needs_escalation:
            final_response += "\n\n⚠️ This issue has been flagged for human escalation."

        return AgentResult(
            response=final_response,
            steps=steps,
            tools_used=tools_used,
        )

    def _knowledge_lookup(self, query: str) -> list[dict]:
        """Tool 1: Search FAISS for similar past issues."""
        store = get_faiss_store()
        results = store.search(query, top_k=3)
        return [r for r in results if r.get("score", 0) > 0.3]

    def _classify_priority(self, intent: dict) -> dict:
        """Tool 2: Use LLM to classify/confirm priority."""
        llm = get_llm_service()
        summary = intent.get("summary", "")
        try:
            response = llm.complete(
                prompt=f"Classify the priority of this support request:\n\"{summary}\"",
                system_prompt=PRIORITY_SYSTEM_PROMPT,
                output_schema={"priority": "string", "reason": "string"},
                max_tokens=128,
            )
            if response.parsed:
                return response.parsed
        except Exception as e:
            logger.warning("Priority classification failed: %s", e)

        return {"priority": intent.get("priority", "medium"), "reason": "default classification"}

    def _generate_response(self, intent: dict, similar_issues: list[dict]) -> str:
        """Tool 3: Generate a support response using LLM with RAG context."""
        llm = get_llm_service()
        summary = intent.get("summary", "")
        entities = intent.get("entities", [])

        context_lines = []
        for issue in similar_issues[:3]:
            context_lines.append(f"- Similar issue: {issue.get('text', 'N/A')}")

        context_block = "\n".join(context_lines) if context_lines else "No similar past issues found."

        prompt = (
            f"User request: {summary}\n"
            f"Entities mentioned: {', '.join(entities) if entities else 'none'}\n\n"
            f"Similar past issues:\n{context_block}\n\n"
            f"Provide a helpful response to resolve this support request."
        )

        try:
            response = llm.complete(prompt=prompt, system_prompt=SUPPORT_SYSTEM_PROMPT, max_tokens=512)
            return response.content
        except Exception as e:
            logger.error("LLM response generation failed: %s", e)
            return f"I've logged your request regarding: {summary}. A team member will follow up shortly."

    def _escalation_check(self, intent: dict, priority: dict) -> bool:
        """Tool 4: Determine if issue needs human escalation."""
        if priority.get("priority") == "high":
            return True
        if intent.get("intent_type") == "escalation":
            return True
        high_priority_keywords = ["outage", "security", "breach", "down", "critical", "urgent"]
        summary = (intent.get("summary", "") + " ".join(intent.get("entities", []))).lower()
        return any(kw in summary for kw in high_priority_keywords)
