"""
Sub-query collector for aggregating results.

This module contains the agent responsible for collecting
sub-query results.
"""

import logging
from typing import Optional
from langsmith import traceable

from schemas import (
    GraphState,
    QueryAnalysisResult,
    SubQueryResult,
    AnswerWithCitations,
)

logger = logging.getLogger(__name__)


class SubQueryCollectorAgent:
    """
    Agent responsible for collecting sub-query results.
    
    Stores the answer from the current sub-query and prepares
    for the next iteration or synthesis.
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """Initialize sub-query collector agent."""
        self.session_id = session_id
    
    @traceable(name="collect_sub_query_result_node", metadata={"step": "sub_query_collection"})
    async def collect_result(self, state: GraphState) -> dict:
        """Collect result of current sub-query and move to next."""
        query_analysis: QueryAnalysisResult | None = state.get("query_analysis")
        current_index = state.get("current_sub_query_index", 0)
        sub_query_results: list[SubQueryResult] = state.get("sub_query_results", [])
        final_answer: AnswerWithCitations | None = state.get("final_answer")
        
        if not query_analysis or not query_analysis.sub_queries:
            return {}
        
        if current_index >= len(query_analysis.sub_queries):
            return {}
        
        current_sub_query = query_analysis.sub_queries[current_index]
        
        # Collect the answer for this sub-query
        answer_text = ""
        citations = []
        
        if final_answer:
            answer_text = final_answer.answer
            citations = final_answer.citations
        
        sub_result = SubQueryResult(
            sub_query=current_sub_query,
            answer=answer_text,
            citations=citations,
        )
        
        updated_results = sub_query_results + [sub_result]
        
        logger.info(
            f"[SUB_QUERY] Collected result for sub-query {current_index + 1}: "
            f"answer length={len(answer_text)}, citations={len(citations)}"
        )
        
        return {
            "sub_query_results": updated_results,
            "current_sub_query_index": current_index + 1,
            # Clear final_answer for next sub-query
            "final_answer": None,
        }
