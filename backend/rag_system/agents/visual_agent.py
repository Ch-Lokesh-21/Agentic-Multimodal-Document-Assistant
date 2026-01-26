"""
Visual decision agent for determining image context requirements.

This module contains the agent responsible for deciding if visual
context (PDF page images) would enhance the answer.
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from rag_system.core.base_agent import BaseAgent
from rag_system.prompts import VISUAL_DECISION_PROMPT
from rag_system.tools.visual_detection import detect_visual_elements
from schemas import GraphState, VisualDecision, RetrievedContext

logger = logging.getLogger(__name__)


class VisualDecisionAgent(BaseAgent):
    """
    Agent responsible for deciding if visual context is needed.
    
    Analyzes the query and retrieved context to determine if
    PDF page images would enhance the answer.
    """
    
    @traceable(name="visual_context_decision_node", metadata={"step": "visual_decision"})
    async def decide_visual_context(self, state: GraphState) -> dict:
        """
        Decide if visual context is needed asynchronously.
        
        Args:
            state: Current graph state
            
        Returns:
            State updates with visual decision
        """
        query = state.get("query", "")
        retrieved_context: RetrievedContext | None = state.get("retrieved_context")
        
        logger.info("[VISUAL] Deciding if visual context needed...")
        
        if not retrieved_context:
            decision = VisualDecision(
                requires_visual=False,
                reasoning="No retrieved context available",
                confidence=0.9,
            )
            return {"visual_decision": decision}
        
        # Quick check: does query explicitly ask for visual content?
        query_lower = query.lower()
        visual_query_keywords = [
            "figure", "diagram", "table", "chart", "graph", "image",
            "show me", "what does", "look like", "visualize", "illustration",
            "picture", "screenshot", "plot"
        ]
        query_asks_for_visual = any(kw in query_lower for kw in visual_query_keywords)
        
        # If query doesn't ask for visuals, skip visual retrieval
        if not query_asks_for_visual:
            decision = VisualDecision(
                requires_visual=False,
                reasoning="Query does not explicitly request visual content",
                confidence=0.95,
            )
            logger.info("[VISUAL] Skipping - query doesn't ask for visual content")
            return {"visual_decision": decision}
        
        # Check if text mentions visual elements
        visual_elements_mentioned = detect_visual_elements(retrieved_context.text_chunks)
        
        # Use structured output with Pydantic validation
        structured_llm = self.llm.with_structured_output(VisualDecision)
        prompt = ChatPromptTemplate.from_template(VISUAL_DECISION_PROMPT)
        chain = prompt | structured_llm
        
        decision: VisualDecision = await chain.ainvoke({
            "query": query,
            "total_pages": len(retrieved_context.page_numbers),
            "visual_elements_mentioned": visual_elements_mentioned,
        })
        
        logger.info(f"[VISUAL] Requires visual: {decision.requires_visual}")
        
        return {"visual_decision": decision}
