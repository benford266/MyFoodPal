"""
Database Models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

Base = declarative_base()


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    liked_foods = Column(Text, default="")  # Comma-separated list
    disliked_foods = Column(Text, default="")  # Comma-separated list
    must_use_ingredients = Column(Text, default="")  # Comma-separated list
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    meal_plans = relationship("MealPlan", back_populates="user")


class MealPlan(Base):
    """Meal plan model"""
    __tablename__ = "meal_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, default="Meal Plan")
    serving_size = Column(Integer, default=4)
    recipe_count = Column(Integer, default=5)
    recipes_json = Column(Text, nullable=False)  # JSON string of recipes
    shopping_list_json = Column(Text, nullable=False)  # JSON string of shopping list
    liked_foods_snapshot = Column(Text, default="")  # Preferences snapshot
    disliked_foods_snapshot = Column(Text, default="")
    must_use_ingredients_snapshot = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    rating = Column(Integer, default=None)  # 1-5 star rating
    notes = Column(Text, default="")
    
    # Relationships
    user = relationship("User", back_populates="meal_plans")
    recipe_ratings = relationship("RecipeRating", back_populates="meal_plan")


class RecipeRating(Base):
    """Recipe rating model"""
    __tablename__ = "recipe_ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meal_plan_id = Column(Integer, ForeignKey("meal_plans.id"), nullable=False)
    recipe_index = Column(Integer, nullable=False)  # 0-based index
    recipe_title = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User")
    meal_plan = relationship("MealPlan", back_populates="recipe_ratings")


class RecipeHistory(Base):
    """Recipe history for similarity tracking"""
    __tablename__ = "recipe_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipe_name = Column(String, nullable=False)
    recipe_signature = Column(String, nullable=False)
    cooking_method = Column(String, nullable=False)
    spice_profile = Column(String, nullable=False)
    sauce_base = Column(String, nullable=False)
    cuisine_inspiration = Column(String, nullable=False)
    main_ingredients = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User")


class GenerationTaskStatus(enum.Enum):
    """Task status enum"""
    PENDING = "pending"
    GENERATING_RECIPES = "generating_recipes"
    GENERATING_IMAGES = "generating_images"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationTask(Base):
    """Background task tracking for recipe generation"""
    __tablename__ = "generation_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(GenerationTaskStatus), default=GenerationTaskStatus.PENDING)
    progress = Column(Integer, default=0)  # 0-100 percentage
    current_step = Column(String, default="")
    
    # Generation parameters
    recipe_count = Column(Integer, default=5)
    serving_size = Column(Integer, default=4)
    liked_foods = Column(Text, default="")
    disliked_foods = Column(Text, default="")
    must_use_ingredients = Column(Text, default="")
    
    # Results
    meal_plan_id = Column(Integer, ForeignKey("meal_plans.id"), nullable=True)
    error_message = Column(Text, default="")
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User")
    meal_plan = relationship("MealPlan")