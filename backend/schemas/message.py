"""Message schemas for session conversation history."""

from datetime import datetime, timezone
from typing import Literal

from pydantic import Field

from utils.object_id import PyObjectId

from .base import BaseSchema, MongoBaseSchema, TimestampMixin


class MessageRole(str):
    """Message role types."""
    USER = "user"
    ASSISTANT = "assistant"


class SessionMessageBase(BaseSchema):
    """Base session message schema."""

    role: Literal["user", "assistant"] = Field(
        description="Message role (user or assistant)",
    )
    content: str = Field(
        min_length=1,
        description="Message content (query or answer)",
    )


class SessionMessageCreate(SessionMessageBase):
    """Schema for creating a new session message."""
    pass


class SessionMessageInDB(MongoBaseSchema, TimestampMixin):
    """
    Session message document schema as stored in MongoDB.

    MongoDB Collection: session_messages

    Stores the conversation history for display in the frontend.
    Each message is either a user query or an assistant response.
    """

    session_id: str = Field(
        description="Session identifier this message belongs to",
    )
    user_id: PyObjectId = Field(
        description="User who owns this session",
    )
    role: Literal["user", "assistant"] = Field(
        description="Message role (user or assistant)",
    )
    content: str = Field(
        description="Message content (query or answer)",
    )
    metadata: dict | None = Field(
        default=None,
        description="Optional metadata (citations, sources, etc.)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "session_id": "session_abc123def456",
                "user_id": "507f1f77bcf86cd799439012",
                "role": "user",
                "content": "What is the transformer architecture?",
                "metadata": None,
                "created_at": "2024-01-01T00:00:00Z",
            }
        }
    }


class SessionMessageResponse(BaseSchema):
    """Session message response schema for API responses."""

    id: str = Field(
        description="MongoDB document ID",
    )
    session_id: str = Field(
        description="Session identifier",
    )
    role: Literal["user", "assistant"] = Field(
        description="Message role",
    )
    content: str = Field(
        description="Message content",
    )
    metadata: dict | None = Field(
        default=None,
        description="Optional metadata",
    )
    created_at: datetime = Field(
        description="Message timestamp",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "session_id": "session_abc123def456",
                "role": "assistant",
                "content": "The transformer architecture is a neural network...",
                "metadata": {
                    "citations": [{"source_id": "doc1", "page_number": 1}]
                },
                "created_at": "2024-01-01T00:00:00Z",
            }
        }
    }

    @classmethod
    def from_db(cls, message: SessionMessageInDB) -> "SessionMessageResponse":
        """Create response from database model."""
        return cls(
            id=str(message.id),
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            metadata=message.metadata,
            created_at=message.created_at,
        )


class SessionMessagesListResponse(BaseSchema):
    """Response for session messages list."""

    session_id: str = Field(
        description="Session identifier",
    )
    messages: list[SessionMessageResponse] = Field(
        description="List of messages in chronological order",
    )
    total: int = Field(
        description="Total number of messages",
    )
