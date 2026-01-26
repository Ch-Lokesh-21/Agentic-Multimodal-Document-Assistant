"""
User model schemas for MongoDB storage and API responses.
"""

from datetime import datetime, timezone

from pydantic import EmailStr, Field

from utils.object_id import PyObjectId, create_object_id

from .base import BaseSchema, MongoBaseSchema, TimestampMixin


class UserBase(BaseSchema):
    """Base user schema with common fields."""

    email: EmailStr = Field(
        description="User email address",
        examples=["user@example.com"],
    )


class UserCreate(UserBase):
    """Schema for creating a new user."""

    hashed_password: str = Field(
        description="Bcrypt hashed password",
    )


class UserInDB(MongoBaseSchema, TimestampMixin):
    """
    User document schema as stored in MongoDB.

    MongoDB Collection: users
    """

    email: EmailStr = Field(
        description="User email address (unique)",
    )
    hashed_password: str = Field(
        description="Bcrypt hashed password",
    )
    is_active: bool = Field(
        default=True,
        description="Whether user account is active",
    )
    is_verified: bool = Field(
        default=False,
        description="Whether email is verified",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "email": "user@example.com",
                "hashed_password": "$2b$12$...",
                "is_active": True,
                "is_verified": False,
                "created_at": "2024-01-01T00:00:00Z",
            }
        }
    }


class UserResponse(BaseSchema):
    """User response schema (excludes sensitive data)."""

    id: str = Field(
        description="User ID",
        alias="_id",
    )
    email: EmailStr = Field(
        description="User email address",
    )
    is_active: bool = Field(
        description="Whether user account is active",
    )
    is_verified: bool = Field(
        description="Whether email is verified",
    )
    created_at: datetime = Field(
        description="Account creation timestamp",
    )

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "email": "user@example.com",
                "is_active": True,
                "is_verified": False,
                "created_at": "2024-01-01T00:00:00Z",
            }
        }
    }

    @classmethod
    def from_db(cls, user: UserInDB) -> "UserResponse":
        """Create response from database model."""
        return cls(
            _id=str(user.id),
            email=user.email,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
        )


class CurrentUser(BaseSchema):
    """Schema for current authenticated user (injected via middleware)."""

    id: PyObjectId = Field(
        description="User ID",
    )
    email: EmailStr = Field(
        description="User email",
    )

    @classmethod
    def from_token_payload(cls, user_id: str, email: str) -> "CurrentUser":
        """Create CurrentUser from JWT token payload."""
        return cls(id=PyObjectId(user_id), email=email)
