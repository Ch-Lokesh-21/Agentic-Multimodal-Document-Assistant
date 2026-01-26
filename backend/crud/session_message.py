from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from db.mongo import get_session_messages_collection
from schemas import SessionMessageInDB
from utils.object_id import PyObjectId


class SessionMessageCRUD:
    """CRUD operations for SessionMessage documents."""

    @staticmethod
    def _get_collection() -> AsyncIOMotorCollection:
        """Get session messages collection."""
        return get_session_messages_collection()

    @classmethod
    async def create(
        cls,
        session_id: str,
        user_id: PyObjectId,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> SessionMessageInDB:
        """
        Create a new session message.

        Args:
            session_id: Session identifier
            user_id: User ID who owns the session
            role: Message role (user or assistant)
            content: Message content
            metadata: Optional metadata (citations, sources, etc.)

        Returns:
            Created message document
        """

        collection = cls._get_collection()

        message = SessionMessageInDB(
            session_id=session_id,
            user_id=user_id,
            role=role,
            content=content,
            metadata=metadata,
            created_at=datetime.now(timezone.utc),
        )

        result = await collection.insert_one(message.to_mongo_dict())
        message.id = result.inserted_id

        return message

    @classmethod
    async def get_by_session_id(
        cls,
        session_id: str,
        user_id: PyObjectId,
        skip: int = 0,
        limit: int = 100,
    ) -> list[SessionMessageInDB]:
        """
        Get all messages for a session in chronological order.

        Args:
            session_id: Session identifier
            user_id: User ID for access validation
            skip: Number of messages to skip
            limit: Maximum number of messages to return

        Returns:
            List of message documents
        """
        collection = cls._get_collection()

        cursor = collection.find(
            {"session_id": session_id, "user_id": user_id}
        ).sort("created_at", 1).skip(skip).limit(limit)

        messages = []
        async for doc in cursor:
            messages.append(SessionMessageInDB.model_validate(doc))

        return messages

    @classmethod
    async def count_by_session_id(
        cls,
        session_id: str,
        user_id: PyObjectId,
    ) -> int:
        """
        Count messages in a session.

        Args:
            session_id: Session identifier
            user_id: User ID for access validation

        Returns:
            Number of messages
        """
        collection = cls._get_collection()
        return await collection.count_documents(
            {"session_id": session_id, "user_id": user_id}
        )

    @classmethod
    async def delete_by_session_id(
        cls,
        session_id: str,
        user_id: PyObjectId,
    ) -> int:
        """
        Delete all messages for a session.

        Args:
            session_id: Session identifier
            user_id: User ID for access validation

        Returns:
            Number of messages deleted
        """
        collection = cls._get_collection()
        result = await collection.delete_many(
            {"session_id": session_id, "user_id": user_id}
        )
        return result.deleted_count


session_message_crud = SessionMessageCRUD()
