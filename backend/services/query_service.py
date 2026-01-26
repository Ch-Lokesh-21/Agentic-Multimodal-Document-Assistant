"""
Query service for RAG workflow execution.
"""

import logging
import time
from typing import AsyncGenerator, Optional

from config import settings
from crud import session_crud, session_message_crud
from schemas import (
    QueryRequest,
    QueryResponse,
    GraphState,
    StreamChunk,
)
from services.session_service import session_service
from utils.object_id import PyObjectId
from rag_system import RAGWorkflow 

logger = logging.getLogger(__name__)


class QueryError(Exception):
    """Raised when query processing fails."""
    pass


class QueryService:
    """Service for RAG query execution."""

    @classmethod
    async def execute_query(
        cls,
        session_id: str,
        user_id: PyObjectId,
        query_request: QueryRequest,
    ) -> QueryResponse:
        """Execute RAG query against session."""
        start_time = time.time()

        session = await session_service.validate_session_access(session_id, user_id)

        await session_service.update_activity(session_id)

        try:
            graph = RAGWorkflow(
                session_id=session_id,
                collection_name=session_id,
            )

            result = await graph.ainvoke(query_request.query)

            processing_time = (time.time() - start_time) * 1000

            final_answer = result.get("final_answer")

            if final_answer is None:
                raise QueryError("No answer generated")

            try:
                await session_message_crud.create(
                    session_id=session_id,
                    user_id=user_id,
                    role="user",
                    content=query_request.query,
                )

                metadata = None
                if query_request.include_sources and final_answer.citations:
                    metadata = {
                        "citations": [
                            {
                                "source_type": c.source_type,
                                "source_id": c.source_id,
                                "page_number": c.page_number,
                                "url": c.url,
                                "confidence": c.confidence,
                                "snippet": c.snippet,
                            }
                            for c in final_answer.citations
                        ]
                    }

                await session_message_crud.create(
                    session_id=session_id,
                    user_id=user_id,
                    role="assistant",
                    content=final_answer.answer,
                    metadata=metadata,
                )
            except Exception as msg_err:
                logger.error(
                    f"Failed to save messages to session_messages: {str(msg_err)}")

            return QueryResponse(
                success=True,
                query=query_request.query,
                answer=final_answer.answer,
                citations=final_answer.citations if query_request.include_sources else [],
                routing=result.get("routing_decision"),
                visual_decision=result.get("visual_decision"),
                processing_time_ms=processing_time,
                session_id=session_id,
            )

        except Exception as e:
            logger.error(f"Query failed for session {session_id}: {str(e)}")
            raise QueryError(f"Query processing failed: {str(e)}")

    @classmethod
    async def stream_query(
        cls,
        session_id: str,
        user_id: PyObjectId,
        query_request: QueryRequest,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream RAG query execution.

        Args:
            session_id: Session identifier
            user_id: User ID for validation
            query_request: Query request data

        Yields:
            StreamChunk objects as processing progresses
        """
        from datetime import datetime, timezone

        session = await session_service.validate_session_access(session_id, user_id)

        await session_service.update_activity(session_id)

        try:
            await session_message_crud.create(
                session_id=session_id,
                user_id=user_id,
                role="user",
                content=query_request.query,
            )
        except Exception as msg_err:
            logger.error(
                f"Failed to save user message to session_messages: {str(msg_err)}")

        try:
            graph = RAGWorkflow(
                session_id=session_id,
                collection_name=session_id,
            )

            final_answer = None
            final_result = None
            intermediate_steps = []

            async for step in graph.astream(query_request.query):
                for node_name, node_data in step.items():
                    if node_data is None:
                        continue

                    if node_name == "route":
                        routing_decision = node_data.get(
                            "routing_decision") if isinstance(node_data, dict) else None
                        step_content = routing_decision.model_dump() if routing_decision else {}
                        intermediate_steps.append({
                            "type": "routing",
                            "content": step_content.get("decision", "Routing...")
                        })
                        yield StreamChunk(
                            type="routing",
                            content=step_content,
                            timestamp=datetime.now(timezone.utc),
                        )
                    elif node_name == "rag_retrieve":
                        retrieved_context = node_data.get(
                            "retrieved_context") if isinstance(node_data, dict) else None
                        doc_count = len(retrieved_context.chunks) if retrieved_context and hasattr(
                            retrieved_context, 'chunks') else 0
                        intermediate_steps.append({
                            "type": "retrieval",
                            "content": f"Retrieved {doc_count} documents"
                        })
                        yield StreamChunk(
                            type="retrieval",
                            content={"retrieved": bool(
                                retrieved_context), "count": doc_count},
                            timestamp=datetime.now(timezone.utc),
                        )
                    elif node_name == "visual_decide":
                        visual_decision = node_data.get(
                            "visual_decision") if isinstance(node_data, dict) else None
                        step_content = visual_decision.model_dump() if visual_decision else {}
                        intermediate_steps.append({
                            "type": "visual",
                            "content": step_content.get("decision", "Processing visuals...")
                        })
                        yield StreamChunk(
                            type="visual_decision",
                            content=step_content,
                            timestamp=datetime.now(timezone.utc),
                        )
                    elif "answer" in node_name.lower():
                        answer = node_data.get("final_answer") if isinstance(
                            node_data, dict) else None
                        if answer:
                            final_answer = answer
                            final_result = node_data
                            yield StreamChunk(
                                type="answer_chunk",
                                content={"chunk": final_answer.answer},
                                timestamp=datetime.now(timezone.utc),
                            )

                            if query_request.include_sources and final_answer.citations:
                                for citation in final_answer.citations:
                                    yield StreamChunk(
                                        type="citation",
                                        content={
                                            "source_type": citation.source_type,
                                            "source_id": citation.source_id,
                                            "page_number": citation.page_number,
                                            "url": citation.url,
                                            "confidence": citation.confidence,
                                            "snippet": citation.snippet,
                                        },
                                        timestamp=datetime.now(timezone.utc),
                                    )

            if final_answer:
                try:
                    metadata = {
                        "intermediate_steps": intermediate_steps
                    }
                    if query_request.include_sources and final_answer.citations:
                        metadata["citations"] = [
                            {
                                "source_type": c.source_type,
                                "source_id": c.source_id,
                                "page_number": c.page_number,
                                "url": c.url,
                                "confidence": c.confidence,
                                "snippet": c.snippet,
                            }
                            for c in final_answer.citations
                        ]

                    await session_message_crud.create(
                        session_id=session_id,
                        user_id=user_id,
                        role="assistant",
                        content=final_answer.answer,
                        metadata=metadata,
                    )
                except Exception as msg_err:
                    logger.error(
                        f"Failed to save assistant message to session_messages: {str(msg_err)}")

            yield StreamChunk(
                type="done",
                content={"session_id": session_id},
                timestamp=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.error(f"Stream query failed: {str(e)}")
            yield StreamChunk(
                type="error",
                content={"error": str(e)},
                timestamp=datetime.now(timezone.utc),
            )


query_service = QueryService()
