"""
RAG answer generation agent.

This module contains the agent responsible for generating answers
from retrieved context with optional vision-based processing.
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from config import settings
from rag_system.core.base_agent import BaseAgent
from rag_system.prompts import RAG_ANSWER_PROMPT
from rag_system.tools.multimodal_answer import generate_multimodal_answer
from rag_system.utils.message_utils import (
    get_trimmed_messages,
    format_history_for_prompt,
)
from schemas import (
    GraphState,
    RetrievedContext,
    AnswerWithCitations,
    Citation,
)

logger = logging.getLogger(__name__)


class RAGAnswerAgent(BaseAgent):
    """
    Agent responsible for generating answers from RAG context.
    
    Uses retrieved documents and optionally images to generate
    comprehensive answers with citations.
    """
    
    @traceable(name="generate_rag_answer_node", metadata={"step": "rag_answer_generation"})
    async def generate_answer(self, state: GraphState) -> dict:
        """
        Generate answer from RAG context asynchronously, optionally using vision for images.
        
        Args:
            state: Current graph state
            
        Returns:
            State updates with final answer
        """
        query = state.get("query", "")
        retrieved_context: RetrievedContext | None = state.get("retrieved_context")
        messages = list(state.get("messages", []))
        
        logger.info("[ANSWER] Generating RAG-based answer...")
        
        if not retrieved_context:
            logger.warning("[ANSWER] No retrieved context")
            return {}
        
        try:
            # Get trimmed conversation history for context
            trimmed_messages = get_trimmed_messages(messages)
            history_context = format_history_for_prompt(trimmed_messages)
            
            # Build context with source metadata for proper citations
            context_text = self._build_context_with_sources(retrieved_context)
            
            # Check if we have images for multimodal processing
            if retrieved_context.images and len(retrieved_context.images) > 0:
                logger.info(f"[ANSWER] Using vision model with {len(retrieved_context.images)} images")
                response = await generate_multimodal_answer(
                    query=query,
                    context_text=context_text,
                    images=retrieved_context.images,
                    images_justification=retrieved_context.images_justification,
                    history_context=history_context,
                )
            else:
                # Text-only RAG answer
                prompt = ChatPromptTemplate.from_template(RAG_ANSWER_PROMPT)
                chain = prompt | self.llm
                
                response = await chain.ainvoke({
                    "question": query,
                    "context": context_text,
                    "visual_context_text": "",
                    "history_context": history_context,
                })
            
            # Build citations with Pydantic validation
            citations = self._build_citations(retrieved_context)
            
            answer = AnswerWithCitations(
                answer=response.content,
                citations=citations,
                uncertainty=0.15 if retrieved_context.images else 0.2,
                answer_type="synthesized",
            )
            
            logger.info(f"[ANSWER] Generated answer with {len(citations)} citations")
            
            return {"final_answer": answer}
            
        except Exception as e:
            logger.error(f"[ANSWER] Error: {str(e)}")
            return {"error_message": f"Answer generation failed: {str(e)}"}
    
    def _build_citations(self, retrieved_context: RetrievedContext) -> list[Citation]:
        """Build citations from retrieved context using chunk metadata."""
        citations = []
        seen_citations: set[tuple[str, int | None]] = set()  # (source, page) dedup
        
        max_citations = settings.rag.max_citations
        snippet_length = settings.rag.citation_snippet_length
        
        for chunk in retrieved_context.chunks[:max_citations]:
            key = (chunk.source_file, chunk.page_number)
            if key not in seen_citations:
                seen_citations.add(key)
                citations.append(Citation(
                    source_type="document",
                    source_id=chunk.source_file,
                    page_number=chunk.page_number,
                    snippet=chunk.content[:snippet_length] if chunk.content else "",
                    confidence=settings.rag.default_confidence,
                ))
        
        return citations
    
    def _build_context_with_sources(self, retrieved_context: RetrievedContext) -> str:
        """
        Build formatted context string with source metadata for LLM citations.
        
        Args:
            retrieved_context: Retrieved context with chunks
            
        Returns:
            Formatted context string with source info per chunk
        """
        context_parts = []
        for i, chunk in enumerate(retrieved_context.chunks, 1):
            source = chunk.source_file or "unknown"
            page = chunk.page_number or "?"
            content = chunk.content or ""
            
            section = f"[Document {i}] (Source: {source}, Page {page})\n{content}"
            context_parts.append(section)
        
        return "\n\n".join(context_parts)
