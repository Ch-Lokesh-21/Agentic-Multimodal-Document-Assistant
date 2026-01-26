import json
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from middleware import CurrentUserDep
from schemas import (
    QueryRequest,
    QueryResponse,
    ErrorResponse,
)
from services import (
    SessionNotFoundError,
    SessionAccessDeniedError,
    QueryError,
    query_service,
)

router = APIRouter(tags=["Query"])


@router.post(
    "/sessions/{session_id}/query",
    response_model=QueryResponse,
    responses={
        200: {"description": "Query processed successfully"},
        400: {"model": ErrorResponse, "description": "Query processing failed"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
    summary="Execute RAG query",
    description="Execute a RAG query against a session's documents.",
)
async def execute_query(
    session_id: str,
    query_request: QueryRequest,
    current_user: CurrentUserDep,
) -> QueryResponse:
    """
    Execute a RAG query.

    - **session_id**: Session to query
    - **query**: User's question
    - **stream**: Whether to stream the response (use /query/stream instead)
    - **include_sources**: Whether to include citations in response
    """
    if query_request.stream:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="For streaming responses, use POST /sessions/{session_id}/query/stream",
        )

    try:
        return await query_service.execute_query(
            session_id=session_id,
            user_id=current_user.id,
            query_request=query_request,
        )
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except SessionAccessDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except QueryError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/sessions/{session_id}/query/stream",
    responses={
        200: {
            "description": "Streaming query response",
            "content": {"text/event-stream": {}},
        },
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
    summary="Stream RAG query",
    description="Execute a RAG query with streaming response (Server-Sent Events).",
)
async def stream_query(
    session_id: str,
    query_request: QueryRequest,
    current_user: CurrentUserDep,
):
    """
    Execute a streaming RAG query.
    """
    async def generate() -> AsyncGenerator[str, None]:
        try:
            async for chunk in query_service.stream_query(
                session_id=session_id,
                user_id=current_user.id,
                query_request=query_request,
            ):
                data = chunk.model_dump_json()
                yield f"data: {data}\n\n"

        except SessionNotFoundError as e:
            error_data = json.dumps(
                {"type": "error", "content": {"error": str(e)}})
            yield f"data: {error_data}\n\n"
        except SessionAccessDeniedError as e:
            error_data = json.dumps(
                {"type": "error", "content": {"error": str(e)}})
            yield f"data: {error_data}\n\n"
        except Exception as e:
            error_data = json.dumps(
                {"type": "error", "content": {"error": str(e)}})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
