"""Pydantic schemas for user-related operations."""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base schema for user data."""
    email: EmailStr
    name: str
    phone: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str
    target_exam_id: Optional[int] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    name: Optional[str] = None
    phone: Optional[str] = None
    profile_pic: Optional[str] = None
    target_exam_id: Optional[int] = None


class UserResponse(UserBase):
    """Schema for user response data."""
    id: int
    profile_pic: Optional[str] = None
    target_exam_id: Optional[int] = None
    total_stars: int = 0
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
