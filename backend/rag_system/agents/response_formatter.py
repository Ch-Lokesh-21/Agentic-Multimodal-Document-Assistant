"""
Response formatting agent for output cleanup.

This module contains the agent responsible for formatting
final responses and cleaning up transient state.
"""

import logging
from langchain_core.messages import AIMessage
from langsmith import traceable

from rag_system.utils.state_utils import estimate_state_size
from schemas import GraphState, AnswerWithCitations

logger = logging.getLogger(__name__)


class ResponseFormattingAgent:
    """Format final responses and cleanup transient state."""
    
    @traceable(name="format_response_node", metadata={"step": "response_formatting"})
    def format_response(self, state: GraphState) -> dict:
        """Format response, log state sizes, clear transient fields."""
        final_answer: AnswerWithCitations | None = state.get("final_answer")
        route = state.get("route", "unknown")
        
        state_size_before = estimate_state_size(dict(state))
        logger.info(f"[FORMAT] State size BEFORE cleanup: {state_size_before.get('_total_kb', 0)}KB")
        if state_size_before.get("_warnings"):
            for warning in state_size_before["_warnings"]:
                logger.warning(f"[FORMAT] {warning}")
        
        if not final_answer:
            final_answer = AnswerWithCitations(
                answer="I encountered an error. Please try again.",
                answer_type="unable_to_answer",
                citations=[],
                uncertainty=1.0,
            )
        
        citations_summary = [
            {"source": c.source_id, "page": c.page_number}
            for c in final_answer.citations[:5]
        ]
        
        ai_response = AIMessage(
            content=final_answer.answer,
            additional_kwargs={
                "route": route,
                "answer_type": final_answer.answer_type,
                "citations_count": len(final_answer.citations),
                "citations_summary": citations_summary,
                "uncertainty": final_answer.uncertainty,
            }
        )
        
        logger.info(f"[FORMAT] Response formatted, route={route}, type={final_answer.answer_type}")
        
        result = {
            "messages": [ai_response],
            "final_answer": final_answer,
            "retrieved_context": None,
            "sub_query_results": [],
            "web_results": [],
            "visual_decision": None,
            "query_analysis": None,
            "intermediate_reasoning": "",
            "current_sub_query_index": 0,
        }
        
        cleaned_state = {**dict(state), **result}
        state_size_after = estimate_state_size(cleaned_state)
        logger.info(f"[FORMAT] State size AFTER cleanup: {state_size_after.get('_total_kb', 0)}KB")
        logger.info(f"[FORMAT] Checkpoint size reduced by {state_size_before.get('_total_kb', 0) - state_size_after.get('_total_kb', 0):.2f}KB")
        
        return result
