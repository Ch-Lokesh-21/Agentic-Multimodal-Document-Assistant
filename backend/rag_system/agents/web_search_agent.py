"""
Web search agent for external information retrieval.

This module contains the agent responsible for performing
web searches and generating answers from web results.
"""

import asyncio
import json
import logging
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from config import settings
from rag_system.core.base_agent import BaseAgent
from rag_system.prompts import WEB_SEARCH_PROMPT
from rag_system.utils.message_utils import (
    get_trimmed_messages,
    format_history_for_prompt,
)
from schemas import (
    GraphState,
    WebSearchResult,
    AnswerWithCitations,
    Citation,
)

logger = logging.getLogger(__name__)


class WebSearchAgent(BaseAgent):
    """
    Agent responsible for web search operations.
    
    Performs web searches using Tavily and processes results.
    """
    
    @traceable(name="web_search_node", metadata={"step": "web_search"})
    async def search(self, state: GraphState) -> dict:
        """
        Perform web search using Tavily asynchronously.
        
        Args:
            state: Current graph state
            
        Returns:
            State updates with web results
        """
        query = state.get("query", "")
        
        logger.info(f"[WEB] Searching web for: {query}")
        
        try:
            from langchain_tavily import TavilySearch
            
            tavily = TavilySearch(max_results=settings.tavily.max_results, topic="general")
            response = await asyncio.to_thread(tavily.invoke, {"query": query})
            
            # Parse response
            if isinstance(response, str):
                data = json.loads(response)
            else:
                data = response
            
            # Build web results with Pydantic validation
            web_results = []
            for result in data.get("results", []):
                web_results.append(WebSearchResult(
                    url=result.get("url", ""),
                    title=result.get("title", ""),
                    snippet=result.get("content", ""),
                    relevance_score=result.get("score", 0.8),
                ))
            
            logger.info(f"[WEB] Found {len(web_results)} results")
            return {"web_results": web_results}
            
        except Exception as e:
            logger.error(f"[WEB] Error: {str(e)}")
            return {
                "error_message": f"Web search failed: {str(e)}",
                "web_results": [],
            }
    
    @traceable(name="generate_web_answer_node", metadata={"step": "web_answer_generation"})
    async def generate_answer(self, state: GraphState) -> dict:
        """
        Generate answer from web results asynchronously.
        
        Args:
            state: Current graph state
            
        Returns:
            State updates with final answer
        """
        query = state.get("query", "")
        web_results: list[WebSearchResult] = state.get("web_results", [])
        messages = list(state.get("messages", []))
        
        logger.info("[ANSWER] Generating web-based answer...")
        
        if not web_results:
            logger.info("[ANSWER] No web results - falling back to LLM")
            return {"route": "llm"}
        
        try:
            # Get trimmed conversation history for context
            trimmed_messages = get_trimmed_messages(messages)
            history_context = format_history_for_prompt(trimmed_messages)
            
            # Format web results
            formatted_results = "\n\n".join([
                f"[{r.title}]\nURL: {r.url}\n{r.snippet}"
                for r in web_results
            ])
            
            prompt = ChatPromptTemplate.from_template(WEB_SEARCH_PROMPT)
            chain = prompt | self.llm
            
            response = await chain.ainvoke({
                "question": query,
                "web_results": formatted_results,
                "history_context": history_context,
            })
            
            # Build citations with Pydantic validation
            max_citations = settings.rag.max_citations
            snippet_length = settings.rag.citation_snippet_length
            
            citations = [
                Citation(
                    source_type="web",
                    source_id=r.title,
                    url=r.url,
                    snippet=r.snippet[:snippet_length],
                    confidence=r.relevance_score,
                )
                for r in web_results[:max_citations]
            ]
            
            answer = AnswerWithCitations(
                answer=response.content,
                citations=citations,
                uncertainty=0.3,
                answer_type="synthesized",
                required_fallback=True,
            )
            
            logger.info(f"[ANSWER] Generated web answer with {len(citations)} citations")
            
            return {"final_answer": answer}
            
        except Exception as e:
            logger.error(f"[ANSWER] Error: {str(e)}")
            return {"error_message": f"Web answer generation failed: {str(e)}"}
