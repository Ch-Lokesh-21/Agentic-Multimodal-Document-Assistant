"""
JWT authentication middleware and FastAPI dependencies.
"""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from schemas import CurrentUser
from services import AuthenticationError, auth_service


bearer_scheme = HTTPBearer(
    scheme_name="JWT",
    description="JWT Bearer token for authentication",
    auto_error=True,
)

optional_bearer_scheme = HTTPBearer(
    scheme_name="JWT",
    description="Optional JWT Bearer token",
    auto_error=False,
)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> CurrentUser:
    """Get current authenticated user from bearer token."""
    try:
        token = credentials.credentials
        user = await auth_service.get_current_user(token)
        
        return CurrentUser(
            id=user.id,
            email=user.email,
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(optional_bearer_scheme),
    ],
) -> Optional[CurrentUser]:
    """Get current user if authenticated, None otherwise."""
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        user = await auth_service.get_current_user(token)
        
        return CurrentUser(
            id=user.id,
            email=user.email,
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# Type aliases for dependency injection
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
OptionalUserDep = Annotated[Optional[CurrentUser], Depends(get_optional_user)]


def require_auth(request: Request, user: CurrentUserDep) -> CurrentUser:
    """Store user in request state for access in dependencies."""
    request.state.user = user
    return user


RequireAuthDep = Annotated[CurrentUser, Depends(require_auth)]
