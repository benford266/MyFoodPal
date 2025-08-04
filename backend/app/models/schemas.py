"""
Pydantic Schemas for API Request/Response Models
"""
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# Authentication Schemas
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

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# Recipe Generation Schemas
class RecipeGenerationRequest(BaseModel):
    liked_foods: List[str] = []
    disliked_foods: List[str] = []
    must_use_ingredients: List[str] = []
    recipe_count: int = 5
    serving_size: int = 4
    generate_images: bool = True


class RecipeIngredient(BaseModel):
    item: str
    quantity: str
    unit: str


class Recipe(BaseModel):
    name: str
    prep_time: str
    cook_time: str
    servings: int
    cuisine_inspiration: str
    difficulty: str
    ingredients: List[RecipeIngredient]
    instructions: List[str]
    image_path: Optional[str] = None


class ShoppingListItem(BaseModel):
    ingredient: str
    quantity: str
    unit: str
    used_in_recipes: List[str]


class MealPlanResponse(BaseModel):
    id: int
    name: str
    serving_size: int
    recipe_count: int
    recipes: List[Recipe]
    shopping_list: List[ShoppingListItem]
    created_at: datetime
    rating: Optional[int] = None
    notes: str

    class Config:
        from_attributes = True


# Task Status Schemas
class TaskStatus(str, Enum):
    PENDING = "pending"
    GENERATING_RECIPES = "generating_recipes"
    GENERATING_IMAGES = "generating_images"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationTaskResponse(BaseModel):
    id: int
    status: TaskStatus
    progress: int
    current_step: str
    meal_plan_id: Optional[int] = None
    error_message: str
    created_at: datetime

    class Config:
        from_attributes = True


# Export Schemas
class PDFExportRequest(BaseModel):
    recipes: List[Dict[str, Any]]
    shopping_list: List[Dict[str, Any]]
    liked_foods: List[str] = []
    disliked_foods: List[str] = []
    serving_size: int = 4


# User Preferences Update
class UserPreferencesUpdate(BaseModel):
    liked_foods: Optional[List[str]] = None
    disliked_foods: Optional[List[str]] = None
    must_use_ingredients: Optional[List[str]] = None


# Recipe Rating Schemas
class RecipeRatingCreate(BaseModel):
    recipe_index: int
    recipe_title: str
    rating: int  # 1-5
    notes: Optional[str] = ""


class RecipeRatingResponse(BaseModel):
    id: int
    recipe_index: int
    recipe_title: str
    rating: int
    notes: str
    created_at: datetime

    class Config:
        from_attributes = True