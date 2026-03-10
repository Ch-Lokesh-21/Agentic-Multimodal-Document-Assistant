"""RAG answer generation agent."""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from config import settings
from rag_system.core.base_agent import BaseAgent
from rag_system.prompts import RAG_ANSWER_PROMPT
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
    """Agent responsible for generating answers from RAG context."""
    
    @traceable(name="generate_rag_answer_node", metadata={"step": "rag_answer_generation"})
    async def generate_answer(self, state: GraphState) -> dict:
        """
        Generate answer from RAG context asynchronously.
        
        Visual content (images, tables) are now pre-processed during ingestion
        and stored as text descriptions in the vector DB, so no vision model
        is needed at query time.
        """
        query = state.get("query", "")
        retrieved_context: RetrievedContext | None = state.get("retrieved_context")
        messages = list(state.get("messages", []))
        
        logger.info("[ANSWER] Generating RAG-based answer...")
        
        if not retrieved_context:
            logger.warning("[ANSWER] No retrieved context")
            return {}
        
        try:
            trimmed_messages = get_trimmed_messages(messages)
            history_context = format_history_for_prompt(trimmed_messages)
            
            # Build context with content type markers
            context_text = self._build_context_with_sources(retrieved_context)
            
            # Count content types for logging
            content_types = self._count_content_types(retrieved_context)
            logger.info(
                f"[ANSWER] Context includes: {content_types['text']} text chunks, "
                f"{content_types['image']} image descriptions, "
                f"{content_types['table']} table descriptions"
            )
            
            # Generate answer using text-only LLM (visual content is already text descriptions)
            prompt = ChatPromptTemplate.from_template(RAG_ANSWER_PROMPT)
            chain = prompt | self.llm
            
            response = await chain.ainvoke({
                "question": query,
                "context": context_text,
                "visual_context_text": "",
                "history_context": history_context,
            })
            
            citations = self._build_citations(retrieved_context)
            
            # Lower uncertainty when we have visual content descriptions
            has_visual_content = content_types['image'] > 0 or content_types['table'] > 0
            uncertainty = 0.15 if has_visual_content else 0.2
            
            answer = AnswerWithCitations(
                answer=response.content,
                citations=citations,
                uncertainty=uncertainty,
                answer_type="synthesized",
            )
            
            logger.info(f"[ANSWER] Generated answer with {len(citations)} citations")
            
            return {"final_answer": answer}
            
        except Exception as e:
            logger.error(f"[ANSWER] Error: {str(e)}")
            return {"error_message": f"Answer generation failed: {str(e)}"}
    
    def _count_content_types(self, retrieved_context: RetrievedContext) -> dict:
        """Count chunks by content type."""
        counts = {"text": 0, "image": 0, "table": 0}
        for chunk in retrieved_context.chunks:
            content_type = chunk.content_type or "text"
            if content_type in counts:
                counts[content_type] += 1
            else:
                counts["text"] += 1
        return counts
    
    def _build_citations(self, retrieved_context: RetrievedContext) -> list[Citation]:
        """Build citations from retrieved context using chunk metadata."""
        citations = []
        seen_citations: set[tuple[str, int | None, str]] = set()
        
        max_citations = settings.rag.max_citations
        snippet_length = settings.rag.citation_snippet_length
        
        for chunk in retrieved_context.chunks[:max_citations]:
            content_type = chunk.content_type or "text"
            key = (chunk.source_file, chunk.page_number, content_type)
            
            if key not in seen_citations:
                seen_citations.add(key)
                
                # Include content type in snippet for visual citations
                snippet = chunk.content[:snippet_length] if chunk.content else ""
                if content_type in ("image", "table"):
                    snippet = f"[{content_type.upper()}] {snippet}"
                
                citations.append(Citation(
                    source_type="document",
                    source_id=chunk.source_file,
                    page_number=chunk.page_number,
                    snippet=snippet,
                    confidence=settings.rag.default_confidence,
                ))
        
        return citations
    
    def _build_context_with_sources(self, retrieved_context: RetrievedContext) -> str:
        """Build formatted context string with source metadata and content types for LLM."""
        context_parts = []
        for i, chunk in enumerate(retrieved_context.chunks, 1):
            source = chunk.source_file or "unknown"
            page = chunk.page_number or "?"
            content = chunk.content or ""
            content_type = chunk.content_type or "text"
            
            # Add content type marker for visual content
            type_marker = ""
            if content_type == "image":
                type_marker = "[IMAGE DESCRIPTION] "
            elif content_type == "table":
                type_marker = "[TABLE DESCRIPTION] "
            
            section = f"[Document {i}] (Source: {source}, Page {page}, Type: {content_type})\n{type_marker}{content}"
            context_parts.append(section)
        
        return "\n\n".join(context_parts)
