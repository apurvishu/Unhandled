"""User schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    """Schema for user registration."""
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole


class UserLogin(BaseModel):
    """Schema for user login (used with OAuth2PasswordRequestForm too)."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    name: str | None = Field(None, min_length=2, max_length=255)
    email: EmailStr | None = None
    is_active: bool | None = None
    role: UserRole | None = None


class UserResponse(BaseModel):
    """Schema for user in responses — never expose password_hash."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ShipOwnerCreate(BaseModel):
    """Schema for creating a ship owner profile."""
    company_name: str = Field(..., min_length=2, max_length=255)
    contact_information: str | None = None
    address: str | None = None


class ShipOwnerResponse(BaseModel):
    """Schema for ship owner in responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    company_name: str
    contact_information: str | None = None
    address: str | None = None
    created_at: datetime
