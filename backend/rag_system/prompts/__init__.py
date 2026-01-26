"""Prompt templates for the RAG system."""

from rag_system.prompts.routing import ROUTING_PROMPT
from rag_system.prompts.rag import (
    RAG_ANSWER_PROMPT,
    WEB_SEARCH_PROMPT,
    GENERAL_KNOWLEDGE_PROMPT,
    build_multimodal_prompt,
)
from rag_system.prompts.visual import (
    VISUAL_DECISION_PROMPT,
    PAGE_SELECTION_PROMPT,
)
from rag_system.prompts.query_analyzer import (
    QUERY_ANALYZER_PROMPT,
    SYNTHESIZE_ANSWERS_PROMPT,
)

__all__ = [
    "ROUTING_PROMPT",
    "RAG_ANSWER_PROMPT",
    "WEB_SEARCH_PROMPT",
    "GENERAL_KNOWLEDGE_PROMPT",
    "VISUAL_DECISION_PROMPT",
    "PAGE_SELECTION_PROMPT",
    "QUERY_ANALYZER_PROMPT",
    "SYNTHESIZE_ANSWERS_PROMPT",
    "build_multimodal_prompt",
]
