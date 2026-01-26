from fastapi import APIRouter, HTTPException, status

from middleware import CurrentUserDep
from schemas import (
    SessionCreate,
    SessionResponse,
    SessionUpdate,
    SessionListResponse,
    APIResponse,
    ErrorResponse,
)
from services import (
    SessionNotFoundError,
    session_service,
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Session created successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
    summary="Create a new session",
    description="Create a new RAG session for document upload and querying.",
)
async def create_session(
    session_data: SessionCreate,
    current_user: CurrentUserDep,
) -> SessionResponse:
    """
    Create a new session.

    - **name**: Display name for the session
    - **description**: Optional description of the session
    """
    return await session_service.create_session(current_user.id, session_data)


@router.get(
    "",
    response_model=SessionListResponse,
    responses={
        200: {"description": "Sessions retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
    summary="List all sessions",
    description="Get all sessions for the authenticated user.",
)
async def list_sessions(
    current_user: CurrentUserDep,
    skip: int = 0,
    limit: int = 100,
) -> SessionListResponse:
    """
    List all sessions for the current user.
    """
    return await session_service.list_sessions(
        current_user.id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    responses={
        200: {"description": "Session retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
    summary="Get session by ID",
    description="Get a specific session by its session_id.",
)
async def get_session(
    session_id: str,
    current_user: CurrentUserDep,
) -> SessionResponse:
    """
    Get session details.

    - **session_id**: Unique session identifier

    Only returns session if owned by the authenticated user.
    """
    try:
        return await session_service.get_session(session_id, current_user.id)
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.patch(
    "/{session_id}",
    response_model=SessionResponse,
    responses={
        200: {"description": "Session updated successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
    summary="Update session",
    description="Update session name or description.",
)
async def update_session(
    session_id: str,
    update_data: SessionUpdate,
    current_user: CurrentUserDep,
) -> SessionResponse:
    """
    Update session details.

    - **session_id**: Session to update
    - **name**: New session name (optional)
    - **description**: New description (optional)
    """
    try:
        return await session_service.update_session(
            session_id,
            current_user.id,
            update_data,
        )
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/{session_id}",
    response_model=APIResponse,
    responses={
        200: {"description": "Session deleted successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
    summary="Delete session",
    description="Soft delete a session (marks as inactive).",
)
async def delete_session(
    session_id: str,
    current_user: CurrentUserDep,
) -> APIResponse:
    """
    Delete a session.

    - **session_id**: Session to delete

    This is a soft delete - the session is marked inactive but data is retained.
    """
    try:
        await session_service.delete_session(session_id, current_user.id)
        return APIResponse(
            success=True,
            message=f"Session '{session_id}' deleted successfully",
        )
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/{session_id}/messages",
    responses={
        200: {"description": "Session messages retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
    summary="Get session messages",
    description="Get conversation history for a session. Returns user queries and assistant responses in chronological order.",
)
async def get_session_messages(
    session_id: str,
    current_user: CurrentUserDep,
):
    """
    Get session conversation history.

    - **session_id**: Session identifier

    Returns messages stored in the session_messages collection.
    Each message includes the role (user/assistant), content, timestamp, and optional metadata (citations).
    """
    try:
        messages = await session_service.get_session_messages(session_id, current_user.id)
        return {
            "success": True,
            "session_id": session_id,
            "messages": messages,
            "total": len(messages),
        }
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
