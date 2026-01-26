from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from db import get_users_collection
from schemas import UserCreate, UserInDB
from utils.object_id import PyObjectId


class UserCRUD:
    """CRUD operations for User documents."""

    @staticmethod
    def _get_collection() -> AsyncIOMotorCollection:
        """Get users collection."""
        return get_users_collection()

    @classmethod
    async def create(cls, user_data: UserCreate) -> UserInDB:
        """
        Create a new user.

        Args:
            user_data: User creation data with hashed password

        Returns:
            Created user document
        """
        collection = cls._get_collection()

        user = UserInDB(
            email=user_data.email,
            hashed_password=user_data.hashed_password,
            created_at=datetime.now(timezone.utc),
        )

        result = await collection.insert_one(user.to_mongo_dict())
        user.id = result.inserted_id  

        return user

    @classmethod
    async def get_by_id(cls, user_id: str | PyObjectId) -> Optional[UserInDB]:
        """
        Get user by ID.

        Args:
            user_id: User document ID

        Returns:
            User document or None if not found
        """
        collection = cls._get_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        doc = await collection.find_one({"_id": user_id})

        if doc is None:
            return None

        return UserInDB.model_validate(doc)

    @classmethod
    async def get_by_email(cls, email: str) -> Optional[UserInDB]:
        """
        Get user by email address.

        Args:
            email: User email

        Returns:
            User document or None if not found
        """
        collection = cls._get_collection()

        doc = await collection.find_one({"email": email.lower()})

        if doc is None:
            return None

        return UserInDB.model_validate(doc)

    @classmethod
    async def exists_by_email(cls, email: str) -> bool:
        """
        Check if user with email exists.

        Args:
            email: Email to check

        Returns:
            True if user exists
        """
        collection = cls._get_collection()
        count = await collection.count_documents({"email": email.lower()}, limit=1)
        return count > 0

    @classmethod
    async def update(
        cls,
        user_id: str | PyObjectId,
        update_data: dict,
    ) -> Optional[UserInDB]:
        """
        Update user document.

        Args:
            user_id: User document ID
            update_data: Fields to update

        Returns:
            Updated user document or None
        """
        collection = cls._get_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        update_data["updated_at"] = datetime.now(timezone.utc)

        result = await collection.find_one_and_update(
            {"_id": user_id},
            {"$set": update_data},
            return_document=True,
        )

        if result is None:
            return None

        return UserInDB.model_validate(result)

    @classmethod
    async def delete(cls, user_id: str | PyObjectId) -> bool:
        """
        Delete user document.

        Args:
            user_id: User document ID

        Returns:
            True if deleted, False if not found
        """
        collection = cls._get_collection()

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        result = await collection.delete_one({"_id": user_id})
        return result.deleted_count > 0


user_crud = UserCRUD()
