"""
FastAPI dependencies for authentication and authorization.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Decode the JWT token and return the corresponding user.

    Raises:
        HTTPException 401: If token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "success": False,
            "error": {
                "code": "INVALID_CREDENTIALS",
                "message": "Could not validate credentials.",
            },
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        user_id: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if user_id is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Ensure the current user is active.

    Raises:
        HTTPException 403: If user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "INACTIVE_USER",
                    "message": "User account is deactivated.",
                },
            },
        )
    return current_user


def require_role(*roles: UserRole):
    """
    Factory that creates a dependency enforcing role-based access.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(UserRole.ADMIN))])
        async def admin_endpoint():
            ...

    Or as a parameter dependency:
        async def endpoint(user: User = Depends(require_role(UserRole.ADMIN, UserRole.PORT_OWNER))):
            ...
    """

    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "INSUFFICIENT_PERMISSIONS",
                        "message": f"This action requires one of the following roles: {', '.join(r.value for r in roles)}.",
                    },
                },
            )
        return current_user

    return role_checker
