from contextlib import asynccontextmanager
from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from config import settings


class MongoDB:
    """Async MongoDB connection manager with singleton pattern."""

    client: AsyncIOMotorClient | None = None
    database: AsyncIOMotorDatabase | None = None

    @classmethod
    async def connect(cls) -> None:
        """Establish connection to MongoDB."""
        if cls.client is not None:
            return

        cls.client = AsyncIOMotorClient(
            settings.mongodb.uri.get_secret_value(),
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
        )
        cls.database = cls.client[settings.mongodb.database]

        # Verify connection
        await cls.client.admin.command("ping")

        # Create indexes
        await cls._create_indexes()

    @classmethod
    async def disconnect(cls) -> None:
        """
        Close MongoDB connection.

        Should be called during application shutdown.
        """
        if cls.client is not None:
            cls.client.close()
            cls.client = None
            cls.database = None

    @classmethod
    async def _create_indexes(cls) -> None:
        """Create database indexes for optimal query performance."""
        if cls.database is None:
            return

        # Users collection indexes
        users = cls.database[settings.mongodb.users_collection]
        await users.create_index("email", unique=True)

        # Sessions collection indexes
        sessions = cls.database[settings.mongodb.sessions_collection]
        await sessions.create_index("session_id", unique=True)
        await sessions.create_index("user_id")
        await sessions.create_index([("user_id", 1), ("created_at", -1)])

        # Documents collection indexes
        documents = cls.database[settings.mongodb.documents_collection]
        await documents.create_index("user_id")
        await documents.create_index("session_id")
        await documents.create_index([("session_id", 1), ("status", 1)])
        await documents.create_index([("user_id", 1), ("session_id", 1)])

        # Session messages collection indexes
        session_messages = cls.database["session_messages"]
        await session_messages.create_index([("session_id", 1), ("user_id", 1)])
        await session_messages.create_index([("session_id", 1), ("created_at", 1)])

        # LangGraph checkpoints indexes
        checkpoints = cls.database[settings.mongodb.checkpoints_collection]
        await checkpoints.create_index("thread_id")
        await checkpoints.create_index([("thread_id", 1), ("checkpoint_ns", 1)])

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """
        Get database instance.

        Returns:
            AsyncIOMotorDatabase: MongoDB database

        Raises:
            RuntimeError: If not connected
        """
        if cls.database is None:
            raise RuntimeError(
                "Database not connected. Call MongoDB.connect() first.")
        return cls.database

    @classmethod
    def get_collection(cls, name: str) -> AsyncIOMotorCollection:
        """
        Get a collection by name.

        Args:
            name: Collection name

        Returns:
            AsyncIOMotorCollection: MongoDB collection
        """
        return cls.get_database()[name]

    @classmethod
    def session_messages(cls) -> AsyncIOMotorCollection:
        """Get session messages collection."""
        return cls.get_collection(settings.mongodb.session_messages_collection)

    # Convenience properties for collections
    @classmethod
    @property
    def users(cls) -> AsyncIOMotorCollection:
        """Get users collection."""
        return cls.get_collection(settings.mongodb.users_collection)

    @classmethod
    @property
    def sessions(cls) -> AsyncIOMotorCollection:
        """Get sessions collection."""
        return cls.get_collection(settings.mongodb.sessions_collection)

    @classmethod
    @property
    def documents(cls) -> AsyncIOMotorCollection:
        """Get documents collection."""
        return cls.get_collection(settings.mongodb.documents_collection)

    @classmethod
    @property
    def checkpoints(cls) -> AsyncIOMotorCollection:
        """Get LangGraph checkpoints collection."""
        return cls.get_collection(settings.mongodb.checkpoints_collection)


async def get_db() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency to get database instance.

    Yields:
        AsyncIOMotorDatabase: MongoDB database
    """
    return MongoDB.get_database()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    Async context manager for database access.

    Yields:
        AsyncIOMotorDatabase: MongoDB database
    """
    try:
        yield MongoDB.get_database()
    finally:
        pass  # Connection managed at app level


def get_users_collection() -> AsyncIOMotorCollection:
    """Get users collection."""
    return MongoDB.get_collection(settings.mongodb.users_collection)


def get_sessions_collection() -> AsyncIOMotorCollection:
    """Get sessions collection."""
    return MongoDB.get_collection(settings.mongodb.sessions_collection)


def get_documents_collection() -> AsyncIOMotorCollection:
    """Get documents collection."""
    return MongoDB.get_collection(settings.mongodb.documents_collection)


def get_checkpoints_collection() -> AsyncIOMotorCollection:
    """Get LangGraph checkpoints collection."""
    return MongoDB.get_collection(settings.mongodb.checkpoints_collection)


def get_session_messages_collection() -> AsyncIOMotorCollection:
    """Get session messages collection."""
    return MongoDB.get_collection("session_messages")
