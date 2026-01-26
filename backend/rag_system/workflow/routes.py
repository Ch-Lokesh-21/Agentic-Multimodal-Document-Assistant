"""
Routing functions for the RAG workflow graph.

This module provides conditional edge routing logic.
"""

import logging
from langsmith import traceable

from config import settings
from schemas import (
    GraphState,
    VisualDecision,
    AnswerWithCitations,
    QueryAnalysisResult,
)

logger = logging.getLogger(__name__)


@traceable(name="route_decision_function", metadata={"step": "routing_decision_fn"})
def route_decision(state: GraphState) -> str:
    """Determine which path to take based on routing decision."""
    return state.get("route") or "llm"


@traceable(name="visual_route_function", metadata={"step": "visual_routing_fn"})
def visual_route(state: GraphState) -> str:
    """Determine if we need to retrieve images."""
    visual_decision: VisualDecision | None = state.get("visual_decision")
    if visual_decision and visual_decision.requires_visual:
        return "retrieve_images"
    return "generate_rag_answer"


@traceable(name="quality_check_route_function", metadata={"step": "quality_check_routing_fn"})
def quality_check_route(state: GraphState) -> str:
    """Determine if RAG answer quality is sufficient."""
    final_answer: AnswerWithCitations | None = state.get("final_answer")
    
    if not final_answer:
        return "web_search"
    
    is_empty = not final_answer.answer or len(final_answer.answer.strip()) < 50
    has_high_uncertainty = final_answer.uncertainty > 0.6
    has_no_citations = len(final_answer.citations) == 0
    
    if is_empty or has_high_uncertainty or has_no_citations:
        return "web_search"
    
    return "format_response"


@traceable(name="query_analysis_route_function", metadata={"step": "query_analysis_routing_fn"})
def query_analysis_route(state: GraphState) -> str:
    """
    Determine the path based on query analysis result.
    
    Args:
        state: Current graph state
        
    Returns:
        Route name: "simple_rag", "complex_rag", or "too_complex"
    """
    query_analysis: QueryAnalysisResult | None = state.get("query_analysis")
    final_answer: AnswerWithCitations | None = state.get("final_answer")
    
    # If final_answer already set (too complex error), skip to format
    if final_answer and final_answer.answer_type == "unable_to_answer":
        return "too_complex"
    
    if not query_analysis:
        return "simple_rag"
    
    if query_analysis.classification == "simple":
        return "simple_rag"
    
    return "complex_rag"


@traceable(name="sub_query_loop_route_function", metadata={"step": "sub_query_loop_routing_fn"})
def sub_query_loop_route(state: GraphState) -> str:
    """
    Determine if more sub-queries need processing.
    
    Args:
        state: Current graph state
        
    Returns:
        Route name: "continue_loop" or "synthesize"
    """
    query_analysis: QueryAnalysisResult | None = state.get("query_analysis")
    current_index = state.get("current_sub_query_index", 0)
    
    if not query_analysis or not query_analysis.sub_queries:
        return "synthesize"
    
    if current_index < len(query_analysis.sub_queries):
        return "continue_loop"
    
    return "synthesize"


def quality_or_collect_route(state: GraphState) -> str:
    """
    Extended quality check route that handles sub-query collection.
    
    Args:
        state: Current graph state
        
    Returns:
        Route name: "web_search", "format_response", or "collect_sub_query"
    """
    query_analysis: QueryAnalysisResult | None = state.get("query_analysis")
    final_answer: AnswerWithCitations | None = state.get("final_answer")
    
    # Check if we're in complex query mode
    is_complex = (
        query_analysis is not None and 
        query_analysis.classification == "complex" and
        query_analysis.sub_queries
    )
    
    if not final_answer:
        logger.info("[CHECK] No RAG answer - will try web search")
        return "web_search"
    
    # Quality checks using config values
    is_empty = not final_answer.answer or len(final_answer.answer.strip()) < settings.rag.min_answer_length
    has_high_uncertainty = final_answer.uncertainty > settings.rag.quality_uncertainty_threshold
    has_no_citations = len(final_answer.citations) == 0
    
    if is_empty or has_high_uncertainty or has_no_citations:
        logger.info(f"[CHECK] RAG quality low - falling back to web search")
        return "web_search"
    
    # If complex query, collect the sub-query result
    if is_complex:
        current_index = state.get("current_sub_query_index", 0)
        if current_index < len(query_analysis.sub_queries):
            logger.info(f"[CHECK] RAG quality good - collecting sub-query result")
            return "collect_sub_query"
    
    logger.info(f"[CHECK] RAG quality good")
    return "format_response"


def web_answer_route(state: GraphState) -> str:
    """
    Route after web answer generation - handles complex query mode.
    
    Args:
        state: Current graph state
        
    Returns:
        Route name: "format_response" or "collect_sub_query"
    """
    query_analysis: QueryAnalysisResult | None = state.get("query_analysis")
    
    # Check if we're in complex query mode
    is_complex = (
        query_analysis is not None and 
        query_analysis.classification == "complex" and
        query_analysis.sub_queries
    )
    
    if is_complex:
        current_index = state.get("current_sub_query_index", 0)
        if current_index < len(query_analysis.sub_queries):
            logger.info(f"[WEB_ROUTE] Complex query mode - collecting web answer for sub-query")
            return "collect_sub_query"
    
    return "format_response"
