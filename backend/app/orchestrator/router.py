import logging

logger = logging.getLogger(__name__)


def route_task(parsed_intent: dict) -> str:
    agents = parsed_intent.get("requires_agents", [])
    intent_type = parsed_intent.get("intent_type", "general")

    if intent_type in ("support_ticket", "faq_query", "escalation"):
        return "support"
    if intent_type == "domain_lookup":
        return "domain"
    if intent_type == "multi_step" and len(agents) > 1:
        return "both"
    if "support" in agents:
        return "support"
    if "domain" in agents:
        return "domain"

    return "support"
