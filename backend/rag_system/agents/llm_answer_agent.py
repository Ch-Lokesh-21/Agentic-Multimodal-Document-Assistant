"""
LLM answer agent for general knowledge responses.

This module contains the agent responsible for generating
answers using direct LLM knowledge without retrieval.
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from rag_system.core.base_agent import BaseAgent
from rag_system.prompts import GENERAL_KNOWLEDGE_PROMPT
from rag_system.utils.message_utils import (
    get_trimmed_messages,
    format_history_for_prompt,
)
from schemas import (
    GraphState,
    AnswerWithCitations,
    Citation,
)

logger = logging.getLogger(__name__)


class LLMAnswerAgent(BaseAgent):
    """
    Agent responsible for generating answers using general LLM knowledge.
    
    Falls back to direct LLM knowledge when neither RAG nor web search
    is appropriate.
    """
    
    @traceable(name="generate_llm_answer_node", metadata={"step": "llm_answer_generation"})
    async def generate_answer(self, state: GraphState) -> dict:
        """
        Generate answer using general LLM knowledge asynchronously.
        
        Args:
            state: Current graph state
            
        Returns:
            State updates with final answer
        """
        query = state.get("query", "")
        messages = list(state.get("messages", []))
        
        logger.info("[ANSWER] Generating LLM-based answer...")
        
        try:
            # Get trimmed conversation history for context
            trimmed_messages = get_trimmed_messages(messages)
            history_context = format_history_for_prompt(trimmed_messages)
            
            prompt = ChatPromptTemplate.from_template(GENERAL_KNOWLEDGE_PROMPT)
            chain = prompt | self.llm
            
            response = await chain.ainvoke({"question": query, "history_context": history_context})
            
            answer = AnswerWithCitations(
                answer=response.content,
                citations=[
                    Citation(
                        source_type="llm_knowledge",
                        source_id="general_knowledge",
                        snippet="Generated from LLM's general knowledge",
                        confidence=0.7,
                    )
                ],
                uncertainty=0.4,
                answer_type="direct",
            )
            
            logger.info("[ANSWER] Generated LLM answer")
            
            return {"final_answer": answer}
            
        except Exception as e:
            logger.error(f"[ANSWER] Error: {str(e)}")
            return {"error_message": f"LLM answer generation failed: {str(e)}"}
