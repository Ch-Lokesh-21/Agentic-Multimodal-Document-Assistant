"""
Sub-query processor for complex query handling.

This module contains the agent responsible for preparing
sub-queries for RAG processing.
"""

import logging
from typing import Optional
from langsmith import traceable

from schemas import GraphState, QueryAnalysisResult

logger = logging.getLogger(__name__)


class SubQueryProcessorAgent:
    """
    Agent responsible for preparing sub-queries for RAG processing.
    
    Sets up the state for processing individual sub-queries
    through the existing RAG pipeline.
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """Initialize sub-query processor agent."""
        self.session_id = session_id
    
    @traceable(name="prepare_sub_query_node", metadata={"step": "sub_query_preparation"})
    async def prepare_sub_query(self, state: GraphState) -> dict:
        """Prepare the next sub-query for RAG processing."""
        
        query_analysis: QueryAnalysisResult | None = state.get("query_analysis")
        current_index = state.get("current_sub_query_index", 0)
        original_query = state.get("query", "")
        
        if not query_analysis or not query_analysis.sub_queries:
            logger.warning("[SUB_QUERY] No sub-queries available")
            return {}
        
        if current_index >= len(query_analysis.sub_queries):
            logger.info("[SUB_QUERY] All sub-queries processed")
            return {}
        
        current_sub_query = query_analysis.sub_queries[current_index]
        logger.info(
            f"[SUB_QUERY] Processing sub-query {current_index + 1}/{len(query_analysis.sub_queries)}: "
            f"{current_sub_query}"
        )
        
        return {
            "query": current_sub_query,
            # Clear previous retrieval state for fresh RAG run
            "retrieved_context": None,
            "visual_decision": None,
        }
