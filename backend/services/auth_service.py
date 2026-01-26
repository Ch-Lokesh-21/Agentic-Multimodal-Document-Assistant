"""
Authentication service for user registration, login, and JWT management.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from config import settings
from crud import user_crud
from schemas import (
    UserSignupRequest,
    UserLoginRequest,
    UserCreate,
    UserInDB,
    TokenResponse,
    TokenPayload,
    AuthResponse,
)


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against hash."""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )

    @staticmethod
    def create_access_token(user_id: str, email: str) -> tuple[str, int]:
        """
        Create JWT access token.

        Args:
            user_id: User ID to encode
            email: User email

        Returns:
            Tuple of (token, expires_in_seconds)
        """
        expires_delta = timedelta(
            minutes=settings.jwt.access_token_expire_minutes)
        expire = datetime.now(timezone.utc) + expires_delta

        payload = {
            "sub": user_id,
            "email": email,
            "exp": int(expire.timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "type": "access",
        }

        token = jwt.encode(
            payload,
            settings.jwt.secret_key.get_secret_value(),
            algorithm=settings.jwt.algorithm,
        )

        return token, int(expires_delta.total_seconds())

    @staticmethod
    def create_refresh_token(user_id: str, email: str) -> tuple[str, int]:
        """
        Create JWT refresh token.

        Args:
            user_id: User ID to encode
            email: User email

        Returns:
            Tuple of (token, expires_in_seconds)
        """
        expires_delta = timedelta(
            days=settings.jwt.refresh_token_expire_days)
        expire = datetime.now(timezone.utc) + expires_delta

        payload = {
            "sub": user_id,
            "email": email,
            "exp": int(expire.timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "type": "refresh",
        }

        token = jwt.encode(
            payload,
            settings.jwt.secret_key.get_secret_value(),
            algorithm=settings.jwt.algorithm,
        )

        return token, int(expires_delta.total_seconds())

    @staticmethod
    def decode_token(token: str) -> TokenPayload:
        """
        Decode and validate JWT token.

        Args:
            token: JWT token string

        Returns:
            TokenPayload with decoded data

        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt.secret_key.get_secret_value(),
                algorithms=[settings.jwt.algorithm],
            )
            return TokenPayload(**payload)
        except JWTError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")

    @classmethod
    async def signup(cls, signup_data: UserSignupRequest) -> AuthResponse:
        """
        Register a new user.

        Args:
            signup_data: Signup request data

        Returns:
            AuthResponse with token

        Raises:
            AuthenticationError: If email already exists
        """
        if await user_crud.exists_by_email(signup_data.email):
            raise AuthenticationError("Email already registered")

        hashed_password = cls.hash_password(signup_data.password)

        user_create = UserCreate(
            email=signup_data.email.lower(),
            hashed_password=hashed_password,
        )
        user = await user_crud.create(user_create)

        token, expires_in = cls.create_access_token(str(user.id), user.email)
        refresh_token, refresh_expires_in = cls.create_refresh_token(str(user.id), user.email)

        return AuthResponse(
            success=True,
            message="User registered successfully",
            token=TokenResponse(
                access_token=token,
                token_type="bearer",
                expires_in=expires_in,
            ),
            refresh_token=refresh_token,
            refresh_token_expires_in=refresh_expires_in,
            user_id=str(user.id),
        )

    @classmethod
    async def login(cls, login_data: UserLoginRequest) -> AuthResponse:
        """
        Authenticate user and return token.

        Args:
            login_data: Login request data

        Returns:
            AuthResponse with token

        Raises:
            AuthenticationError: If credentials are invalid
        """
        user = await user_crud.get_by_email(login_data.email.lower())

        if user is None:
            raise AuthenticationError("Invalid email or password")

        if not cls.verify_password(login_data.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        token, expires_in = cls.create_access_token(str(user.id), user.email)
        refresh_token, refresh_expires_in = cls.create_refresh_token(str(user.id), user.email)

        return AuthResponse(
            success=True,
            message="Login successful",
            token=TokenResponse(
                access_token=token,
                token_type="bearer",
                expires_in=expires_in,
            ),
            refresh_token=refresh_token,
            refresh_token_expires_in=refresh_expires_in,
            user_id=str(user.id),
        )

    @classmethod
    async def get_current_user(cls, token: str) -> UserInDB:
        """
        Get current user from token.

        Args:
            token: JWT access token

        Returns:
            User document

        Raises:
            AuthenticationError: If token invalid or user not found
        """
        payload = cls.decode_token(token)

        user = await user_crud.get_by_id(payload.sub)
        if user is None:
            raise AuthenticationError("User not found")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        return user

    @classmethod
    async def refresh_access_token(cls, refresh_token: str) -> AuthResponse:
        """
        Generate new access token from refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            AuthResponse with new access token

        Raises:
            AuthenticationError: If refresh token is invalid
        """
        try:
            payload = cls.decode_token(refresh_token)
            
            if payload.type != "refresh":
                raise AuthenticationError("Invalid token type")
            
            user = await user_crud.get_by_id(payload.sub)
            if user is None:
                raise AuthenticationError("User not found")

            if not user.is_active:
                raise AuthenticationError("Account is deactivated")

            token, expires_in = cls.create_access_token(str(user.id), user.email)

            return AuthResponse(
                success=True,
                message="Token refreshed successfully",
                token=TokenResponse(
                    access_token=token,
                    token_type="bearer",
                    expires_in=expires_in,
                ),
                user_id=str(user.id),
            )
        except AuthenticationError:
            raise


auth_service = AuthService()
