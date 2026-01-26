"""
Query analyzer agent for complex query decomposition.

This module contains the agent responsible for analyzing
and classifying user queries.
"""

import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from config import settings
from rag_system.prompts import QUERY_ANALYZER_PROMPT
from schemas import (
    GraphState,
    QueryAnalysisResult,
    AnswerWithCitations,
)

logger = logging.getLogger(__name__)


class QueryAnalyzerAgent:
    """
    Agent responsible for analyzing and classifying user queries.
    
    Determines if a query is simple (single intent) or complex
    (multiple sub-questions, comparisons, or multi-part queries).
    """
    
    def __init__(self, model: Optional[str] = None, session_id: Optional[str] = None):
        """Initialize query analyzer agent."""
        self.model = model or settings.llm.model
        self.session_id = session_id
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=settings.llm.temperature,
        )
        self.max_sub_queries = settings.query_analyzer.max_sub_queries
    
    @traceable(name="query_analyzer_node", metadata={"step": "query_analysis"})
    async def analyze_query(self, state: GraphState) -> dict:
        """Analyze the user query and classify as simple or complex."""
        query = state.get("query", "")
        
        logger.info(f"[QUERY_ANALYZER] Analyzing query: {query}")
        
        try:
            # Use structured output for query analysis
            structured_llm = self.llm.with_structured_output(QueryAnalysisResult)
            prompt = ChatPromptTemplate.from_template(QUERY_ANALYZER_PROMPT)
            chain = prompt | structured_llm
            
            analysis: QueryAnalysisResult = await chain.ainvoke({
                "query": query,
                "max_sub_queries": self.max_sub_queries,
            })
            
            # Enforce max sub-queries limit
            if len(analysis.sub_queries) > self.max_sub_queries:
                logger.warning(
                    f"[QUERY_ANALYZER] Too many sub-queries detected: {len(analysis.sub_queries)}, "
                    f"max allowed: {self.max_sub_queries}"
                )
                # Return error state for too complex queries
                error_answer = AnswerWithCitations(
                    answer="The query is too complex for the current implementation. Please simplify.",
                    citations=[],
                    uncertainty=1.0,
                    answer_type="unable_to_answer",
                )
                return {
                    "query_analysis": analysis,
                    "final_answer": error_answer,
                    "error_message": f"Query too complex: {len(analysis.sub_queries)} sub-queries detected, max {self.max_sub_queries} allowed",
                }
            
            logger.info(
                f"[QUERY_ANALYZER] Classification: {analysis.classification} "
                f"(confidence: {analysis.confidence:.2f})"
            )
            
            if analysis.classification == "complex":
                logger.info(f"[QUERY_ANALYZER] Sub-queries: {analysis.sub_queries}")
            
            return {
                "query_analysis": analysis,
                "current_sub_query_index": 0,
                "sub_query_results": [],
                "intermediate_reasoning": state.get("intermediate_reasoning", "") + 
                    f"\n[QUERY_ANALYSIS] {analysis.reasoning}",
            }
            
        except Exception as e:
            logger.error(f"[QUERY_ANALYZER] Error: {str(e)}")
            # On error, default to simple query processing
            fallback_analysis = QueryAnalysisResult(
                classification="simple",
                reasoning=f"Analysis failed, defaulting to simple: {str(e)}",
                sub_queries=[],
                is_comparison=False,
                confidence=0.5,
            )
            return {
                "query_analysis": fallback_analysis,
                "current_sub_query_index": 0,
                "sub_query_results": [],
            }
