"""Base Pydantic schemas with common configuration."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from utils.object_id import PyObjectId, create_object_id


class BaseSchema(BaseModel):
    """Base schema with Pydantic v2 configuration."""
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        use_enum_values=True,
        validate_default=True,
        str_strip_whitespace=True,
        json_encoders={
            PyObjectId: str,
            datetime: lambda v: v.isoformat(),
        },
    )


class MongoBaseSchema(BaseSchema):
    """
    Base schema for MongoDB documents with _id field.
    
    Automatically handles ObjectId conversion.
    """
    
    id: PyObjectId = Field(
        default_factory=create_object_id,
        alias="_id",
        description="MongoDB document ID",
    )
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        use_enum_values=True,
        validate_default=True,
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "_id": "507f1f77bcf86cd799439011",
            }
        },
    )
    
    def to_mongo_dict(self) -> dict[str, Any]:
        """
        Convert model to MongoDB-compatible dictionary.
        
        Returns:
            Dict with _id as ObjectId
        """
        data = self.model_dump(by_alias=True, exclude_none=True, mode="python")
        return data
    
    @classmethod
    def from_mongo(cls, data: dict[str, Any]) -> "MongoBaseSchema":
        """
        Create model instance from MongoDB document.
        
        Args:
            data: MongoDB document dictionary
            
        Returns:
            Model instance
        """
        if data is None:
            raise ValueError("Cannot create model from None")
        return cls.model_validate(data)


class TimestampMixin(BaseModel):
    """Mixin for adding timestamp fields."""
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Document creation timestamp",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Last update timestamp",
    )


class APIResponse(BaseSchema):
    """Standard API response wrapper."""
    
    success: bool = Field(
        default=True,
        description="Whether the request was successful",
    )
    message: str = Field(
        default="Operation completed successfully",
        description="Human-readable message",
    )
    data: Any = Field(
        default=None,
        description="Response payload",
    )


class PaginatedResponse(BaseSchema):
    """Paginated response for list endpoints."""
    
    items: list[Any] = Field(
        default_factory=list,
        description="List of items",
    )
    total: int = Field(
        default=0,
        description="Total number of items",
    )
    page: int = Field(
        default=1,
        ge=1,
        description="Current page number",
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Items per page",
    )
    pages: int = Field(
        default=1,
        ge=1,
        description="Total number of pages",
    )
    
    @classmethod
    def create(
        cls,
        items: list[Any],
        total: int,
        page: int = 1,
        page_size: int = 20,
    ) -> "PaginatedResponse":
        """
        Create paginated response.
        
        Args:
            items: List of items for current page
            total: Total count of all items
            page: Current page number
            page_size: Items per page
            
        Returns:
            PaginatedResponse instance
        """
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )


class ErrorResponse(BaseSchema):
    """Standard error response."""
    
    success: bool = Field(default=False)
    error: str = Field(description="Error type/code")
    message: str = Field(description="Human-readable error message")
    details: dict[str, Any] | None = Field(
        default=None,
        description="Additional error details",
    )
