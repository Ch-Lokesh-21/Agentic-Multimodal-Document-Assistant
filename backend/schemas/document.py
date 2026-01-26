"""Document schemas for PDF upload and ingestion."""

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import Field

from utils.object_id import PyObjectId, create_object_id

from .base import BaseSchema, MongoBaseSchema, TimestampMixin


class DocumentStatus(str, Enum):
    """Document processing status enum."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class DocumentBase(BaseSchema):
    """Base document schema."""

    file_name: str = Field(
        description="Original file name",
        examples=["research_paper.pdf"],
    )


class DocumentCreate(DocumentBase):
    """Schema for creating a document record."""

    user_id: PyObjectId = Field(
        description="Owner user ID",
    )
    session_id: str = Field(
        description="Session this document belongs to",
    )
    file_path: str = Field(
        description="Path to stored file",
    )
    file_size: int = Field(
        ge=0,
        description="File size in bytes",
    )
    content_type: str = Field(
        default="application/pdf",
        description="File MIME type",
    )


class DocumentInDB(MongoBaseSchema, TimestampMixin):
    """Document record stored in MongoDB."""

    user_id: PyObjectId = Field(
        description="Owner user ID",
    )
    session_id: str = Field(
        description="Session ID this document belongs to",
    )
    file_name: str = Field(
        description="Original file name",
    )
    file_path: str = Field(
        description="Path to stored file on disk",
    )
    file_size: int = Field(
        ge=0,
        description="File size in bytes",
    )
    content_type: str = Field(
        default="application/pdf",
        description="File MIME type",
    )
    status: DocumentStatus = Field(
        default=DocumentStatus.UPLOADED,
        description="Current processing status",
    )
    chunk_count: int | None = Field(
        default=None,
        description="Number of chunks after ingestion",
    )
    page_count: int | None = Field(
        default=None,
        description="Number of pages in document",
    )
    error_message: str | None = Field(
        default=None,
        description="Error message if processing failed",
    )
    processed_at: datetime | None = Field(
        default=None,
        description="Timestamp when processing completed",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "user_id": "507f1f77bcf86cd799439012",
                "session_id": "session_abc123def456",
                "file_name": "attention_is_all_you_need.pdf",
                "file_path": "./app/uploads/session_abc123def456/attention_is_all_you_need.pdf",
                "file_size": 2048576,
                "content_type": "application/pdf",
                "status": "indexed",
                "chunk_count": 42,
                "page_count": 15,
                "created_at": "2024-01-01T00:00:00Z",
                "processed_at": "2024-01-01T00:01:00Z",
            }
        }
    }


class DocumentResponse(BaseSchema):
    """API response for document details."""

    id: str = Field(
        description="Document ID",
    )
    session_id: str = Field(
        description="Session ID",
    )
    file_name: str = Field(
        description="Original file name",
    )
    file_size: int = Field(
        description="File size in bytes",
    )
    status: DocumentStatus = Field(
        description="Processing status",
    )
    chunk_count: int | None = Field(
        default=None,
        description="Number of indexed chunks",
    )
    page_count: int | None = Field(
        default=None,
        description="Number of pages",
    )
    error_message: str | None = Field(
        default=None,
        description="Error message if failed",
    )
    created_at: datetime = Field(
        description="Upload timestamp",
    )
    processed_at: datetime | None = Field(
        default=None,
        description="Processing completion timestamp",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "session_id": "session_abc123def456",
                "file_name": "attention_is_all_you_need.pdf",
                "file_size": 2048576,
                "status": "indexed",
                "chunk_count": 42,
                "page_count": 15,
                "created_at": "2024-01-01T00:00:00Z",
                "processed_at": "2024-01-01T00:01:00Z",
            }
        }
    }

    @classmethod
    def from_db(cls, doc: DocumentInDB) -> "DocumentResponse":
        """Create response from database model."""
        return cls(
            id=str(doc.id),
            session_id=doc.session_id,
            file_name=doc.file_name,
            file_size=doc.file_size,
            status=doc.status,
            chunk_count=doc.chunk_count,
            page_count=doc.page_count,
            error_message=doc.error_message,
            created_at=doc.created_at,
            processed_at=doc.processed_at,
        )


class DocumentUploadResponse(BaseSchema):
    """Response for document upload."""

    success: bool = Field(default=True)
    message: str = Field(default="Document uploaded successfully")
    document: DocumentResponse = Field(
        description="Uploaded document details",
    )


class DocumentListResponse(BaseSchema):
    """Response for document list."""

    documents: list[DocumentResponse] = Field(
        default_factory=list,
        description="List of documents",
    )
    total: int = Field(
        default=0,
        description="Total number of documents",
    )


class DocumentStatusUpdate(BaseSchema):
    """Document status update."""

    status: DocumentStatus = Field(
        description="New status",
    )
    chunk_count: int | None = Field(
        default=None,
        description="Number of chunks after indexing",
    )
    page_count: int | None = Field(
        default=None,
        description="Number of pages",
    )
    error_message: str | None = Field(
        default=None,
        description="Error message if failed",
    )
