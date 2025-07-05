from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timezone
from typing import List, Dict, Any

from .models import User, MealPlan, RecipeRating, RecipeHistory
from ..models.schemas import UserCreate, MealPlanCreate

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# User utilities
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        name=user.name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

# Meal plan utilities
def create_meal_plan(db: Session, meal_plan: MealPlanCreate, user_id: int):
    db_meal_plan = MealPlan(
        user_id=user_id,
        name=meal_plan.name,
        serving_size=meal_plan.serving_size,
        recipe_count=meal_plan.recipe_count,
        recipes_json=meal_plan.recipes_json,
        shopping_list_json=meal_plan.shopping_list_json,
        liked_foods_snapshot=meal_plan.liked_foods_snapshot,
        disliked_foods_snapshot=meal_plan.disliked_foods_snapshot
    )
    db.add(db_meal_plan)
    db.commit()
    db.refresh(db_meal_plan)
    return db_meal_plan

def get_user_meal_plans(db: Session, user_id: int, limit: int = 10):
    return db.query(MealPlan).filter(MealPlan.user_id == user_id).order_by(MealPlan.created_at.desc()).limit(limit).all()

# Recipe rating utilities
def get_recipe_rating(db: Session, user_id: int, meal_plan_id: int, recipe_index: int):
    """Get a specific recipe rating"""
    return db.query(RecipeRating).filter(
        RecipeRating.user_id == user_id,
        RecipeRating.meal_plan_id == meal_plan_id,
        RecipeRating.recipe_index == recipe_index
    ).first()

def create_or_update_recipe_rating(db: Session, user_id: int, meal_plan_id: int, recipe_index: int, recipe_title: str, rating: int, notes: str = ""):
    """Create or update a recipe rating"""
    existing_rating = get_recipe_rating(db, user_id, meal_plan_id, recipe_index)
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating
        existing_rating.notes = notes
        existing_rating.updated_at = datetime.now(timezone.utc)
    else:
        # Create new rating
        new_rating = RecipeRating(
            user_id=user_id,
            meal_plan_id=meal_plan_id,
            recipe_index=recipe_index,
            recipe_title=recipe_title,
            rating=rating,
            notes=notes
        )
        db.add(new_rating)
    
    db.commit()
    return existing_rating if existing_rating else new_rating

def get_meal_plan_recipe_ratings(db: Session, user_id: int, meal_plan_id: int):
    """Get all recipe ratings for a specific meal plan"""
    return db.query(RecipeRating).filter(
        RecipeRating.user_id == user_id,
        RecipeRating.meal_plan_id == meal_plan_id
    ).order_by(RecipeRating.recipe_index).all()

def get_user_recipe_ratings(db: Session, user_id: int, limit: int = 100):
    """Get all recipe ratings for a user"""
    return db.query(RecipeRating).filter(
        RecipeRating.user_id == user_id
    ).order_by(RecipeRating.updated_at.desc()).limit(limit).all()

# Recipe History utilities
def create_recipe_signature(recipe: Dict[str, Any], cooking_method: str, spice_profile: str, sauce_base: str, cuisine_inspiration: str) -> str:
    """Create a unique signature for a recipe based on key characteristics"""
    # Create a signature from key elements
    name = recipe.get("name", "").lower().strip()
    main_ingredients = []
    
    # Extract main ingredients (protein and key items)
    ingredients = recipe.get("ingredients", [])
    for ingredient in ingredients[:5]:  # Focus on first 5 main ingredients
        if isinstance(ingredient, dict):
            item = ingredient.get("item", "").lower().strip()
        else:
            item = str(ingredient).lower().strip()
        if item:
            main_ingredients.append(item)
    
    # Create signature from cooking method, spices, and main ingredients
    signature_parts = [
        cooking_method.split()[0] if cooking_method else "",  # First word of method
        spice_profile.split()[0] if spice_profile else "",    # First word of spice
        sauce_base.split()[0] if sauce_base else "",          # First word of sauce
        "-".join(main_ingredients[:3])                        # Top 3 ingredients
    ]
    
    return "|".join(filter(None, signature_parts)).lower()

def save_recipe_to_history(db: Session, user_id: int, recipe: Dict[str, Any], cooking_method: str, spice_profile: str, sauce_base: str, cuisine_inspiration: str):
    """Save a recipe to user's history for future avoidance"""
    try:
        # Extract main ingredients
        main_ingredients = []
        ingredients = recipe.get("ingredients", [])
        for ingredient in ingredients:
            if isinstance(ingredient, dict):
                item = ingredient.get("item", "")
            else:
                item = str(ingredient)
            if item:
                main_ingredients.append(item.strip())
        
        # Create signature
        signature = create_recipe_signature(recipe, cooking_method, spice_profile, sauce_base, cuisine_inspiration)
        
        # Save to history
        history_entry = RecipeHistory(
            user_id=user_id,
            recipe_name=recipe.get("name", "Unknown Recipe"),
            recipe_signature=signature,
            cooking_method=cooking_method,
            spice_profile=spice_profile,
            sauce_base=sauce_base,
            cuisine_inspiration=cuisine_inspiration,
            main_ingredients=", ".join(main_ingredients[:10])  # Store up to 10 ingredients
        )
        
        db.add(history_entry)
        db.commit()
        
        # Clean up old history (keep only last 30 recipes per user)
        cleanup_old_recipe_history(db, user_id)
        
    except Exception as e:
        print(f"Error saving recipe to history: {e}")
        db.rollback()

def cleanup_old_recipe_history(db: Session, user_id: int, keep_count: int = 30):
    """Keep only the most recent recipes in history"""
    try:
        # Get all history entries for user, ordered by newest first
        all_entries = db.query(RecipeHistory).filter(
            RecipeHistory.user_id == user_id
        ).order_by(RecipeHistory.created_at.desc()).all()
        
        # If we have more than keep_count, delete the oldest ones
        if len(all_entries) > keep_count:
            entries_to_delete = all_entries[keep_count:]
            for entry in entries_to_delete:
                db.delete(entry)
            db.commit()
            print(f"Cleaned up {len(entries_to_delete)} old recipe history entries for user {user_id}")
            
    except Exception as e:
        print(f"Error cleaning up recipe history: {e}")
        db.rollback()

def get_user_recipe_history(db: Session, user_id: int, limit: int = 30):
    """Get user's recent recipe history"""
    return db.query(RecipeHistory).filter(
        RecipeHistory.user_id == user_id
    ).order_by(RecipeHistory.created_at.desc()).limit(limit).all()

def check_recipe_similarity(db: Session, user_id: int, recipe: Dict[str, Any], cooking_method: str, spice_profile: str, sauce_base: str, cuisine_inspiration: str, similarity_threshold: float = 0.7) -> bool:
    """Check if a recipe is too similar to recent user history"""
    try:
        # Get recent recipe history
        recent_recipes = get_user_recipe_history(db, user_id, 30)
        
        if not recent_recipes:
            return False  # No history, recipe is unique
        
        # Create signature for current recipe
        current_signature = create_recipe_signature(recipe, cooking_method, spice_profile, sauce_base, cuisine_inspiration)
        current_name = recipe.get("name", "").lower()
        
        # Check against recent recipes
        for historical_recipe in recent_recipes:
            # Check exact signature match
            if historical_recipe.recipe_signature == current_signature:
                print(f"⚠️ Recipe signature matches previous: {historical_recipe.recipe_name}")
                return True
            
            # Check name similarity (fuzzy match)
            historical_name = historical_recipe.recipe_name.lower()
            if historical_name and current_name:
                # Simple word overlap check
                current_words = set(current_name.split())
                historical_words = set(historical_name.split())
                if len(current_words & historical_words) >= 2:  # 2+ words overlap
                    print(f"⚠️ Recipe name too similar to previous: {historical_recipe.recipe_name}")
                    return True
            
            # Check cooking method + spice combination similarity
            if (historical_recipe.cooking_method == cooking_method and 
                historical_recipe.spice_profile == spice_profile):
                print(f"⚠️ Cooking method + spice combination matches previous recipe")
                return True
        
        return False  # Recipe is sufficiently unique
        
    except Exception as e:
        print(f"Error checking recipe similarity: {e}")
        return False  # Default to allowing recipe if check fails