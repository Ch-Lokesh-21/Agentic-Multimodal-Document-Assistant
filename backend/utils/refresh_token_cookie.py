from fastapi import Response
from config import settings

def set_refresh_token_cookie(response: Response, refresh_token: str, max_age: int):
    """
    Set refresh token cookie with environment-aware security settings.
    
    In production with HTTPS:
    - secure=True (only sent over HTTPS)
    - samesite="none" (for cross-origin) or "lax" (same-site)
    - httponly=True (XSS protection)
    
    In development:
    - secure=False (works with HTTP localhost)
    - samesite="lax"
    """
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=max_age,
        httponly=settings.cookie.httponly,
        secure=settings.cookie.secure,
        samesite=settings.cookie.samesite,
    )

def delete_refresh_token_cookie(response: Response):
    """
    Delete refresh token cookie with matching security settings.
    """
    response.delete_cookie(
        key="refresh_token",
        httponly=settings.cookie.httponly,
        secure=settings.cookie.secure,
        samesite=settings.cookie.samesite,
    )
