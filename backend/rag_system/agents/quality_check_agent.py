"""Quality check agent for RAG answer validation."""

import logging
from langsmith import traceable

from config import settings
from schemas import GraphState, AnswerWithCitations

logger = logging.getLogger(__name__)


class QualityCheckAgent:
    """Agent responsible for checking RAG answer quality."""
    
    @traceable(name="check_rag_quality_node", metadata={"step": "rag_quality_check"})
    def check_quality(self, state: GraphState) -> dict:
        """Check RAG answer quality."""
        final_answer: AnswerWithCitations | None = state.get("final_answer")
        
        if not final_answer:
            logger.info("[CHECK] No RAG answer - will try web search")
            return {}
        
        is_empty = not final_answer.answer or len(final_answer.answer.strip()) < settings.rag.min_answer_length
        has_high_uncertainty = final_answer.uncertainty > settings.rag.quality_uncertainty_threshold
        has_no_citations = len(final_answer.citations) == 0
        
        if is_empty or has_high_uncertainty or has_no_citations:
            logger.info(f"[CHECK] RAG quality low - falling back to web search")
            return {}
        
        logger.info(f"[CHECK] RAG quality good")
        return {}
