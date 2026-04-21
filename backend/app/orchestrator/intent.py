import logging

from app.services.llm import get_llm_service

logger = logging.getLogger(__name__)

INTENT_SYSTEM_PROMPT = """You are an intent parser for a multi-agent coordination system called MACE.
Given a user message, extract structured intent information.

You must respond with valid JSON only. No markdown, no extra text.

The JSON must have these fields:
- "intent_type": one of "support_ticket", "faq_query", "escalation", "domain_lookup", "general", "multi_step"
- "summary": a one-sentence summary of what the user wants
- "entities": a list of key entities mentioned (e.g., "password", "laptop", "VPN")
- "priority": one of "low", "medium", "high"
- "requires_agents": a list of agents needed, each being "support" or "domain"
- "has_dependency": boolean, true if the request implies sequential steps ("first do X, then Y")
"""

INTENT_SCHEMA = {
    "intent_type": "string",
    "summary": "string",
    "entities": ["string"],
    "priority": "string",
    "requires_agents": ["string"],
    "has_dependency": "boolean",
}


def parse_intent(user_message: str) -> dict:
    llm = get_llm_service()
    response = llm.complete(
        prompt=f'Parse the intent from this user message:\n\n"{user_message}"',
        system_prompt=INTENT_SYSTEM_PROMPT,
        output_schema=INTENT_SCHEMA,
        max_tokens=512,
    )

    if response.parsed:
        logger.info("Parsed intent: %s", response.parsed.get("intent_type"))
        return {
            "parsed_intent": response.parsed,
            "llm_usage": {
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "model": response.model,
                "latency_ms": response.latency_ms,
            },
        }

    logger.warning("Intent parsing returned non-JSON, using fallback")
    return {
        "parsed_intent": {
            "intent_type": "general",
            "summary": user_message[:200],
            "entities": [],
            "priority": "medium",
            "requires_agents": ["support"],
            "has_dependency": False,
        },
        "llm_usage": {
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "model": response.model,
            "latency_ms": response.latency_ms,
        },
    }
