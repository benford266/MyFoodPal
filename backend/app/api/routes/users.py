"""
User Management API Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database.connection import get_db
from ...database.models import User
from ...models.schemas import UserResponse, UserPreferencesUpdate
from ...services.auth import AuthService

router = APIRouter()
auth_service = AuthService()


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get current user profile"""
    return current_user


@router.put("/preferences", response_model=UserResponse)
async def update_user_preferences(
    preferences: UserPreferencesUpdate,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Update user food preferences"""
    
    if preferences.liked_foods is not None:
        current_user.liked_foods = ",".join(preferences.liked_foods)
    
    if preferences.disliked_foods is not None:
        current_user.disliked_foods = ",".join(preferences.disliked_foods)
    
    if preferences.must_use_ingredients is not None:
        current_user.must_use_ingredients = ",".join(preferences.must_use_ingredients)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user