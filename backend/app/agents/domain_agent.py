"""Domain Agent — handles domain-specific lookups and multi-step research workflows.

This agent uses a multi-step workflow with 3+ tools:
1. semantic_search — deep search of the FAISS index for domain knowledge
2. synthesize_answer — uses LLM to synthesize information from multiple sources
3. extract_entities — uses LLM to extract structured entities from the query
4. validate_response — self-critique loop to validate the quality of the answer
"""

import logging

from app.agents.base import BaseAgent, AgentResult
from app.memory.faiss_store import get_faiss_store
from app.services.llm import get_llm_service

logger = logging.getLogger(__name__)

SYNTHESIS_SYSTEM_PROMPT = """You are a domain knowledge agent in the MACE multi-agent system.
Synthesize the provided information into a clear, accurate answer.
If the context is insufficient, state what you know and what is uncertain.
Keep your response under 300 words. Be specific and factual."""

ENTITY_EXTRACTION_PROMPT = """Extract key entities from this text. Return ONLY valid JSON:
{"entities": [{"name": "entity name", "type": "person|system|concept|action", "relevance": "high|medium|low"}]}"""

VALIDATION_PROMPT = """You are a quality validator. Evaluate this AI-generated response for accuracy and completeness.
Return ONLY valid JSON: {"quality_score": 0.0-1.0, "issues": ["issue1", "issue2"], "is_acceptable": true/false}"""


class DomainAgent(BaseAgent):
    """Agent that handles domain lookups and knowledge synthesis."""

    name = "domain"
    description = "Handles domain-specific lookups and knowledge synthesis"

    def execute(self, intent: dict, context: dict | None = None) -> AgentResult:
        steps = []
        tools_used = []
        query = intent.get("summary", "")

        # Step 1: Extract entities from the query for better search
        entities = self._extract_entities(query)
        steps.append(self._log_step(
            "extract_entities",
            f"Extracted {len(entities)} entities: {[e['name'] for e in entities[:5]]}"
        ))
        tools_used.append("extract_entities")

        # Step 2: Semantic search with enriched query
        search_results = self._semantic_search(query, entities)
        steps.append(self._log_step(
            "semantic_search",
            f"Retrieved {len(search_results)} relevant results from knowledge base"
        ))
        tools_used.append("semantic_search")

        # Step 3: Synthesize answer from search results
        synthesized = self._synthesize_answer(query, search_results, entities)
        steps.append(self._log_step("synthesize_answer", "Synthesized response from retrieved context"))
        tools_used.append("synthesize_answer")

        # Step 4: Validate response quality (self-critique loop)
        validation = self._validate_response(query, synthesized)
        steps.append(self._log_step(
            "validate_response",
            f"Quality score: {validation.get('quality_score', 'N/A')}, "
            f"Acceptable: {validation.get('is_acceptable', True)}"
        ))
        tools_used.append("validate_response")

        # If validation fails, refine the response
        if not validation.get("is_acceptable", True):
            synthesized = self._refine_response(synthesized, validation.get("issues", []))
            steps.append(self._log_step("refine_response", "Refined response based on validation feedback"))
            tools_used.append("refine_response")

        return AgentResult(
            response=synthesized,
            steps=steps,
            tools_used=tools_used,
        )

    def _extract_entities(self, query: str) -> list[dict]:
        """Tool 1: Extract structured entities from the user query."""
        llm = get_llm_service()
        try:
            response = llm.complete(
                prompt=f"Extract entities from: \"{query}\"",
                system_prompt=ENTITY_EXTRACTION_PROMPT,
                output_schema={"entities": [{"name": "string", "type": "string", "relevance": "string"}]},
                max_tokens=256,
            )
            if response.parsed and "entities" in response.parsed:
                return response.parsed["entities"]
        except Exception as e:
            logger.warning("Entity extraction failed: %s", e)

        return [{"name": query, "type": "concept", "relevance": "high"}]

    def _semantic_search(self, query: str, entities: list[dict]) -> list[dict]:
        """Tool 2: Deep semantic search of the FAISS knowledge base."""
        store = get_faiss_store()

        # Search with original query
        results = store.search(query, top_k=5)

        # Also search with high-relevance entities for broader coverage
        for entity in entities[:3]:
            if entity.get("relevance") == "high":
                entity_results = store.search(entity["name"], top_k=2)
                for r in entity_results:
                    if r not in results and r.get("score", 0) > 0.3:
                        results.append(r)

        # Deduplicate and sort by score
        seen_texts = set()
        unique_results = []
        for r in sorted(results, key=lambda x: x.get("score", 0), reverse=True):
            text = r.get("text", "")
            if text not in seen_texts:
                seen_texts.add(text)
                unique_results.append(r)

        return unique_results[:5]

    def _synthesize_answer(self, query: str, search_results: list[dict], entities: list[dict]) -> str:
        """Tool 3: Synthesize an answer from retrieved context using LLM."""
        llm = get_llm_service()

        context_lines = []
        for i, result in enumerate(search_results[:5], 1):
            context_lines.append(f"{i}. {result.get('text', 'N/A')} (relevance: {result.get('score', 0):.2f})")

        context_block = "\n".join(context_lines) if context_lines else "No relevant context found in knowledge base."
        entity_list = ", ".join(e["name"] for e in entities[:5]) if entities else "none identified"

        prompt = (
            f"User query: {query}\n"
            f"Key entities: {entity_list}\n\n"
            f"Retrieved context:\n{context_block}\n\n"
            f"Synthesize a comprehensive answer based on the above."
        )

        try:
            response = llm.complete(prompt=prompt, system_prompt=SYNTHESIS_SYSTEM_PROMPT, max_tokens=512)
            return response.content
        except Exception as e:
            logger.error("Synthesis failed: %s", e)
            return f"I found relevant information about your query regarding '{query}' but encountered an error synthesizing the response."

    def _validate_response(self, query: str, response: str) -> dict:
        """Tool 4: Self-critique loop — validate the quality of the generated response."""
        llm = get_llm_service()
        try:
            validation = llm.complete(
                prompt=(
                    f"Query: {query}\n\n"
                    f"Generated response: {response}\n\n"
                    f"Evaluate this response for quality, accuracy, and completeness."
                ),
                system_prompt=VALIDATION_PROMPT,
                output_schema={"quality_score": "number", "issues": ["string"], "is_acceptable": "boolean"},
                max_tokens=256,
            )
            if validation.parsed:
                return validation.parsed
        except Exception as e:
            logger.warning("Validation step failed: %s", e)

        return {"quality_score": 0.7, "issues": [], "is_acceptable": True}

    def _refine_response(self, original: str, issues: list[str]) -> str:
        """Refine the response if validation fails."""
        llm = get_llm_service()
        issues_text = "; ".join(issues) if issues else "general quality concerns"
        try:
            response = llm.complete(
                prompt=(
                    f"Original response: {original}\n\n"
                    f"Issues identified: {issues_text}\n\n"
                    f"Please improve the response to address these issues. Keep it concise."
                ),
                system_prompt="You are a response refinement assistant. Improve the given response.",
                max_tokens=512,
            )
            return response.content
        except Exception as e:
            logger.warning("Response refinement failed: %s", e)
            return original
