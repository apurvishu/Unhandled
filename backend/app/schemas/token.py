"""Token schemas for JWT authentication."""

from pydantic import BaseModel


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT token payload."""
    sub: str
    exp: int
    type: str


class RefreshTokenRequest(BaseModel):
    """Request to refresh an access token."""
    refresh_token: str
