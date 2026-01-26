"""Session schemas for multi-session RAG workflow."""

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import Field, field_validator

from utils.object_id import PyObjectId, create_object_id

from .base import BaseSchema, MongoBaseSchema, TimestampMixin


def generate_session_id() -> str:
    """Generate unique session ID."""
    return f"session_{uuid4().hex[:16]}"


class SessionBase(BaseSchema):
    """Base session schema."""

    name: str = Field(
        min_length=1,
        max_length=255,
        description="Session display name",
        examples=["Research Paper Analysis"],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional session description",
    )


class SessionCreate(SessionBase):
    """Schema for creating a new session."""
    pass


class SessionInDB(MongoBaseSchema, TimestampMixin):
    """
    Session document schema as stored in MongoDB.

    MongoDB Collection: sessions
    """

    session_id: str = Field(
        default_factory=generate_session_id,
        description="Unique session identifier (used as thread_id and collection name)",
    )
    user_id: PyObjectId = Field(
        description="Owner user ID",
    )
    name: str = Field(
        description="Session display name",
    )
    description: str | None = Field(
        default=None,
        description="Optional session description",
    )
    document_count: int = Field(
        default=0,
        ge=0,
        description="Number of documents in this session",
    )
    last_activity_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last activity timestamp",
    )
    is_active: bool = Field(
        default=True,
        description="Whether session is active",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "session_id": "session_abc123def456",
                "user_id": "507f1f77bcf86cd799439012",
                "name": "Research Paper Analysis",
                "description": "Analyzing transformer architecture papers",
                "document_count": 3,
                "created_at": "2024-01-01T00:00:00Z",
                "last_activity_at": "2024-01-01T12:00:00Z",
                "is_active": True,
            }
        }
    }


class SessionResponse(BaseSchema):
    """Session response schema for API responses."""

    id: str = Field(
        description="MongoDB document ID",
    )
    session_id: str = Field(
        description="Unique session identifier",
    )
    name: str = Field(
        description="Session display name",
    )
    description: str | None = Field(
        default=None,
        description="Session description",
    )
    document_count: int = Field(
        description="Number of documents",
    )
    created_at: datetime = Field(
        description="Creation timestamp",
    )
    last_activity_at: datetime = Field(
        description="Last activity timestamp",
    )
    is_active: bool = Field(
        description="Whether session is active",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "session_id": "session_abc123def456",
                "name": "Research Paper Analysis",
                "description": "Analyzing transformer architecture papers",
                "document_count": 3,
                "created_at": "2024-01-01T00:00:00Z",
                "last_activity_at": "2024-01-01T12:00:00Z",
                "is_active": True,
            }
        }
    }

    @classmethod
    def from_db(cls, session: SessionInDB) -> "SessionResponse":
        """Create response from database model."""
        return cls(
            id=str(session.id),
            session_id=session.session_id,
            name=session.name,
            description=session.description,
            document_count=session.document_count,
            created_at=session.created_at,
            last_activity_at=session.last_activity_at,
            is_active=session.is_active,
        )


class SessionUpdate(BaseSchema):
    """Schema for updating a session."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated session name",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Updated description",
    )


class SessionListResponse(BaseSchema):
    """Response schema for session list endpoint."""

    sessions: list[SessionResponse] = Field(
        default_factory=list,
        description="List of sessions",
    )
    total: int = Field(
        default=0,
        description="Total number of sessions",
    )
