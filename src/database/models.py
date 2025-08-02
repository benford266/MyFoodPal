from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime, timezone
import enum

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    liked_foods = Column(Text, default="")  # Comma-separated list
    disliked_foods = Column(Text, default="")  # Comma-separated list
    must_use_ingredients = Column(Text, default="")  # Comma-separated list of ingredients that must be used
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    
    # Relationship to meal plans
    meal_plans = relationship("MealPlan", back_populates="user")

class MealPlan(Base):
    __tablename__ = "meal_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, default="Meal Plan")
    serving_size = Column(Integer, default=4)
    recipe_count = Column(Integer, default=5)
    recipes_json = Column(Text, nullable=False)  # JSON string of recipes
    shopping_list_json = Column(Text, nullable=False)  # JSON string of shopping list
    liked_foods_snapshot = Column(Text, default="")  # Snapshot of preferences at generation time
    disliked_foods_snapshot = Column(Text, default="")
    must_use_ingredients_snapshot = Column(Text, default="")  # Snapshot of must-use ingredients at generation time
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    rating = Column(Integer, default=None)  # 1-5 star rating
    notes = Column(Text, default="")  # User notes about this meal plan
    
    # Relationship to user
    user = relationship("User", back_populates="meal_plans")
    # Relationship to recipe ratings
    recipe_ratings = relationship("RecipeRating", back_populates="meal_plan")

class RecipeRating(Base):
    __tablename__ = "recipe_ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meal_plan_id = Column(Integer, ForeignKey("meal_plans.id"), nullable=False)
    recipe_index = Column(Integer, nullable=False)  # 0-based index of recipe in meal plan
    recipe_title = Column(String, nullable=False)  # Store recipe title for reference
    rating = Column(Integer, nullable=False)  # 1-5 star rating
    notes = Column(Text, default="")  # User notes about this specific recipe
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User")
    meal_plan = relationship("MealPlan", back_populates="recipe_ratings")

class RecipeHistory(Base):
    __tablename__ = "recipe_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipe_name = Column(String, nullable=False)  # Recipe name for quick lookup
    recipe_signature = Column(String, nullable=False)  # Unique signature of key elements
    cooking_method = Column(String, nullable=False)  # Track cooking method used
    spice_profile = Column(String, nullable=False)  # Track spice combination used
    sauce_base = Column(String, nullable=False)  # Track sauce type used
    cuisine_inspiration = Column(String, nullable=False)  # Track cultural inspiration
    main_ingredients = Column(Text, nullable=False)  # Key ingredients as comma-separated
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User")

class GenerationTaskStatus(enum.Enum):
    PENDING = "pending"
    GENERATING_RECIPES = "generating_recipes"
    GENERATING_IMAGES = "generating_images"
    COMPLETED = "completed"
    FAILED = "failed"

class GenerationTask(Base):
    __tablename__ = "generation_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(GenerationTaskStatus), default=GenerationTaskStatus.PENDING)
    progress = Column(Integer, default=0)  # 0-100 percentage
    current_step = Column(String, default="")  # Current operation description
    
    # Generation parameters
    recipe_count = Column(Integer, default=5)
    serving_size = Column(Integer, default=4)
    liked_foods = Column(Text, default="")
    disliked_foods = Column(Text, default="")
    must_use_ingredients = Column(Text, default="")
    
    # Results (when completed)
    meal_plan_id = Column(Integer, ForeignKey("meal_plans.id"), nullable=True)
    error_message = Column(Text, default="")
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User")
    meal_plan = relationship("MealPlan")