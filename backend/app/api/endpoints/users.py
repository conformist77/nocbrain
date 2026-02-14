"""
NOCbRAIN User Management Endpoints
Basic user management functionality
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from pydantic import BaseModel

router = APIRouter()


class UserResponse(BaseModel):
    """User response model"""
    id: int
    username: str
    email: str
    is_active: bool = True


class UserCreate(BaseModel):
    """User creation model"""
    username: str
    email: str
    password: str


@router.get("/", response_model=List[UserResponse])
async def get_users() -> List[UserResponse]:
    """Get all users"""
    # Mock implementation
    return [
        UserResponse(id=1, username="admin", email="admin@nocbrain.com"),
        UserResponse(id=2, username="user", email="user@nocbrain.com")
    ]


@router.post("/", response_model=UserResponse)
async def create_user(user_data: UserCreate) -> UserResponse:
    """Create a new user"""
    # Mock implementation
    return UserResponse(
        id=3,
        username=user_data.username,
        email=user_data.email
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int) -> UserResponse:
    """Get user by ID"""
    # Mock implementation
    if user_id == 1:
        return UserResponse(id=1, username="admin", email="admin@nocbrain.com")
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
