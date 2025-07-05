from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    liked_foods: str
    disliked_foods: str
    must_use_ingredients: str
    created_at: datetime
    is_active: bool

class MealPlanCreate(BaseModel):
    name: str
    serving_size: int
    recipe_count: int
    recipes_json: str
    shopping_list_json: str
    liked_foods_snapshot: str
    disliked_foods_snapshot: str
    must_use_ingredients_snapshot: str

class MealPlanResponse(BaseModel):
    id: int
    user_id: int
    name: str
    serving_size: int
    recipe_count: int
    recipes_json: str
    shopping_list_json: str
    liked_foods_snapshot: str
    disliked_foods_snapshot: str
    must_use_ingredients_snapshot: str
    created_at: datetime
    rating: Optional[int]
    notes: str