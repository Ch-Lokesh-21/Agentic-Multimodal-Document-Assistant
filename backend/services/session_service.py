"""
Session service for managing RAG sessions.
"""

from typing import Optional

from crud import session_crud
from schemas import (
    SessionCreate,
    SessionInDB,
    SessionResponse,
    SessionUpdate,
    SessionListResponse,
)
from utils.object_id import PyObjectId


class SessionNotFoundError(Exception):
    """Raised when session is not found."""
    pass


class SessionAccessDeniedError(Exception):
    """Raised when user doesn't have access to session."""
    pass


class SessionService:
    """Service for session management operations."""

    @classmethod
    async def create_session(
        cls,
        user_id: PyObjectId,
        session_data: SessionCreate,
    ) -> SessionResponse:
        """Create a new session for user."""
        session = await session_crud.create(user_id, session_data)
        return SessionResponse.from_db(session)

    @classmethod
    async def get_session(
        cls,
        session_id: str,
        user_id: PyObjectId,
    ) -> SessionResponse:
        """Get session by ID with ownership validation."""
        session = await session_crud.get_by_session_id_and_user(session_id, user_id)

        if session is None:
            raise SessionNotFoundError(f"Session '{session_id}' not found")

        return SessionResponse.from_db(session)

    @classmethod
    async def get_session_internal(
        cls,
        session_id: str,
        user_id: PyObjectId,
    ) -> SessionInDB:
        """Get session document for internal use."""
        session = await session_crud.get_by_session_id_and_user(session_id, user_id)

        if session is None:
            raise SessionNotFoundError(f"Session '{session_id}' not found")

        return session

    @classmethod
    async def list_sessions(
        cls,
        user_id: PyObjectId,
        skip: int = 0,
        limit: int = 100,
    ) -> SessionListResponse:
        """List all sessions for user."""
        sessions = await session_crud.get_all_by_user(user_id, skip=skip, limit=limit, active_only=True)
        total = await session_crud.count_by_user(user_id, active_only=True)

        return SessionListResponse(
            sessions=[SessionResponse.from_db(s) for s in sessions],
            total=total,
        )

    @classmethod
    async def update_session(
        cls,
        session_id: str,
        user_id: PyObjectId,
        update_data: SessionUpdate,
    ) -> SessionResponse:
        """Update session."""
        session = await session_crud.update(session_id, user_id, update_data)

        if session is None:
            raise SessionNotFoundError(f"Session '{session_id}' not found")

        return SessionResponse.from_db(session)

    @classmethod
    async def delete_session(
        cls,
        session_id: str,
        user_id: PyObjectId,
    ) -> bool:
        """Delete session (soft delete)."""
        deleted = await session_crud.delete(session_id, user_id)

        if not deleted:
            raise SessionNotFoundError(f"Session '{session_id}' not found")

        return True

    @classmethod
    async def validate_session_access(
        cls,
        session_id: str,
        user_id: PyObjectId,
    ) -> SessionInDB:
        """Validate user has access to session."""
        session = await session_crud.get_by_session_id(session_id)

        if session is None:
            raise SessionNotFoundError(f"Session '{session_id}' not found")

        if str(session.user_id) != str(user_id):
            raise SessionAccessDeniedError("Access denied to this session")

        return session

    @classmethod
    async def update_activity(cls, session_id: str) -> None:
        """Update session last activity timestamp."""
        await session_crud.update_activity(session_id)

    @classmethod
    async def increment_documents(cls, session_id: str, delta: int = 1) -> None:
        """Increment document count for session."""
        await session_crud.increment_document_count(session_id, delta)

    @classmethod
    async def get_session_messages(
        cls,
        session_id: str,
        user_id: PyObjectId,
    ) -> list:
        """
        Get conversation messages for a session from session_messages collection.

        Retrieves the conversation history stored for frontend display.
        """
        from crud import session_message_crud
        from schemas import SessionMessageResponse
        import logging

        logger = logging.getLogger(__name__)

        session = await cls.validate_session_access(session_id, user_id)

        try:
            messages = await session_message_crud.get_by_session_id(
                session_id=session_id,
                user_id=user_id,
            )

            formatted_messages = [
                SessionMessageResponse.from_db(msg).model_dump()
                for msg in messages
            ]

            logger.info(
                f"Retrieved {len(formatted_messages)} messages for session {session_id}")
            return formatted_messages

        except Exception as e:
            logger.error(
                f"Failed to retrieve messages for session {session_id}: {str(e)}", exc_info=True)
            return []


session_service = SessionService()
