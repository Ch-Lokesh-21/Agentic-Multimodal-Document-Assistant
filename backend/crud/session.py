from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from db import get_sessions_collection
from schemas import SessionCreate, SessionInDB, SessionUpdate, generate_session_id
from utils.object_id import PyObjectId


class SessionCRUD:
    """CRUD operations for Session documents."""

    @staticmethod
    def _get_collection() -> AsyncIOMotorCollection:
        """Get sessions collection."""
        return get_sessions_collection()

    @classmethod
    async def create(
        cls,
        user_id: PyObjectId,
        session_data: SessionCreate,
    ) -> SessionInDB:
        """
        Create a new session.

        Args:
            user_id: Owner user ID
            session_data: Session creation data

        Returns:
            Created session document
        """
        collection = cls._get_collection()

        session = SessionInDB(
            session_id=generate_session_id(),
            user_id=user_id,
            name=session_data.name,
            description=session_data.description,
            created_at=datetime.now(timezone.utc),
            last_activity_at=datetime.now(timezone.utc),
        )

        result = await collection.insert_one(session.to_mongo_dict())
        session.id = result.inserted_id

        return session

    @classmethod
    async def get_by_id(cls, session_doc_id: str | PyObjectId) -> Optional[SessionInDB]:
        """
        Get session by MongoDB document ID.

        Args:
            session_doc_id: MongoDB document _id

        Returns:
            Session document or None
        """
        collection = cls._get_collection()

        if isinstance(session_doc_id, str):
            session_doc_id = ObjectId(session_doc_id)

        doc = await collection.find_one({"_id": session_doc_id})

        if doc is None:
            return None

        return SessionInDB.model_validate(doc)

    @classmethod
    async def get_by_session_id(cls, session_id: str) -> Optional[SessionInDB]:
        """
        Get session by unique session_id.

        Args:
            session_id: Unique session identifier (e.g., "session_abc123")

        Returns:
            Session document or None
        """
        collection = cls._get_collection()

        doc = await collection.find_one({"session_id": session_id})

        if doc is None:
            return None

        return SessionInDB.model_validate(doc)

    @classmethod
    async def get_by_session_id_and_user(
        cls,
        session_id: str,
        user_id: PyObjectId,
    ) -> Optional[SessionInDB]:
        """
        Get session by session_id, validating user ownership.

        Args:
            session_id: Session identifier
            user_id: User ID for ownership validation

        Returns:
            Session document or None if not found or not owned by user
        """
        collection = cls._get_collection()

        doc = await collection.find_one({
            "session_id": session_id,
            "user_id": ObjectId(str(user_id)),
        })

        if doc is None:
            return None

        return SessionInDB.model_validate(doc)

    @classmethod
    async def get_all_by_user(
        cls,
        user_id: PyObjectId,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> list[SessionInDB]:
        """
        Get all sessions for a user.

        Args:
            user_id: User ID
            skip: Number of documents to skip
            limit: Maximum documents to return
            active_only: Only return active sessions

        Returns:
            List of session documents
        """
        collection = cls._get_collection()

        query = {"user_id": ObjectId(str(user_id))}
        if active_only:
            query["is_active"] = True

        cursor = collection.find(query).sort(
            "created_at", -1).skip(skip).limit(limit)

        sessions = []
        async for doc in cursor:
            sessions.append(SessionInDB.model_validate(doc))

        return sessions

    @classmethod
    async def count_by_user(cls, user_id: PyObjectId, active_only: bool = True) -> int:
        """
        Count sessions for a user.

        Args:
            user_id: User ID
            active_only: Only count active sessions

        Returns:
            Number of sessions
        """
        collection = cls._get_collection()

        query = {"user_id": ObjectId(str(user_id))}
        if active_only:
            query["is_active"] = True

        return await collection.count_documents(query)

    @classmethod
    async def update(
        cls,
        session_id: str,
        user_id: PyObjectId,
        update_data: SessionUpdate,
    ) -> Optional[SessionInDB]:
        """
        Update session document.

        Args:
            session_id: Session identifier
            user_id: User ID for ownership validation
            update_data: Fields to update

        Returns:
            Updated session or None if not found/not owned
        """
        collection = cls._get_collection()

        update_dict = update_data.model_dump(exclude_none=True)
        update_dict["updated_at"] = datetime.now(timezone.utc)

        result = await collection.find_one_and_update(
            {
                "session_id": session_id,
                "user_id": ObjectId(str(user_id)),
            },
            {"$set": update_dict},
            return_document=True,
        )

        if result is None:
            return None

        return SessionInDB.model_validate(result)

    @classmethod
    async def update_activity(cls, session_id: str) -> bool:
        """
        Update last activity timestamp.

        Args:
            session_id: Session identifier

        Returns:
            True if updated
        """
        collection = cls._get_collection()

        result = await collection.update_one(
            {"session_id": session_id},
            {"$set": {"last_activity_at": datetime.now(timezone.utc)}},
        )

        return result.modified_count > 0

    @classmethod
    async def increment_document_count(cls, session_id: str, delta: int = 1) -> bool:
        """
        Increment document count for session.

        Args:
            session_id: Session identifier
            delta: Amount to increment (can be negative)

        Returns:
            True if updated
        """
        collection = cls._get_collection()

        result = await collection.update_one(
            {"session_id": session_id},
            {
                "$inc": {"document_count": delta},
                "$set": {"last_activity_at": datetime.now(timezone.utc)},
            },
        )

        return result.modified_count > 0

    @classmethod
    async def delete(cls, session_id: str, user_id: PyObjectId) -> bool:
        """
        Soft delete session (mark as inactive).

        Args:
            session_id: Session identifier
            user_id: User ID for ownership validation

        Returns:
            True if deleted
        """
        collection = cls._get_collection()

        result = await collection.update_one(
            {
                "session_id": session_id,
                "user_id": ObjectId(str(user_id)),
            },
            {
                "$set": {
                    "is_active": False,
                    "updated_at": datetime.now(timezone.utc),
                },
            },
        )

        return result.modified_count > 0

    @classmethod
    async def hard_delete(cls, session_id: str, user_id: PyObjectId) -> bool:
        """
        Permanently delete session.

        Args:
            session_id: Session identifier
            user_id: User ID for ownership validation

        Returns:
            True if deleted
        """
        collection = cls._get_collection()

        result = await collection.delete_one({
            "session_id": session_id,
            "user_id": ObjectId(str(user_id)),
        })

        return result.deleted_count > 0


session_crud = SessionCRUD()
