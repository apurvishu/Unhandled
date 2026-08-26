"""Authentication routes: register, login, refresh, profile."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.ship_owner import ShipOwner
from app.models.user import User, UserRole
from app.schemas.common import StandardResponse
from app.schemas.token import RefreshTokenRequest, Token
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.utils.errors import AppException, ConflictException

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=StandardResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == user_in.email))
    if existing.scalar_one_or_none() is not None:
        raise ConflictException("An account with this email address already exists.")

    hashed_pw = get_password_hash(user_in.password)
    user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=hashed_pw,
        role=user_in.role,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    # If role is SHIP_OWNER, initialize ship_owner profile
    if user.role == UserRole.SHIP_OWNER:
        owner = ShipOwner(
            user_id=user.id,
            company_name=f"{user.name} Shipping",
        )
        db.add(owner)
        await db.flush()

    return StandardResponse(
        data=UserResponse.model_validate(user),
        message="User registered successfully.",
    )


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
):
    """OAuth2 compatible login returning JWT access and refresh tokens."""
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Incorrect email or password.",
                },
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
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

    access_token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value, "email": user.email},
    )
    refresh_token = create_refresh_token(subject=user.id)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_in: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchange a valid refresh token for a new access token."""
    try:
        payload = decode_token(refresh_in.refresh_token)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"success": False, "error": {"code": "INVALID_TOKEN", "message": "Invalid refresh token."}},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "error": {"code": "INVALID_TOKEN", "message": "Invalid or expired refresh token."}},
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "error": {"code": "USER_NOT_FOUND", "message": "User not found or inactive."}},
        )

    new_access_token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value, "email": user.email},
    )
    new_refresh_token = create_refresh_token(subject=user.id)

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.get("/me", response_model=StandardResponse[UserResponse])
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve the currently authenticated user's profile."""
    return StandardResponse(data=UserResponse.model_validate(current_user))
