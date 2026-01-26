"""
Query schemas for RAG workflow requests and responses.
"""

import operator
from datetime import datetime
from typing import Annotated, Literal, Sequence, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import Field

from .base import BaseSchema


class QueryRequest(BaseSchema):
    """Request schema for RAG query endpoint."""

    query: str = Field(
        min_length=1,
        max_length=5000,
        description="User's question or query",
        examples=["What is the attention mechanism in transformers?"],
    )
    stream: bool = Field(
        default=False,
        description="Whether to stream the response",
    )
    include_sources: bool = Field(
        default=True,
        description="Whether to include source citations",
    )


class RoutingDecision(BaseSchema):
    """
    Structured output for the agentic router's decision.

    The router uses LLM reasoning to determine the best path.
    """

    route: Literal["llm", "web_search", "multimodal_rag"] = Field(
        description="Routing decision: 'llm', 'web_search', or 'multimodal_rag'",
    )
    reasoning: str = Field(
        description="Detailed reasoning for the routing decision",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1) for this decision",
    )
    fallback_route: Literal["llm", "web_search", "multimodal_rag"] | None = Field(
        default=None,
        description="Optional fallback route if primary fails",
    )


class VisualDecision(BaseSchema):
    """Decision on whether visual context (images) is needed."""

    requires_visual: bool = Field(
        description="Whether visual context (PDF page images) is needed",
    )
    reasoning: str = Field(
        description="Explanation for visual decision",
    )
    visual_type: Literal["full_page", "diagram", "table", "figure"] | None = Field(
        default=None,
        description="Type of visual content needed",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence that visual context is needed",
    )


class SourcePageSelection(BaseSchema):
    """Page selection from a specific source document."""

    source_file: str = Field(
        description="The source filename (e.g., 'document.pdf')",
    )
    pages: list[int] = Field(
        description="List of page numbers (1-indexed) to extract from this source",
        max_length=5,
    )


class PageSelectionDecision(BaseSchema):
    """
    LLM decision about which specific pages to convert to images.

    After visual context is deemed necessary, this schema captures
    the intelligent selection of relevant pages based on query and metadata.
    Supports multiple documents with per-document page selection.
    """

    selected_pages: list[SourcePageSelection] = Field(
        description="List of page selections per source document",
        max_length=5,
    )
    reasoning: str = Field(
        description="Explanation for why these specific pages were selected",
    )


class QueryAnalysisResult(BaseSchema):
    """Query classification (simple/complex) with extracted sub-queries."""

    classification: Literal["simple", "complex"] = Field(
        description="Query classification: 'simple' for single intent queries, 'complex' for multi-part/comparison queries",
    )
    reasoning: str = Field(
        description="Explanation for the classification decision",
    )
    sub_queries: list[str] = Field(
        default_factory=list,
        description="Extracted sub-queries if the query is complex (max 3)",
    )
    is_comparison: bool = Field(
        default=False,
        description="Whether the query asks for a comparison between things",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1) for this classification",
    )


class SubQueryResult(BaseSchema):
    """Result for a single sub-query in complex query processing."""

    sub_query: str = Field(
        description="The sub-query that was processed",
    )
    answer: str = Field(
        description="The answer to the sub-query",
    )
    citations: list["Citation"] = Field(
        default_factory=list,
        description="Citations for this sub-query answer",
    )


class Citation(BaseSchema):
    """Single citation source for answer."""

    source_type: Literal["document", "web", "llm_knowledge"] = Field(
        description="Type of source",
    )
    source_id: str = Field(
        description="Unique identifier (file name, URL, or 'general_knowledge')",
    )
    page_number: int | None = Field(
        default=None,
        description="Page number if document source",
    )
    url: str | None = Field(
        default=None,
        description="URL if web source",
    )
    snippet: str = Field(
        description="Supporting text snippet",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Relevance confidence score",
    )


class AnswerWithCitations(BaseSchema):
    """
    Final answer with proper citations.

    Terminal output of the RAG workflow.
    """

    answer: str = Field(
        description="The final answer to the user's query",
    )
    citations: list[Citation] = Field(
        default_factory=list,
        description="Supporting citations",
    )
    uncertainty: float = Field(
        ge=0.0,
        le=1.0,
        default=0.0,
        description="Answer confidence (0=not confident, 1=very confident)",
    )
    required_fallback: bool = Field(
        default=False,
        description="Whether a fallback route was used",
    )
    answer_type: Literal["direct", "synthesized", "partial", "unable_to_answer"] = Field(
        default="direct",
        description="Type of answer provided",
    )


class RetrievedChunk(BaseSchema):
    """Single retrieved document chunk with its metadata."""

    content: str = Field(
        description="Text content of the chunk",
    )
    page_number: int | None = Field(
        default=None,
        description="Page number this chunk came from (1-indexed)",
    )
    source_file: str = Field(
        default="unknown",
        description="Source file name",
    )
    category: str | None = Field(
        default=None,
        description="Document category/type from Unstructured",
    )


class RetrievedContext(BaseSchema):
    """Retrieved document context for RAG."""

    chunks: list[RetrievedChunk] = Field(
        default_factory=list,
        description="Retrieved document chunks with metadata",
    )
    unique_page_numbers: list[int] = Field(
        default_factory=list,
        description="Unique sorted page numbers from all retrieved chunks",
    )
    source_files: list[str] = Field(
        default_factory=list,
        description="Unique source file names",
    )
    images: list[str] = Field(
        default_factory=list,
        description="Base64-encoded images (if visual context retrieved)",
    )
    images_justification: str = Field(
        default="",
        description="Explanation for page selection",
    )

    @property
    def text_chunks(self) -> list[str]:
        """Backward compatibility: get text content from chunks."""
        return [chunk.content for chunk in self.chunks]

    @property
    def page_numbers(self) -> list[int]:
        """Backward compatibility: get page numbers per chunk (with None filtered)."""
        return [chunk.page_number for chunk in self.chunks if chunk.page_number is not None]


class WebSearchResult(BaseSchema):
    """Web search result from Tavily."""

    url: str = Field(description="Result URL")
    title: str = Field(description="Result title")
    snippet: str = Field(description="Text snippet")
    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Relevance score",
    )


class GraphState(TypedDict, total=False):
    """
    LangGraph state that tracks the entire workflow.
    """

    messages: Annotated[Sequence[AnyMessage], add_messages]

    query: str

    route: Literal["llm", "web_search", "multimodal_rag"] | None

    routing_decision: RoutingDecision | None

    query_analysis: QueryAnalysisResult | None

    current_sub_query_index: int

    sub_query_results: list[SubQueryResult]

    visual_decision: VisualDecision | None

    retrieved_context: RetrievedContext | None

    web_results: list[WebSearchResult]

    intermediate_reasoning: str

    final_answer: AnswerWithCitations | None

    error_message: str | None


class QueryResponse(BaseSchema):
    """RAG query response."""

    success: bool = Field(default=True)
    query: str = Field(description="Original query")
    answer: str = Field(description="Generated answer")
    citations: list[Citation] = Field(
        default_factory=list,
        description="Source citations",
    )
    routing: RoutingDecision | None = Field(
        default=None,
        description="Routing decision details",
    )
    visual_decision: VisualDecision | None = Field(
        default=None,
        description="Visual context decision",
    )
    processing_time_ms: float = Field(
        description="Processing time in milliseconds",
    )
    session_id: str = Field(
        description="Session ID for context",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "query": "What is the attention mechanism?",
                "answer": "The attention mechanism allows models to focus on relevant parts...",
                "citations": [
                    {
                        "source_type": "document",
                        "source_id": "attention_paper.pdf",
                        "page_number": 3,
                        "snippet": "Attention is computed as...",
                        "confidence": 0.95,
                    }
                ],
                "routing": {
                    "route": "multimodal_rag",
                    "reasoning": "Query references specific document content",
                    "confidence": 0.92,
                },
                "processing_time_ms": 1523.45,
                "session_id": "session_abc123def456",
            }
        }
    }


class StreamChunk(BaseSchema):
    """Single chunk in streaming response."""

    type: Literal["routing", "retrieval", "visual", "answer_chunk", "citation", "done", "error"] = Field(
        description="Chunk type",
    )
    content: str | dict = Field(
        description="Chunk content",
    )
    timestamp: datetime = Field(
        description="Chunk timestamp",
    )
