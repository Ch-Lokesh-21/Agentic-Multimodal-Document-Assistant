"""
Authentication schemas for signup, login, and JWT tokens.
"""

from pydantic import EmailStr, Field, field_validator

from .base import BaseSchema


class UserSignupRequest(BaseSchema):
    """Request schema for user registration."""

    email: EmailStr = Field(
        description="User email address",
        examples=["user@example.com"],
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="User password (min 8 characters)",
        examples=["securepassword123"],
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError(
                "Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError(
                "Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLoginRequest(BaseSchema):
    """Request schema for user login."""

    email: EmailStr = Field(
        description="User email address",
        examples=["user@example.com"],
    )
    password: str = Field(
        description="User password",
        examples=["securepassword123"],
    )


class TokenResponse(BaseSchema):
    """Response schema for authentication tokens."""

    access_token: str = Field(
        description="JWT access token",
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')",
    )
    expires_in: int = Field(
        description="Token expiration time in seconds",
    )


class TokenPayload(BaseSchema):
    """JWT token payload schema."""

    sub: str = Field(
        description="Subject (user ID)",
    )
    email: str = Field(
        description="User email",
    )
    exp: int = Field(
        description="Expiration timestamp",
    )
    iat: int = Field(
        description="Issued at timestamp",
    )
    type: str = Field(
        default="access",
        description="Token type",
    )


class AuthResponse(BaseSchema):
    """Response schema for successful authentication."""

    success: bool = Field(default=True)
    message: str = Field(default="Authentication successful")
    token: TokenResponse = Field(
        description="Authentication token details",
    )
    refresh_token: str = Field(
        default=None,
        description="Refresh token for obtaining new access tokens",
    )
    refresh_token_expires_in: int = Field(
        default=None,
        description="Refresh token expiration time in seconds",
    )
    user_id: str = Field(
        description="Authenticated user ID",
    )
