"""
Answer synthesis agent for complex queries.

This module contains the agent responsible for synthesizing
final answers from multiple sub-query results.
"""

import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from config import settings
from rag_system.prompts import SYNTHESIZE_ANSWERS_PROMPT
from schemas import (
    GraphState,
    QueryAnalysisResult,
    SubQueryResult,
    AnswerWithCitations,
    Citation,
)

logger = logging.getLogger(__name__)


class AnswerSynthesisAgent:
    """
    Agent responsible for synthesizing final answer from sub-query results.
    
    Combines all sub-query answers into a coherent final response
    that addresses the original user query.
    """
    
    def __init__(self, model: Optional[str] = None, session_id: Optional[str] = None):
        """
        Initialize answer synthesis agent.
        
        Args:
            model: LLM model name
            session_id: Session ID for tracking
        """
        self.model = model or settings.llm.model
        self.session_id = session_id
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=settings.llm.temperature,
        )
    
    @traceable(name="synthesize_answers_node", metadata={"step": "answer_synthesis"})
    async def synthesize_answers(self, state: GraphState) -> dict:
        """
        Synthesize a final answer from all sub-query results.
        
        Args:
            state: Current graph state
            
        Returns:
            State updates with synthesized final answer
        """
        # Restore original query for synthesis
        query_analysis: QueryAnalysisResult | None = state.get("query_analysis")
        sub_query_results: list[SubQueryResult] = state.get("sub_query_results", [])
        
        # Get original query from state (should be preserved)
        # We need to access the original query before sub-query processing modified it
        # This is stored in the routing_decision or we use the first message
        messages = state.get("messages", [])
        original_query = ""
        
        # Find the original human message
        for msg in messages:
            if hasattr(msg, "content") and isinstance(msg.content, str):
                original_query = msg.content
                break
        
        if not original_query:
            original_query = state.get("query", "")
        
        logger.info(f"[SYNTHESIS] Synthesizing answer for: {original_query}")
        logger.info(f"[SYNTHESIS] Combining {len(sub_query_results)} sub-query results")
        
        if not sub_query_results:
            logger.warning("[SYNTHESIS] No sub-query results to synthesize")
            return {}
        
        try:
            # Format sub-query results for synthesis
            formatted_results = self._format_sub_query_results(sub_query_results)
            
            prompt = ChatPromptTemplate.from_template(SYNTHESIZE_ANSWERS_PROMPT)
            chain = prompt | self.llm
            
            response = await chain.ainvoke({
                "original_query": original_query,
                "sub_query_results": formatted_results,
            })
            
            # Combine all citations from sub-queries
            all_citations = self._combine_citations(sub_query_results)
            
            final_answer = AnswerWithCitations(
                answer=response.content,
                citations=all_citations,
                uncertainty=0.2,
                answer_type="synthesized",
            )
            
            logger.info(
                f"[SYNTHESIS] Synthesized answer with {len(all_citations)} total citations"
            )
            
            return {
                "query": original_query,  # Restore original query
                "final_answer": final_answer,
            }
            
        except Exception as e:
            logger.error(f"[SYNTHESIS] Error: {str(e)}")
            # Fallback: concatenate answers
            fallback_answer = self._create_fallback_answer(sub_query_results)
            return {
                "query": original_query,
                "final_answer": fallback_answer,
                "error_message": f"Synthesis failed, using fallback: {str(e)}",
            }
    
    def _format_sub_query_results(self, results: list[SubQueryResult]) -> str:
        """Format sub-query results for the synthesis prompt."""
        formatted_parts = []
        for i, result in enumerate(results, 1):
            part = f"Sub-Question {i}: {result.sub_query}\n"
            part += f"Answer: {result.answer}\n"
            if result.citations:
                citations_str = ", ".join(
                    f"[{c.source_id}, p.{c.page_number}]" if c.page_number else f"[{c.source_id}]"
                    for c in result.citations
                )
                part += f"Citations: {citations_str}\n"
            formatted_parts.append(part)
        return "\n---\n".join(formatted_parts)
    
    def _combine_citations(self, results: list[SubQueryResult]) -> list[Citation]:
        """Combine citations from all sub-queries, removing duplicates."""
        seen: set[tuple[str, int | None]] = set()
        combined = []
        max_citations = settings.rag.max_citations
        
        for result in results:
            for citation in result.citations:
                key = (citation.source_id, citation.page_number)
                if key not in seen and len(combined) < max_citations:
                    seen.add(key)
                    combined.append(citation)
        
        return combined
    
    def _create_fallback_answer(self, results: list[SubQueryResult]) -> AnswerWithCitations:
        """Create a fallback answer by concatenating sub-query answers."""
        answer_parts = []
        for i, result in enumerate(results, 1):
            answer_parts.append(f"**{result.sub_query}**\n{result.answer}")
        
        return AnswerWithCitations(
            answer="\n\n".join(answer_parts),
            citations=self._combine_citations(results),
            uncertainty=0.4,
            answer_type="synthesized",
        )
