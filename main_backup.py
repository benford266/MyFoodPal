from fastapi import FastAPI, Response, Depends, HTTPException, status
from nicegui import ui, app
import httpx
from typing import List, Dict, Any, Optional
import json
import os
import re
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime, timezone
import io
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import sqlite3

# Load environment variables
load_dotenv()

# Configuration - Set via environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://192.168.4.170:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "ALIENTELLIGENCE/recipemaker")

# Database setup
DATABASE_URL = "sqlite:///./foodpal.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# FastAPI app
fastapi_app = FastAPI()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    liked_foods = Column(Text, default="")  # Comma-separated list
    disliked_foods = Column(Text, default="")  # Comma-separated list
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

# Pydantic models for API
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    liked_foods: str = ""
    disliked_foods: str = ""

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    liked_foods: str
    disliked_foods: str
    created_at: datetime

class MealPlanCreate(BaseModel):
    name: str = "Meal Plan"
    serving_size: int = 4
    recipe_count: int = 5
    recipes_json: str
    shopping_list_json: str
    liked_foods_snapshot: str = ""
    disliked_foods_snapshot: str = ""

class MealPlanResponse(BaseModel):
    id: int
    name: str
    serving_size: int
    recipe_count: int
    created_at: datetime
    rating: Optional[int]
    notes: str

# Create tables
Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Password utilities
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
        name=user.name,
        liked_foods=user.liked_foods,
        disliked_foods=user.disliked_foods
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

def generate_shopping_list(recipes: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Generate a consolidated shopping list from multiple recipes"""
    ingredient_totals = {}
    
    for recipe in recipes:
        if "ingredients" in recipe and isinstance(recipe["ingredients"], list):
            for ingredient in recipe["ingredients"]:
                if isinstance(ingredient, dict) and "item" in ingredient:
                    item_name = ingredient["item"].lower().strip()
                    quantity = ingredient.get("quantity", "")
                    unit = ingredient.get("unit", "")
                    
                    # Simple aggregation by item name
                    if item_name in ingredient_totals:
                        # For now, just append quantities (could be enhanced with unit conversion)
                        existing = ingredient_totals[item_name]
                        if existing["unit"] == unit:
                            try:
                                existing_qty = float(existing["quantity"])
                                new_qty = float(quantity)
                                ingredient_totals[item_name]["quantity"] = str(existing_qty + new_qty)
                            except (ValueError, TypeError):
                                ingredient_totals[item_name]["quantity"] = f"{existing['quantity']}, {quantity}"
                        else:
                            ingredient_totals[item_name]["quantity"] = f"{existing['quantity']} {existing['unit']}, {quantity} {unit}"
                            ingredient_totals[item_name]["unit"] = ""
                    else:
                        ingredient_totals[item_name] = {
                            "item": ingredient["item"],
                            "quantity": quantity,
                            "unit": unit
                        }
    
    return list(ingredient_totals.values())

# Session management functions
def get_current_user():
    """Get the current user from session storage"""
    return app.storage.user.get('current_user', None)

def set_current_user(user):
    """Set the current user in session storage"""
    if user:
        # Store user data as a dictionary to avoid SQLAlchemy session issues
        user_data = {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'liked_foods': user.liked_foods,
            'disliked_foods': user.disliked_foods,
            'created_at': user.created_at.isoformat(),
            'is_active': user.is_active
        }
        app.storage.user['current_user'] = user_data
    else:
        app.storage.user['current_user'] = None

def clear_current_user():
    """Clear the current user from session storage"""
    app.storage.user['current_user'] = None

# Theme management
class ThemeManager:
    def __init__(self):
        self.is_dark = self.get_system_theme()
    
    def get_system_theme(self) -> bool:
        """Detect system theme preference"""
        # For now, default to light mode. In production, could use browser API
        return False
    
    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.apply_theme()
    
    def apply_theme(self):
        """Apply theme to the UI"""
        if self.is_dark:
            ui.add_head_html('<style>:root { color-scheme: dark; }</style>')
        else:
            ui.add_head_html('<style>:root { color-scheme: light; }</style>')

theme_manager = ThemeManager()

# Data storage (in production, use a proper database)
user_preferences = {
    "liked_foods": [],
    "disliked_foods": []
}

class RecipeGenerator:
    def __init__(self, ollama_url: str, model: str):
        self.ollama_url = ollama_url
        self.model = model
    
    async def generate_single_recipe(self, recipe_number: int, liked_foods: List[str], disliked_foods: List[str], 
                                   existing_ingredients: List[str] = None, progress_callback=None, total_recipes: int = 5, serving_size: int = 4, used_carbs: List[str] = None) -> Dict[str, Any]:
        """Generate a single recipe, optionally using existing ingredients"""
        
        existing_ingredients_text = ""
        if existing_ingredients:
            existing_ingredients_text = f"""
        SHARED INGREDIENTS TO USE (if possible): {', '.join(existing_ingredients)}
        Try to incorporate some of these ingredients to minimize shopping."""
        
        carb_variety_text = ""
        if used_carbs:
            carb_variety_text = f"""
        CARBOHYDRATE VARIETY REQUIREMENT:
        These carbohydrates have already been used in other recipes: {', '.join(used_carbs)}
        Please choose a DIFFERENT carbohydrate base for this recipe to add variety.
        Carbohydrate options include: rice, pasta, potatoes, quinoa, bulgur, couscous, polenta, bread, noodles, barley, sweet potatoes, lentils, chickpeas, beans, or other grains/starches."""
        
        prompt = f"""
        Generate 1 dinner recipe (Recipe #{recipe_number} of {total_recipes}).

        User preferences:
        LIKES: {', '.join(liked_foods)}
        DISLIKES: {', '.join(disliked_foods)}
        SERVING SIZE: {serving_size} people
        {existing_ingredients_text}
        {carb_variety_text}
        
        REQUIREMENTS:
        - Generate exactly 1 dinner recipe
        - Recipe serves {serving_size} people
        - Scale all ingredient quantities for {serving_size} servings
        - Include prep time and cook time
        - Provide ingredient list with quantities scaled for {serving_size} people
        - Use METRIC UNITS ONLY (grams, kilograms, milliliters, liters, etc.)
        - Include cooking instructions with metric temperatures (Celsius)
        - Make it different from typical recipes
        
        RESPONSE FORMAT - Return valid JSON object (not array):
        {{
            "name": "Recipe Name",
            "prep_time": "15 minutes",
            "cook_time": "30 minutes", 
            "servings": {serving_size},
            "ingredients": [
                {{"item": "ingredient name", "quantity": "500", "unit": "g"}},
                {{"item": "another ingredient", "quantity": "250", "unit": "ml"}}
            ],
            "instructions": ["Step 1 description", "Step 2 description", "Step 3 description"]
        }}
        
        Return only valid JSON - no additional text."""
        
        try:
            if progress_callback:
                await progress_callback(f"Generating recipe {recipe_number}/{total_recipes}...")
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=120.0  # Shorter timeout for single recipe
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return parse_recipe_response(result['response'], recipe_number, serving_size)
                else:
                    return {"error": f"Ollama API error for recipe {recipe_number}: {response.status_code}"}
        
        except Exception as e:
            return {"error": f"Connection error for recipe {recipe_number}: {str(e)}"}

    async def generate_recipes(self, liked_foods: List[str], disliked_foods: List[str], recipe_count: int = 5, serving_size: int = 4, progress_callback=None) -> List[Dict[str, Any]]:
        """Generate specified number of recipes one at a time, sharing ingredients where possible and ensuring carbohydrate variety"""
        recipes = []
        all_ingredients = []
        used_carbohydrates = []
        
        # Common carbohydrate ingredients to track for variety
        carb_keywords = ['rice', 'pasta', 'noodle', 'potato', 'quinoa', 'bulgur', 'couscous', 'polenta', 'bread', 'barley', 'sweet potato', 'lentil', 'chickpea', 'bean', 'flour', 'wheat', 'oat', 'corn', 'maize']
        
        for i in range(1, recipe_count + 1):  # Generate specified number of recipes
            # After first recipe, pass existing ingredients to encourage sharing
            existing_ingredients = all_ingredients if i > 1 else None
            
            # Pass used carbohydrates to encourage variety (from second recipe onwards)
            used_carbs = used_carbohydrates if i > 1 else None
            
            recipe = await self.generate_single_recipe(
                i, liked_foods, disliked_foods, existing_ingredients, progress_callback, recipe_count, serving_size, used_carbs
            )
            
            if "error" in recipe:
                # If one recipe fails, continue with others
                recipes.append(recipe)
                continue
                
            recipes.append(recipe)
            
            # Extract ingredients from this recipe for next recipes
            if "ingredients" in recipe:
                for ingredient in recipe["ingredients"]:
                    item = ingredient.get("item", "").lower()
                    if item and item not in [ing.lower() for ing in all_ingredients]:
                        all_ingredients.append(ingredient.get("item", ""))
                    
                    # Check if this ingredient is a carbohydrate and track it for variety
                    for carb_keyword in carb_keywords:
                        if carb_keyword in item and item not in [carb.lower() for carb in used_carbohydrates]:
                            used_carbohydrates.append(ingredient.get("item", ""))
                            break  # Only add once per ingredient
        
        return recipes

def clean_json_response(response_text: str) -> str:
    """Clean and extract JSON from LLM response"""
    # Remove common prefixes/suffixes
    response_text = response_text.strip()
    
    # Remove markdown code blocks
    response_text = re.sub(r'^```json\s*', '', response_text, flags=re.MULTILINE)
    response_text = re.sub(r'^```\s*$', '', response_text, flags=re.MULTILINE)
    
    # Remove any text before the first {
    start_idx = response_text.find('{')
    if start_idx != -1:
        response_text = response_text[start_idx:]
    
    # Remove any text after the last }
    end_idx = response_text.rfind('}')
    if end_idx != -1:
        response_text = response_text[:end_idx + 1]
    
    # Fix common JSON issues
    response_text = response_text.replace("\\'", "'")  # Fix escaped quotes
    response_text = re.sub(r',\s*}', '}', response_text)  # Remove trailing commas
    response_text = re.sub(r',\s*]', ']', response_text)  # Remove trailing commas in arrays
    
    return response_text

def parse_recipe_response(response_text: str, recipe_number: int, serving_size: int = 4) -> Dict[str, Any]:
    """Parse recipe response with multiple fallback methods"""
    
    # Method 1: Direct JSON parsing
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Method 2: Clean and try again
    try:
        cleaned = clean_json_response(response_text)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Method 3: Extract key information manually
    try:
        # Extract name
        name_match = re.search(r'"name"\s*:\s*"([^"]+)"', response_text)
        name = name_match.group(1) if name_match else f"Recipe {recipe_number}"
        
        # Extract times
        prep_match = re.search(r'"prep_time"\s*:\s*"([^"]+)"', response_text)
        prep_time = prep_match.group(1) if prep_match else "20 minutes"
        
        cook_match = re.search(r'"cook_time"\s*:\s*"([^"]+)"', response_text)
        cook_time = cook_match.group(1) if cook_match else "30 minutes"
        
        # Create fallback recipe
        return {
            "name": name,
            "prep_time": prep_time,
            "cook_time": cook_time,
            "servings": serving_size,
            "ingredients": [
                {"item": "main ingredient", "quantity": "500", "unit": "g"},
                {"item": "vegetables", "quantity": "200", "unit": "g"},
                {"item": "seasoning", "quantity": "5", "unit": "ml"}
            ],
            "instructions": [
                "Prepare ingredients",
                "Cook main ingredient",
                "Add vegetables and seasonings",
                "Serve hot"
            ],
            "_note": "Fallback recipe - original response had parsing issues"
        }
    except Exception:
        pass
    
    # Method 4: Return error with raw response
    return {
        "error": f"Failed to parse recipe {recipe_number}",
        "raw_response": response_text[:500] + "..." if len(response_text) > 500 else response_text
    }

def generate_pdf_export(recipes: List[Dict[str, Any]], shopping_list: List[Dict[str, str]], 
                        liked_foods: List[str], disliked_foods: List[str], serving_size: int) -> bytes:
    """Generate a PDF with recipes and shopping list"""
    
    # Create PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, 
                          topMargin=72, bottomMargin=72)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#059669')
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=20,
        textColor=colors.HexColor('#374151')
    )
    
    recipe_title_style = ParagraphStyle(
        'RecipeTitle',
        parent=styles['Heading3'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#059669')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        leftIndent=20
    )
    
    # Build PDF content
    story = []
    
    # Title page
    story.append(Paragraph("🍽️ FoodPal Meal Plan", title_style))
    story.append(Spacer(1, 20))
    
    # Meal plan info
    current_date = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(f"Generated on: {current_date}", styles['Normal']))
    story.append(Paragraph(f"Serving size: {serving_size} people", styles['Normal']))
    story.append(Paragraph(f"Number of recipes: {len(recipes)}", styles['Normal']))
    story.append(Spacer(1, 30))
    
    # Food preferences
    if liked_foods or disliked_foods:
        story.append(Paragraph("Food Preferences", subtitle_style))
        if liked_foods:
            story.append(Paragraph(f"<b>Likes:</b> {', '.join(liked_foods)}", styles['Normal']))
        if disliked_foods:
            story.append(Paragraph(f"<b>Avoids:</b> {', '.join(disliked_foods)}", styles['Normal']))
        story.append(Spacer(1, 30))
    
    # Shopping List
    if shopping_list:
        story.append(Paragraph("🛒 Shopping List", subtitle_style))
        
        # Create table for shopping list
        shopping_data = [['Quantity', 'Unit', 'Item']]
        for item in shopping_list:
            shopping_data.append([
                item.get('quantity', ''),
                item.get('unit', ''),
                item.get('item', '')
            ])
        
        shopping_table = Table(shopping_data, colWidths=[1*inch, 1*inch, 4*inch])
        shopping_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
        ]))
        
        story.append(shopping_table)
        story.append(PageBreak())
    
    # Recipes
    story.append(Paragraph("📖 Recipes", subtitle_style))
    
    for i, recipe in enumerate(recipes, 1):
        if "error" in recipe:
            continue
            
        # Recipe title
        recipe_name = recipe.get('name', f'Recipe {i}')
        story.append(Paragraph(f"{i}. {recipe_name}", recipe_title_style))
        
        # Recipe info
        prep_time = recipe.get('prep_time', 'N/A')
        cook_time = recipe.get('cook_time', 'N/A')
        servings = recipe.get('servings', serving_size)
        
        info_text = f"<b>Prep:</b> {prep_time} | <b>Cook:</b> {cook_time} | <b>Serves:</b> {servings}"
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Ingredients
        if 'ingredients' in recipe and recipe['ingredients']:
            story.append(Paragraph("<b>Ingredients:</b>", styles['Normal']))
            for ingredient in recipe['ingredients']:
                quantity = ingredient.get('quantity', '')
                unit = ingredient.get('unit', '')
                item = ingredient.get('item', '')
                ingredient_text = f"• {quantity} {unit} {item}".strip()
                story.append(Paragraph(ingredient_text, normal_style))
            story.append(Spacer(1, 10))
        
        # Instructions
        if 'instructions' in recipe and recipe['instructions']:
            story.append(Paragraph("<b>Instructions:</b>", styles['Normal']))
            for j, instruction in enumerate(recipe['instructions'], 1):
                instruction_text = f"{j}. {instruction}"
                story.append(Paragraph(instruction_text, normal_style))
            story.append(Spacer(1, 20))
        
        # Add page break between recipes (except last one)
        if i < len([r for r in recipes if "error" not in r]):
            story.append(PageBreak())
    
    # Build PDF
    doc.build(story)
    
    # Get PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

# FastAPI endpoint for PDF export
@fastapi_app.post("/export-pdf")
async def export_pdf(data: dict):
    """Export meal plan to PDF"""
    try:
        recipes = data.get('recipes', [])
        shopping_list = data.get('shopping_list', [])
        liked_foods = data.get('liked_foods', [])
        disliked_foods = data.get('disliked_foods', [])
        serving_size = data.get('serving_size', 4)
        
        pdf_data = generate_pdf_export(recipes, shopping_list, liked_foods, disliked_foods, serving_size)
        
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=FoodPal_Meal_Plan_{datetime.now().strftime('%Y%m%d')}.pdf"}
        )
    except Exception as e:
        return {"error": str(e)}

recipe_generator = RecipeGenerator(OLLAMA_BASE_URL, OLLAMA_MODEL)

def generate_shopping_list(recipes: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Combine ingredients from all recipes into a shopping list"""
    shopping_list = {}
    
    for recipe in recipes:
        if "ingredients" in recipe and recipe["ingredients"]:
            for ingredient in recipe["ingredients"]:
                item = ingredient.get("item", "")
                quantity = ingredient.get("quantity", "")
                unit = ingredient.get("unit", "")
                
                if item:
                    key = item.lower()
                    if key in shopping_list:
                        # For simplicity, just add quantities (in production, would need unit conversion)
                        shopping_list[key]["quantity"] += f" + {quantity}"
                    else:
                        shopping_list[key] = {
                            "item": item,
                            "quantity": quantity,
                            "unit": unit
                        }
    
    return list(shopping_list.values())

def get_theme_classes():
    """Get theme-appropriate CSS classes with modern design system"""
    if theme_manager.is_dark:
        return {
            'bg_primary': 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900',
            'bg_secondary': 'bg-slate-800/50 backdrop-blur-xl',
            'bg_accent': 'bg-slate-700/80',
            'text_primary': 'text-slate-100',
            'text_secondary': 'text-slate-400',
            'text_accent': 'text-slate-300',
            'border': 'border-slate-600/50',
            'border_accent': 'border-slate-500/30',
            'button_primary': 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 shadow-lg hover:shadow-emerald-500/25',
            'button_secondary': 'bg-slate-700 hover:bg-slate-600 border border-slate-600',
            'card': 'bg-slate-800/40 backdrop-blur-xl border-slate-700/50 shadow-xl',
            'card_hover': 'hover:bg-slate-800/60 hover:border-slate-600/50 hover:shadow-2xl',
            'input_bg': 'bg-slate-800/50 border-slate-600/50 text-slate-100 focus:border-emerald-400/50 focus:ring-emerald-400/20',
            'success_bg': 'bg-gradient-to-r from-emerald-900/30 to-teal-900/30 border-emerald-500/30',
            'error_bg': 'bg-gradient-to-r from-red-900/30 to-rose-900/30 border-red-500/30',
            'gradient_text': 'bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent',
            'chip_bg': 'bg-slate-700/80 text-slate-200 border-slate-600/50'
        }
    else:
        return {
            'bg_primary': 'bg-gradient-to-br from-slate-50 via-white to-slate-100',
            'bg_secondary': 'bg-white/80 backdrop-blur-xl',
            'bg_accent': 'bg-slate-100/80',
            'text_primary': 'text-slate-900',
            'text_secondary': 'text-slate-600',
            'text_accent': 'text-slate-700',
            'border': 'border-slate-200/80',
            'border_accent': 'border-slate-300/50',
            'button_primary': 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 shadow-lg hover:shadow-emerald-500/25',
            'button_secondary': 'bg-white hover:bg-slate-50 border border-slate-300',
            'card': 'bg-white/70 backdrop-blur-xl border-slate-200/50 shadow-lg',
            'card_hover': 'hover:bg-white/90 hover:border-slate-300/50 hover:shadow-xl',
            'input_bg': 'bg-white/80 border-slate-300/80 text-slate-900 focus:border-emerald-400 focus:ring-emerald-400/20',
            'success_bg': 'bg-gradient-to-r from-emerald-50 to-teal-50 border-emerald-200',
            'error_bg': 'bg-gradient-to-r from-red-50 to-rose-50 border-red-200',
            'gradient_text': 'bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 bg-clip-text text-transparent',
            'chip_bg': 'bg-slate-100 text-slate-700 border-slate-200'
        }

@ui.page('/login')
def login_page():
    theme = get_theme_classes()
    
    # Add viewport and Material Icons
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    ui.add_head_html('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">')
    
    with ui.column().classes(f'min-h-screen {theme["bg_primary"]} {theme["text_primary"]} items-center justify-center p-4 sm:p-8'):
        with ui.card().classes(f'{theme["card"]} {theme["border"]} rounded-3xl p-6 sm:p-8 w-full max-w-md shadow-2xl'):
            # Logo and title with better spacing
            ui.html('<div class="text-6xl text-center mb-6">🍽️</div>')
            ui.html(f'<h1 class="text-2xl sm:text-3xl font-bold {theme["gradient_text"]} text-center mb-4">Welcome to FoodPal</h1>')
            ui.html(f'<p class="text-sm {theme["text_secondary"]} text-center mb-8">Your AI-powered recipe companion</p>')
            
            # Login/Register toggle
            is_login = {'value': True}
            
            # Toggle buttons container
            toggle_container = ui.row().classes('w-full mb-6')
            
            def set_login_mode():
                is_login['value'] = True
                update_form()
                update_buttons()
            
            def set_register_mode():
                is_login['value'] = False
                update_form()
                update_buttons()
            
            def update_buttons():
                toggle_container.clear()
                with toggle_container:
                    if is_login['value']:
                        # Login mode - login button active
                        ui.button('Login', on_click=set_login_mode).classes('flex-1 py-3 px-4 rounded-l-xl font-semibold').style(
                            'background-color: #059669; color: white; border: none; font-weight: 600; min-height: 48px;'
                        )
                        ui.button('Register', on_click=set_register_mode).classes('flex-1 py-3 px-4 rounded-r-xl font-semibold').style(
                            'background-color: white; color: #374151; border: 1px solid #d1d5db; font-weight: 600; min-height: 48px;'
                        )
                    else:
                        # Register mode - register button active
                        ui.button('Login', on_click=set_login_mode).classes('flex-1 py-3 px-4 rounded-l-xl font-semibold').style(
                            'background-color: white; color: #374151; border: 1px solid #d1d5db; font-weight: 600; min-height: 48px;'
                        )
                        ui.button('Register', on_click=set_register_mode).classes('flex-1 py-3 px-4 rounded-r-xl font-semibold').style(
                            'background-color: #059669; color: white; border: none; font-weight: 600; min-height: 48px;'
                        )
            
            # Form container
            form_container = ui.column().classes('w-full gap-4')
            
            def update_form():
                form_container.clear()
                with form_container:
                    if is_login['value']:
                        # Login form
                        
                        email_input = ui.input('Email', placeholder='your@email.com').classes(
                            f'{theme["input_bg"]} rounded-xl border-2 {theme["border"]} p-4 w-full'
                        )
                        password_input = ui.input('Password', password=True).classes(
                            f'{theme["input_bg"]} rounded-xl border-2 {theme["border"]} p-4 w-full'
                        )
                        
                        async def handle_login():
                            try:
                                db = next(get_db())
                                user = authenticate_user(db, email_input.value, password_input.value)
                                if user:
                                    set_current_user(user)
                                    ui.notify(f'Welcome back, {user.name}!', type='positive')
                                    ui.navigate.to('/')
                                else:
                                    ui.notify('Invalid email or password', type='negative')
                            except Exception as e:
                                ui.notify(f'Login failed: {str(e)}', type='negative')
                        
                        ui.button('Login', on_click=handle_login).classes(
                            f'{theme["button_primary"]} text-white w-full py-4 rounded-xl text-lg font-semibold'
                        )
                    
                    else:
                        # Register form
                        
                        name_input = ui.input('Full Name', placeholder='John Doe').classes(
                            f'{theme["input_bg"]} rounded-xl border-2 {theme["border"]} p-4 w-full'
                        )
                        email_input = ui.input('Email', placeholder='your@email.com').classes(
                            f'{theme["input_bg"]} rounded-xl border-2 {theme["border"]} p-4 w-full'
                        )
                        password_input = ui.input('Password', password=True).classes(
                            f'{theme["input_bg"]} rounded-xl border-2 {theme["border"]} p-4 w-full'
                        )
                        
                        async def handle_register():
                            try:
                                db = next(get_db())
                                # Check if user exists
                                if get_user_by_email(db, email_input.value):
                                    ui.notify('Email already registered', type='negative')
                                    return
                                
                                # Create user
                                user_data = UserCreate(
                                    email=email_input.value,
                                    password=password_input.value,
                                    name=name_input.value
                                )
                                user = create_user(db, user_data)
                                set_current_user(user)
                                ui.notify(f'Welcome to FoodPal, {user.name}!', type='positive')
                                ui.navigate.to('/')
                            except Exception as e:
                                ui.notify(f'Registration failed: {str(e)}', type='negative')
                        
                        ui.button('Create Account', on_click=handle_register).classes(
                            f'{theme["button_primary"]} text-white w-full py-4 rounded-xl text-lg font-semibold'
                        )
            
            # Initial form and button load
            update_buttons()
            update_form()

@ui.page('/')
def main_page():
    # Check if user is logged in
    current_user = get_current_user()
    if current_user is None:
        ui.navigate.to('/login')
        return
    
    theme = get_theme_classes()
    
    # Add viewport meta tag for proper mobile responsiveness
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    
    # Add Material Icons for proper dropdown arrows
    ui.add_head_html('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">')
    
    # Add sophisticated custom CSS with responsive design
    ui.add_head_html('''
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        * {
            font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
            box-sizing: border-box;
        }
        
        /* Force responsive behavior */
        .nicegui-content {
            width: 100% !important;
            max-width: none !important;
        }
        
        /* Enhanced dropdown styling */
        .q-select, .q-field {
            position: relative !important;
            z-index: 1000 !important;
            font-size: 16px !important;
        }
        
        .q-menu {
            z-index: 2000 !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.15) !important;
            border-radius: 12px !important;
        }
        
        .q-select .q-field__control {
            border-radius: 12px !important;
            min-height: 48px !important;
            padding: 8px 16px !important;
        }
        
        .q-select .q-field__native {
            font-size: 16px !important;
            font-weight: 500 !important;
        }
        
        .q-select .q-field__append {
            color: currentColor !important;
        }
        
        .q-item {
            padding: 12px 16px !important;
            font-size: 16px !important;
            border-radius: 8px !important;
            margin: 4px 8px !important;
        }
        
        .q-item:hover {
            background-color: rgba(16, 185, 129, 0.1) !important;
        }
        
        .material-icons {
            font-family: 'Material Icons' !important;
            font-weight: normal !important;
            font-style: normal !important;
            font-size: 24px !important;
            line-height: 1 !important;
            letter-spacing: normal !important;
            text-transform: none !important;
            display: inline-block !important;
            white-space: nowrap !important;
            word-wrap: normal !important;
            direction: ltr !important;
        }
        
        /* Responsive container */
        .responsive-container {
            width: 100%;
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 1rem;
        }
        
        @media (min-width: 640px) {
            .responsive-container {
                padding: 0 2rem;
            }
        }
        
        @media (min-width: 1024px) {
            .responsive-container {
                padding: 0 3rem;
            }
        }
        
        .recipe-card {
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            transform-style: preserve-3d;
            position: relative;
            overflow: hidden;
        }
        
        .recipe-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
        }
        
        .recipe-card:hover::before {
            opacity: 1;
        }
        
        .recipe-card:hover {
            transform: translateY(-8px) scale(1.02);
        }
        
        .glass-morphism {
            backdrop-filter: blur(16px) saturate(180%);
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.125);
        }
        
        .input-focus {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .input-focus:focus {
            transform: scale(1.02);
            box-shadow: 0 10px 25px rgba(16, 185, 129, 0.15);
        }
        
        .floating-button {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .floating-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }
        
        .floating-button:hover::before {
            left: 100%;
        }
        
        .floating-button:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 35px rgba(16, 185, 129, 0.4);
        }
        
        .progress-glow {
            animation: pulse-glow 2s infinite;
        }
        
        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 20px rgba(16, 185, 129, 0.3); }
            50% { box-shadow: 0 0 40px rgba(16, 185, 129, 0.6); }
        }
        
        .chip-modern {
            transition: all 0.2s ease;
        }
        
        .chip-modern:hover {
            transform: scale(1.05);
        }
        
        .hero-text {
            font-size: clamp(2rem, 8vw, 4rem);
            font-weight: 800;
            line-height: 1.1;
            letter-spacing: -0.02em;
        }
        
        .subtitle {
            font-size: clamp(1rem, 3vw, 1.25rem);
            font-weight: 400;
            line-height: 1.6;
        }
        
        .section-title {
            font-size: clamp(1.25rem, 4vw, 1.875rem);
            font-weight: 700;
            line-height: 1.3;
            letter-spacing: -0.01em;
        }
        
        /* Force responsive grid for recipe cards */
        .recipe-grid {
            display: grid !important;
            grid-template-columns: 1fr !important;
            gap: 1.5rem !important;
            width: 100% !important;
        }
        
        @media (min-width: 768px) {
            .recipe-grid {
                grid-template-columns: repeat(2, 1fr) !important;
                gap: 2rem !important;
            }
        }
        
        @media (min-width: 1200px) {
            .recipe-grid {
                grid-template-columns: repeat(3, 1fr) !important;
            }
        }
        
        /* Force responsive input layout */
        .input-grid {
            display: grid !important;
            grid-template-columns: 1fr !important;
            gap: 2rem !important;
            width: 100% !important;
        }
        
        @media (min-width: 768px) {
            .input-grid {
                grid-template-columns: 1fr 1fr !important;
            }
        }
        
        /* Enhanced mobile experience */
        @media (max-width: 767px) {
            .chip-modern {
                min-height: 44px;
                padding: 0.75rem 1rem;
                font-size: 14px;
            }
            
            .floating-button {
                min-height: 56px;
                font-size: 1.125rem;
                width: 100% !important;
            }
            
            .recipe-card {
                margin-bottom: 1rem;
                padding: 1rem !important;
            }
            
            .recipe-card:hover {
                transform: none;
            }
            
            /* Improve form inputs on mobile */
            .q-select .q-field__control {
                min-height: 52px !important;
                font-size: 16px !important;
            }
            
            textarea {
                font-size: 16px !important;
            }
            
            /* Better spacing on mobile */
            .section-title {
                font-size: 1.5rem !important;
            }
            
            .hero-text {
                font-size: 2.5rem !important;
            }
        }
        
        /* Improved focus states */
        .input-focus:focus {
            transform: scale(1.01);
            box-shadow: 0 8px 25px rgba(16, 185, 129, 0.15) !important;
            border-color: rgb(16, 185, 129) !important;
        }
        
        /* Better button animations */
        .floating-button {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
        }
        
        .floating-button:hover {
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
        }
        
        /* Force button text visibility - comprehensive fix */
        .q-btn .q-btn__content {
            color: inherit !important;
            font-weight: inherit !important;
            opacity: 1 !important;
        }
        
        .q-btn .q-btn__content .block {
            color: inherit !important;
            opacity: 1 !important;
        }
        
        /* Fix any button text visibility issues */
        button {
            color: inherit !important;
        }
        
        button span {
            color: inherit !important;
            opacity: 1 !important;
        }
        
        button .q-btn__content {
            color: inherit !important;
            opacity: 1 !important;
        }
        
        /* Specific override for login/register buttons */
        .bg-white button,
        .bg-white .q-btn,
        .bg-white .q-btn__content {
            color: #374151 !important;
        }
        
        .bg-emerald-600 button,
        .bg-emerald-600 .q-btn,
        .bg-emerald-600 .q-btn__content {
            color: white !important;
        }
        
        /* Hero section responsive adjustments */
        .hero-section {
            padding: clamp(2rem, 8vw, 4rem) 1rem;
        }
        
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 1rem;
        }
        
        @media (min-width: 640px) {
            .feature-grid {
                grid-template-columns: repeat(3, 1fr);
                gap: 2rem;
            }
        }
    </style>
    ''')
    
    # Main container with theme
    with ui.column().classes(f'min-h-screen {theme["bg_primary"]} {theme["text_primary"]} transition-all duration-300'):
        # Hero Header Section with responsive design
        with ui.column().classes('hero-section w-full items-center text-center responsive-container'):
            # App Logo/Title - responsive layout
            with ui.column().classes('items-center mb-6 lg:mb-8'):
                with ui.row().classes('items-center justify-center gap-2 sm:gap-4 mb-4'):
                    ui.html('<div class="text-4xl sm:text-6xl">🍽️</div>')
                    with ui.column().classes('items-center sm:items-start'):
                        ui.html(f'<h1 class="hero-text {theme["gradient_text"]} mb-0 text-center sm:text-left">FoodPal</h1>')
                        ui.html(f'<div class="text-xs sm:text-sm uppercase tracking-widest {theme["text_secondary"]} font-medium text-center sm:text-left">AI Recipe Generator</div>')
            
            # User header with logout and theme toggle
            with ui.row().classes('fixed top-4 right-4 sm:top-6 sm:right-6 z-50 gap-2'):
                # User info
                with ui.card().classes(f'{theme["card"]} {theme["border"]} rounded-full px-4 py-2 shadow-lg'):
                    with ui.row().classes('items-center gap-2'):
                        ui.html(f'<span class="text-sm font-medium {theme["text_primary"]}">👋 {current_user["name"]}</span>')
                
                # Meal history button
                ui.button(
                    '📈',
                    on_click=lambda: ui.navigate.to('/history')
                ).classes(f'{theme["card"]} {theme["border"]} rounded-full w-12 h-12 sm:w-14 sm:h-14 text-lg sm:text-xl shadow-lg transition-all duration-300 hover:scale-110')
                
                # Logout button
                def logout_handler():
                    clear_current_user()
                    ui.navigate.to('/login')
                
                ui.button(
                    '🚪',
                    on_click=logout_handler
                ).classes(f'{theme["card"]} {theme["border"]} rounded-full w-12 h-12 sm:w-14 sm:h-14 text-lg sm:text-xl shadow-lg transition-all duration-300 hover:scale-110')
                
                # Theme toggle
                def toggle_theme_handler():
                    theme_manager.toggle_theme()
                    ui.navigate.reload()
                
                ui.button(
                    '🌙' if not theme_manager.is_dark else '☀️',
                    on_click=toggle_theme_handler
                ).classes(f'{theme["card"]} {theme["border"]} rounded-full w-12 h-12 sm:w-14 sm:h-14 text-lg sm:text-xl shadow-lg transition-all duration-300 hover:scale-110')
            
            # Subtitle with responsive typography
            ui.html(f'''
                <p class="subtitle {theme["text_secondary"]} max-w-full sm:max-w-2xl mx-auto leading-relaxed px-4">
                    Create personalized dinner recipes tailored to your taste preferences, 
                    with smart ingredient optimization for efficient shopping.
                </p>
            ''')
            
            # Stats/Features row - responsive grid
            ui.html(f'''
                <div class="feature-grid mt-6 sm:mt-8 w-full max-w-md sm:max-w-none mx-auto">
                    <div class="flex flex-col items-center">
                        <div class="text-xl sm:text-2xl mb-2">🤖</div>
                        <span class="text-xs sm:text-sm {theme["text_secondary"]} font-medium text-center">AI-Powered</span>
                    </div>
                    <div class="flex flex-col items-center">
                        <div class="text-xl sm:text-2xl mb-2">🥗</div>
                        <span class="text-xs sm:text-sm {theme["text_secondary"]} font-medium text-center">Personalized</span>
                    </div>
                    <div class="flex flex-col items-center">
                        <div class="text-xl sm:text-2xl mb-2">🛒</div>
                        <span class="text-xs sm:text-sm {theme["text_secondary"]} font-medium text-center">Smart Shopping</span>
                    </div>
                </div>
            ''')
        
        # Main content container with responsive design
        with ui.column().classes('responsive-container pb-20'):
            # Preferences Section with improved layout
            with ui.card().classes(f'recipe-card {theme["card"]} {theme["border"]} rounded-3xl p-6 sm:p-8 w-full mb-8'):
                # Section header with better instructions
                ui.html(f'<h2 class="section-title {theme["text_primary"]} mb-4 text-center">🍽️ Your Food Preferences</h2>')
                ui.html(f'<p class="text-base {theme["text_secondary"]} text-center mb-8 max-w-2xl mx-auto">Help us create the perfect recipes by sharing what you love and what you prefer to avoid. Be as specific as you like!</p>')
                
                # Input grid with better responsive layout
                with ui.column().classes('w-full space-y-6 lg:space-y-0'):
                    with ui.row().classes('w-full gap-6 flex-col lg:flex-row'):
                        # Liked foods column
                        with ui.column().classes('flex-1 space-y-4'):
                            # Header with icon and explanation
                            with ui.card().classes(f'{theme["success_bg"]} {theme["border"]} rounded-xl p-4 mb-4'):
                                with ui.row().classes('items-center gap-3 mb-2'):
                                    ui.html('<div class="text-2xl">💚</div>')
                                    ui.html(f'<h3 class="text-xl font-bold {theme["text_primary"]} mb-0">Foods You Love</h3>')
                                ui.html(f'<p class="text-sm {theme["text_secondary"]} leading-relaxed">List ingredients, cuisines, flavors, or dishes you enjoy. Examples: chicken, Italian food, garlic, spicy, comfort food</p>')
                            
                            liked_input = ui.textarea(
                                placeholder='chicken, pasta, garlic, tomatoes, Italian cuisine, comfort food, spicy flavors...',
                                value=current_user["liked_foods"] if current_user else ''
                            ).classes(f'input-focus {theme["input_bg"]} rounded-xl border-2 {theme["border"]} p-4 min-h-[140px] text-base leading-relaxed placeholder:text-opacity-70 focus:ring-4 w-full transition-all duration-200')
                        
                        # Disliked foods column  
                        with ui.column().classes('flex-1 space-y-4'):
                            # Header with icon and explanation
                            with ui.card().classes(f'{theme["error_bg"]} {theme["border"]} rounded-xl p-4 mb-4'):
                                with ui.row().classes('items-center gap-3 mb-2'):
                                    ui.html('<div class="text-2xl">🚫</div>')
                                    ui.html(f'<h3 class="text-xl font-bold {theme["text_primary"]} mb-0">Foods to Avoid</h3>')
                                ui.html(f'<p class="text-sm {theme["text_secondary"]} leading-relaxed">List anything you don\'t like or can\'t eat. Examples: mushrooms, seafood, very spicy, nuts, dairy</p>')
                            
                            disliked_input = ui.textarea(
                                placeholder='mushrooms, seafood, very spicy food, nuts, dairy, cilantro...',
                                value=current_user["disliked_foods"] if current_user else ''
                            ).classes(f'input-focus {theme["input_bg"]} rounded-xl border-2 {theme["border"]} p-4 min-h-[140px] text-base leading-relaxed placeholder:text-opacity-70 focus:ring-4 w-full transition-all duration-200')
                
                # Recipe settings with improved layout
                with ui.column().classes('w-full max-w-4xl mx-auto mt-8 space-y-6'):
                    ui.html(f'<h3 class="text-xl font-bold {theme["text_primary"]} text-center mb-6">Recipe Settings</h3>')
                    
                    with ui.row().classes('w-full gap-6 flex-col sm:flex-row'):
                        # Recipe count
                        with ui.column().classes('flex-1 space-y-3'):
                            with ui.row().classes('items-center gap-3'):
                                ui.html('<div class="text-2xl">📊</div>')
                                ui.html(f'<h4 class="text-lg font-semibold {theme["text_primary"]} mb-0">How many recipes?</h4>')
                            
                            with ui.card().classes(f'{theme["input_bg"]} {theme["border"]} rounded-xl p-4'):
                                recipe_count_select = ui.select(
                                    options={
                                        1: '1 recipe - Quick test',
                                        3: '3 recipes - Weekend meals', 
                                        5: '5 recipes - Work week',
                                        7: '7 recipes - Full week',
                                        10: '10 recipes - Meal prep'
                                    },
                                    value=5,
                                    label=None
                                ).classes('w-full text-base').style('min-height: 48px; font-size: 16px;')
                        
                        # Serving size
                        with ui.column().classes('flex-1 space-y-3'):
                            with ui.row().classes('items-center gap-3'):
                                ui.html('<div class="text-2xl">👥</div>')
                                ui.html(f'<h4 class="text-lg font-semibold {theme["text_primary"]} mb-0">How many people?</h4>')
                            
                            with ui.card().classes(f'{theme["input_bg"]} {theme["border"]} rounded-xl p-4'):
                                serving_size_select = ui.select(
                                    options={
                                        1: '1 person - Solo meals',
                                        2: '2 people - Couple',
                                        4: '4 people - Family',
                                        6: '6 people - Large family',
                                        8: '8 people - Group meals',
                                        12: '12 people - Party/gathering'
                                    },
                                    value=4,
                                    label=None
                                ).classes('w-full text-base').style('min-height: 48px; font-size: 16px;')
            
            # Generate Button with improved design
            with ui.column().classes('w-full items-center mt-12 mb-12 space-y-4'):
                # Call to action text
                ui.html(f'<p class="text-lg {theme["text_secondary"]} text-center mb-4">Ready to discover your perfect recipes?</p>')
                
                # Generate button with better styling
                generate_button = ui.button(
                    '🚀 Generate My Recipes',
                    on_click=lambda: None  # Will be set later
                ).classes(f'floating-button {theme["button_primary"]} text-white text-xl font-bold py-6 px-12 rounded-2xl shadow-2xl transform transition-all duration-300 hover:scale-105 hover:shadow-3xl min-w-[280px]')
                
                # Helper text
                ui.html(f'<p class="text-sm {theme["text_secondary"]} text-center opacity-75">This may take a minute - we\'re crafting something special! ✨</p>')
            
            # Results Container
            result_container = ui.column().classes('w-full gap-6 mt-8')
        
            async def regenerate_recipe_at_index(recipe_index: int, liked_foods: list, disliked_foods: list, serving_size: int, current_recipes: list):
                """Regenerate a single recipe at a specific index"""
                try:
                    # Get current user from session storage
                    current_user = get_current_user()
                    # Get existing ingredients from other recipes to maintain sharing
                    existing_ingredients = []
                    used_carbohydrates = []
                    carb_keywords = ['rice', 'pasta', 'noodle', 'potato', 'quinoa', 'bulgur', 'couscous', 'polenta', 'bread', 'barley', 'sweet potato', 'lentil', 'chickpea', 'bean', 'flour', 'wheat', 'oat', 'corn', 'maize']
                    
                    for idx, recipe in enumerate(current_recipes):
                        if idx != recipe_index and "ingredients" in recipe:
                            for ingredient in recipe["ingredients"]:
                                item = ingredient.get("item", "").lower()
                                if item and item not in [ing.lower() for ing in existing_ingredients]:
                                    existing_ingredients.append(ingredient.get("item", ""))
                                
                                # Track carbohydrates from other recipes
                                for carb_keyword in carb_keywords:
                                    if carb_keyword in item and item not in [carb.lower() for carb in used_carbohydrates]:
                                        used_carbohydrates.append(ingredient.get("item", ""))
                                        break
                    
                    # Show loading state for this recipe
                    ui.notify(f'Generating new recipe #{recipe_index + 1}...', type='info')
                    
                    # Generate new recipe with carbohydrate variety
                    new_recipe = await recipe_generator.generate_single_recipe(
                        recipe_index + 1, liked_foods, disliked_foods, existing_ingredients, 
                        None, len(current_recipes), serving_size, used_carbohydrates
                    )
                    
                    if "error" not in new_recipe:
                        # Replace the recipe in the list
                        current_recipes[recipe_index] = new_recipe
                        
                        # Update meal plan in database if user is logged in
                        try:
                            if current_user:
                                db = next(get_db())
                                
                                # Find the most recent meal plan for this user
                                latest_meal_plan = db.query(MealPlan).filter(
                                    MealPlan.user_id == current_user["id"]
                                ).order_by(MealPlan.created_at.desc()).first()
                                
                                if latest_meal_plan:
                                    # Update the recipes and shopping list
                                    updated_shopping_list = generate_shopping_list(current_recipes)
                                    latest_meal_plan.recipes_json = json.dumps(current_recipes)
                                    latest_meal_plan.shopping_list_json = json.dumps(updated_shopping_list)
                                    db.commit()
                                    
                                    ui.notify(f'Recipe #{recipe_index + 1} updated successfully!', type='positive')
                        except Exception as e:
                            print(f"Error updating meal plan: {e}")
                            ui.notify('Recipe updated but failed to save to history', type='warning')
                        
                        # Refresh the page to show the new recipe
                        ui.navigate.reload()
                    else:
                        ui.notify(f'Failed to generate new recipe: {new_recipe.get("error", "Unknown error")}', type='negative')
                        
                except Exception as e:
                    ui.notify(f'Error regenerating recipe: {str(e)}', type='negative')
        
            async def generate_recipes_handler():
                theme = get_theme_classes()  # Get current theme
                
                # Clear previous results
                result_container.clear()
                
                # Progress tracking
                progress_card = None
                progress_text = None
                
                async def update_progress(message: str):
                    nonlocal progress_card, progress_text
                    if progress_text:
                        progress_text.content = message
                    else:
                        with result_container:
                            progress_card = ui.card().classes(f'progress-glow recipe-card {theme["card"]} {theme["border"]} rounded-3xl p-12 w-full text-center')
                            with progress_card:
                                with ui.column().classes('items-center gap-6'):
                                    ui.spinner(size='xl', color='emerald')
                                    ui.html(f'<h3 class="section-title {theme["text_primary"]} mb-0">Creating Your Recipe Collection</h3>')
                                    progress_text = ui.html(f'<p class="text-lg {theme["text_secondary"]} font-medium">{message}</p>')
                
                # Initial loading state
                await update_progress('Starting recipe generation...')
                
                # Parse inputs
                liked_foods = [food.strip() for food in liked_input.value.split(',') if food.strip()]
                disliked_foods = [food.strip() for food in disliked_input.value.split(',') if food.strip()]
                recipe_count = recipe_count_select.value
                serving_size = serving_size_select.value
                
                # Update user preferences in database
                try:
                    db = next(get_db())
                    if current_user:
                        # Get the actual user object from database to update
                        user = db.query(User).filter(User.id == current_user['id']).first()
                        if user:
                            user.liked_foods = liked_input.value
                            user.disliked_foods = disliked_input.value
                            db.add(user)
                            db.commit()
                            
                            # Update session storage with new preferences
                            updated_user_data = current_user.copy()
                            updated_user_data['liked_foods'] = liked_input.value
                            updated_user_data['disliked_foods'] = disliked_input.value
                            app.storage.user['current_user'] = updated_user_data
                            
                            await update_progress('Saving your preferences...')
                except Exception as e:
                    print(f"Error saving preferences: {e}")
                
                # Generate recipes with progress updates
                recipes = await recipe_generator.generate_recipes(liked_foods, disliked_foods, recipe_count, serving_size, update_progress)
                
                # Clear loading state
                result_container.clear()
                
                with result_container:
                    if recipes and "error" not in recipes[0]:
                        # Save meal plan to database
                        try:
                            db = next(get_db())
                            if current_user:
                                print(f"Saving meal plan for user {current_user['id']} ({current_user['name']})")
                                # Generate shopping list
                                shopping_list = generate_shopping_list(recipes)
                                
                                # Create meal plan record
                                meal_plan_data = MealPlanCreate(
                                    name=f"Meal Plan - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                                    serving_size=serving_size,
                                    recipe_count=recipe_count,
                                    recipes_json=json.dumps(recipes),
                                    shopping_list_json=json.dumps(shopping_list),
                                    liked_foods_snapshot=liked_input.value,
                                    disliked_foods_snapshot=disliked_input.value
                                )
                                
                                saved_meal_plan = create_meal_plan(db, meal_plan_data, current_user['id'])
                                print(f"Successfully saved meal plan with ID: {saved_meal_plan.id}")
                                ui.notify(f'Meal plan saved to your history!', type='positive')
                            else:
                                print("ERROR: current_user is None, cannot save meal plan")
                                ui.notify('Unable to save meal plan - please log in again', type='negative')
                        except Exception as e:
                            print(f"Error saving meal plan: {e}")
                            ui.notify(f'Error saving meal plan: {str(e)}', type='negative')
                        
                        # Success header with stunning design
                        with ui.card().classes(f'recipe-card {theme["success_bg"]} {theme["border"]} rounded-3xl p-8 w-full mb-8'):
                            with ui.column().classes('items-center text-center'):
                                ui.html('<div class="text-5xl mb-4">🎉</div>')
                                ui.html(f'<h2 class="section-title {theme["text_primary"]} mb-4">Your Personalized Recipe Collection</h2>')
                                ui.html(f'<p class="text-lg {theme["text_secondary"]} max-w-2xl mx-auto">We\'ve crafted <strong>{len(recipes)} delicious recipes</strong> perfectly tailored to your taste preferences, with optimized ingredient sharing for efficient shopping.</p>')
                        
                        # Display recipes in a responsive container
                        with ui.element('div').classes('recipe-grid'):
                            for i, recipe in enumerate(recipes, 1):
                                with ui.card().classes(f'recipe-card {theme["card"]} {theme["card_hover"]} {theme["border"]} rounded-3xl p-6 sm:p-8').style('width: 100%'):
                                    # Recipe header with responsive design
                                    with ui.row().classes('items-start justify-between mb-4 sm:mb-6'):
                                        with ui.column().classes('flex-1'):
                                            ui.html(f'<div class="text-xs sm:text-sm font-bold {theme["text_secondary"]} uppercase tracking-wider mb-2">Recipe #{i}</div>')
                                            ui.html(f'<h3 class="text-xl sm:text-2xl font-bold {theme["text_primary"]} leading-tight mb-0">{recipe.get("name", "Unnamed Recipe")}</h3>')
                                        
                                        with ui.column().classes('items-end gap-2'):
                                            ui.html(f'<div class="text-2xl sm:text-3xl">🍽️</div>')
                                            
                                            # Recipe rating section (for saved meal plans)
                                            if saved_meal_plan_id:
                                                try:
                                                    db = next(get_db())
                                                    current_rating = get_recipe_rating(db, current_user['id'], saved_meal_plan_id, i-1)
                                                    rating_value = current_rating.rating if current_rating else 0
                                                    
                                                    with ui.row().classes('items-center gap-2 mb-2'):
                                                        ui.html(f'<span class="text-xs {theme["text_secondary"]}">Rate:</span>')
                                                        
                                                        # Create rating handler
                                                        def create_rating_handler(recipe_idx, recipe_name):
                                                            def rate_recipe_main(rating):
                                                                try:
                                                                    db = next(get_db())
                                                                    create_or_update_recipe_rating(
                                                                        db, current_user['id'], saved_meal_plan_id, recipe_idx, recipe_name, rating
                                                                    )
                                                                    ui.notify(f'Rated "{recipe_name}" {rating} star{"s" if rating != 1 else ""} ⭐', type='positive')
                                                                except Exception as e:
                                                                    ui.notify(f'Rating failed: {str(e)}', type='negative')
                                                            return rate_recipe_main
                                                        
                                                        rating_handler = create_rating_handler(i-1, recipe.get("name", "Unnamed Recipe"))
                                                        
                                                        # Star rating buttons
                                                        for star in range(1, 6):
                                                            star_icon = '⭐' if rating_value >= star else '☆'
                                                            ui.button(
                                                                star_icon,
                                                                on_click=lambda r=star: rating_handler(r)
                                                            ).classes('text-xs bg-transparent border-none p-1 hover:scale-110 transition-transform cursor-pointer').style('min-width: 20px; min-height: 20px;')
                                                except Exception as e:
                                                    print(f"Error loading recipe rating: {e}")
                                            
                                            # Regenerate button for this specific recipe
                                            def create_regenerate_handler(recipe_index, current_recipes):
                                                async def regenerate_single_recipe():
                                                    await regenerate_recipe_at_index(recipe_index, liked_foods, disliked_foods, serving_size, current_recipes)
                                                return regenerate_single_recipe
                                            
                                            ui.button(
                                                '🔄 Try Different',
                                                on_click=create_regenerate_handler(i-1, recipes)
                                            ).classes('text-xs px-3 py-2 rounded-lg font-medium transition-all duration-200 hover:scale-105 shadow-sm').style(
                                                'background-color: #fef3c7; color: #92400e; border: 1px solid #fcd34d; min-height: 36px; font-weight: 600;'
                                            ).tooltip('Don\'t like this recipe? Generate a different one!')
                                    
                                    # Recipe stats with responsive chips
                                    with ui.row().classes('gap-2 sm:gap-3 mb-4 sm:mb-6 flex-wrap'):
                                        for icon, label, value in [
                                            ("⏱️", "Prep", recipe.get("prep_time", "N/A")),
                                            ("🔥", "Cook", recipe.get("cook_time", "N/A")), 
                                            ("👥", "Serves", recipe.get("servings", "N/A"))
                                        ]:
                                            with ui.row().classes(f'chip-modern {theme["chip_bg"]} {theme["border"]} rounded-full px-3 sm:px-4 py-2 items-center gap-2'):
                                                ui.html(f'<span class="text-xs sm:text-sm">{icon}</span>')
                                                ui.html(f'<span class="text-xs sm:text-sm font-medium">{label}: {value}</span>')
                                        
                                    # Ingredients section with improved design
                                    if "ingredients" in recipe and recipe["ingredients"]:
                                        with ui.card().classes(f'{theme["bg_accent"]} rounded-xl p-4 mb-4'):
                                            with ui.row().classes('items-center gap-3 mb-3'):
                                                ui.html('<div class="text-xl">🛒</div>')
                                                ui.html(f'<h4 class="text-lg font-semibold {theme["text_primary"]} mb-0">Ingredients</h4>')
                                            
                                            with ui.column().classes('gap-2'):
                                                for ingredient in recipe["ingredients"]:
                                                    with ui.row().classes('items-center gap-3 py-1'):
                                                        ui.html('<div class="w-2 h-2 bg-emerald-500 rounded-full flex-shrink-0"></div>')
                                                        quantity_unit = f"{ingredient.get('quantity', '')} {ingredient.get('unit', '')}".strip()
                                                        ui.html(f'<span class="text-sm {theme["text_primary"]} flex-1"><span class="font-semibold text-emerald-600">{quantity_unit}</span> {ingredient.get("item", "")}</span>')
                                    
                                    # Instructions section with step-by-step design
                                    if "instructions" in recipe and recipe["instructions"]:
                                        with ui.card().classes(f'{theme["bg_accent"]} rounded-xl p-4'):
                                            with ui.row().classes('items-center gap-3 mb-3'):
                                                ui.html('<div class="text-xl">👨‍🍳</div>')
                                                ui.html(f'<h4 class="text-lg font-semibold {theme["text_primary"]} mb-0">Instructions</h4>')
                                            
                                            with ui.column().classes('gap-3'):
                                                for j, step in enumerate(recipe["instructions"], 1):
                                                    with ui.row().classes('items-start gap-3'):
                                                        ui.html(f'<div class="flex-shrink-0 w-8 h-8 bg-emerald-500 text-white rounded-full flex items-center justify-center text-sm font-bold">{j}</div>')
                                                        ui.html(f'<p class="text-sm {theme["text_primary"]} leading-relaxed flex-1 pt-1">{step}</p>')
                        
                        # Generate and display shopping list
                        shopping_list = generate_shopping_list(recipes)
                        
                        if shopping_list:
                            with ui.card().classes(f'recipe-card {theme["success_bg"]} {theme["border"]} rounded-3xl p-6 sm:p-8 w-full mt-6 sm:mt-8'):
                                with ui.column().classes('items-center text-center mb-4 sm:mb-6'):
                                    ui.html('<div class="text-3xl sm:text-4xl mb-4">🛒</div>')
                                    ui.html(f'<h2 class="section-title {theme["text_primary"]} mb-4">Smart Shopping List</h2>')
                                    ui.html(f'<p class="text-base sm:text-lg {theme["text_secondary"]} max-w-full sm:max-w-2xl mx-auto px-4">Everything you need for your {len(recipes)} recipes, intelligently optimized to minimize shopping time and cost.</p>')
                                
                                with ui.row().classes('gap-2 sm:gap-3 flex-wrap justify-center'):
                                    for item in shopping_list:
                                        with ui.row().classes(f'chip-modern {theme["chip_bg"]} {theme["border"]} rounded-xl sm:rounded-2xl px-4 sm:px-6 py-2 sm:py-3 items-center gap-2 sm:gap-3 min-w-fit'):
                                            ui.html('<div class="w-2 h-2 sm:w-3 sm:h-3 bg-emerald-400 rounded-full flex-shrink-0"></div>')
                                            ui.html(f'<span class="text-xs sm:text-sm font-semibold {theme["text_primary"]}">{item.get("quantity", "")} {item.get("unit", "")} {item.get("item", "")}</span>')
                        
                        # Export button
                        with ui.row().classes('justify-center w-full mt-8'):
                            def export_to_pdf():
                                """Export recipes and shopping list to PDF"""
                                try:
                                    # Generate PDF directly
                                    pdf_data = generate_pdf_export(recipes, shopping_list, liked_foods, disliked_foods, serving_size)
                                    
                                    # Create download with current date
                                    filename = f"FoodPal_Meal_Plan_{datetime.now().strftime('%Y%m%d')}.pdf"
                                    
                                    # Trigger download
                                    ui.download(pdf_data, filename)
                                    ui.notify('PDF exported successfully!', type='positive')
                                    
                                except Exception as e:
                                    ui.notify(f'Export failed: {str(e)}', type='negative')
                            
                            ui.button(
                                '📄 Export to PDF',
                                on_click=export_to_pdf
                            ).classes(f'{theme["button_secondary"]} text-white font-semibold py-3 px-6 rounded-xl shadow-lg')
                    
                    else:
                        # Error state with beautiful design
                        with ui.card().classes(f'recipe-card {theme["error_bg"]} {theme["border"]} rounded-3xl p-8 w-full'):
                            with ui.column().classes('items-center text-center'):
                                ui.html('<div class="text-5xl mb-4">😔</div>')
                                ui.html(f'<h2 class="section-title {theme["text_primary"]} mb-4">Oops! Something went wrong</h2>')
                                error_msg = recipes[0].get("error", "Unknown error") if recipes else "No recipes generated"
                                ui.html(f'<p class="text-lg {theme["text_secondary"]} mb-6">We encountered an issue while creating your recipes: <strong>{error_msg}</strong></p>')
                                
                                # Retry button
                                ui.button(
                                    '🔄 Try Again',
                                    on_click=lambda: generate_recipes_handler()
                                ).classes(f'{theme["button_primary"]} text-white font-semibold py-3 px-6 rounded-xl')
                                
                                if recipes and "raw_response" in recipes[0]:
                                    with ui.expansion('🔍 Technical Details', icon='code').classes('mt-6 w-full max-w-2xl'):
                                        ui.html(f'<pre class="text-xs {theme["text_secondary"]} bg-slate-800 p-4 rounded-lg overflow-auto">{recipes[0]["raw_response"]}</pre>')
            
            # Set the button handler
            generate_button.on_click(generate_recipes_handler)

@ui.page('/meal-plan/{meal_plan_id}')
def meal_plan_detail_page(meal_plan_id: int):
    # Check if user is logged in
    current_user = get_current_user()
    if current_user is None:
        ui.navigate.to('/login')
        return
    
    theme = get_theme_classes()
    
    # Add viewport and Material Icons
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    ui.add_head_html('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">')
    
    try:
        # Load meal plan from database
        db = next(get_db())
        meal_plan = db.query(MealPlan).filter(
            MealPlan.id == meal_plan_id, 
            MealPlan.user_id == current_user['id']
        ).first()
        
        if not meal_plan:
            ui.notify('Meal plan not found', type='negative')
            ui.navigate.to('/history')
            return
        
        # Parse JSON data
        try:
            recipes = json.loads(meal_plan.recipes_json)
            shopping_list = json.loads(meal_plan.shopping_list_json)
            # Load existing recipe ratings
            recipe_ratings = get_meal_plan_recipe_ratings(db, current_user['id'], meal_plan_id)
            ratings_dict = {r.recipe_index: r for r in recipe_ratings}
        except json.JSONDecodeError:
            ui.notify('Error loading meal plan data', type='negative')
            ui.navigate.to('/history')
            return
        
        with ui.column().classes(f'min-h-screen {theme["bg_primary"]} {theme["text_primary"]} p-8'):
            # Header
            with ui.row().classes('items-center justify-between w-full mb-8'):
                with ui.row().classes('items-center gap-4'):
                    ui.button(
                        '←',
                        on_click=lambda: ui.navigate.to('/history')
                    ).classes(f'{theme["button_secondary"]} rounded-full w-12 h-12 text-xl')
                    ui.html(f'<h1 class="text-3xl font-bold {theme["gradient_text"]}">📋 {meal_plan.name}</h1>')
                
                # User info and date
                with ui.column().classes('text-right'):
                    ui.html(f'<span class="text-lg {theme["text_secondary"]}">{current_user["name"]}\'s Kitchen</span>')
                    ui.html(f'<span class="text-sm {theme["text_secondary"]}">{meal_plan.created_at.strftime("%B %d, %Y at %I:%M %p")}</span>')
            
            # Meal plan info
            with ui.row().classes('gap-4 mb-8'):
                ui.html(f'<span class="{theme["chip_bg"]} {theme["border"]} rounded-full px-4 py-2 text-sm font-medium">{meal_plan.recipe_count} recipes</span>')
                ui.html(f'<span class="{theme["chip_bg"]} {theme["border"]} rounded-full px-4 py-2 text-sm font-medium">{meal_plan.serving_size} servings</span>')
                if meal_plan.rating:
                    ui.html(f'<span class="{theme["chip_bg"]} {theme["border"]} rounded-full px-4 py-2 text-sm font-medium">{"⭐" * meal_plan.rating} ({meal_plan.rating}/5)</span>')
            
            # Show preferences snapshot
            if meal_plan.liked_foods_snapshot or meal_plan.disliked_foods_snapshot:
                with ui.card().classes(f'{theme["card"]} {theme["border"]} rounded-2xl p-6 mb-8'):
                    ui.html(f'<h3 class="text-lg font-bold {theme["text_primary"]} mb-4">🎯 Preferences Used</h3>')
                    with ui.row().classes('gap-6 text-sm'):
                        if meal_plan.liked_foods_snapshot:
                            with ui.column():
                                ui.html(f'<span class="font-medium {theme["text_primary"]}">💚 Liked Foods:</span>')
                                ui.html(f'<span class="{theme["text_secondary"]}">{meal_plan.liked_foods_snapshot}</span>')
                        if meal_plan.disliked_foods_snapshot:
                            with ui.column():
                                ui.html(f'<span class="font-medium {theme["text_primary"]}">🚫 Avoided Foods:</span>')
                                ui.html(f'<span class="{theme["text_secondary"]}">{meal_plan.disliked_foods_snapshot}</span>')
            
            # Display recipes
            if recipes:
                ui.html(f'<h2 class="text-2xl font-bold {theme["text_primary"]} mb-6">🍽️ Your Recipes</h2>')
                
                with ui.column().classes('gap-6'):
                    for i, recipe in enumerate(recipes, 1):
                        if "error" not in recipe:
                            recipe_index = i - 1  # 0-based index for database
                            current_rating = ratings_dict.get(recipe_index)
                            
                            with ui.card().classes(f'recipe-card {theme["card"]} {theme["border"]} rounded-3xl p-6 sm:p-8 w-full'):
                                with ui.row().classes('items-center justify-between gap-4 mb-6'):
                                    with ui.row().classes('items-center gap-4'):
                                        ui.html(f'<div class="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-emerald-400 to-teal-500 text-white rounded-full flex items-center justify-center text-xl font-bold">{i}</div>')
                                        ui.html(f'<h3 class="text-2xl font-bold {theme["text_primary"]}">{recipe.get("name", "Untitled Recipe")}</h3>')
                                    
                                    # Recipe rating section
                                    with ui.column().classes('items-end'):
                                        rating_value = current_rating.rating if current_rating else 0
                                        if rating_value > 0:
                                            ui.html(f'<span class="text-sm {theme["text_primary"]} font-medium mb-1">Your Rating:</span>')
                                            ui.html(f'<span class="text-lg">{"⭐" * rating_value}{"☆" * (5-rating_value)}</span>')
                                        else:
                                            ui.html(f'<span class="text-sm {theme["text_secondary"]} mb-1">Rate this recipe:</span>')
                                        
                                        # Star rating buttons
                                        def rate_recipe(recipe_idx: int, recipe_title: str, rating: int):
                                            try:
                                                db = next(get_db())
                                                create_or_update_recipe_rating(
                                                    db, current_user['id'], meal_plan_id, recipe_idx, recipe_title, rating
                                                )
                                                ui.notify(f'Rated "{recipe_title}" {rating} star{"s" if rating != 1 else ""} ⭐', type='positive')
                                                ui.navigate.reload()
                                            except Exception as e:
                                                ui.notify(f'Rating failed: {str(e)}', type='negative')
                                        
                                        with ui.row().classes('gap-1 mt-2'):
                                            for star in range(1, 6):
                                                star_icon = '⭐' if rating_value >= star else '☆'
                                                button_class = f'text-lg bg-transparent border-none p-1 hover:scale-110 transition-transform cursor-pointer'
                                                if rating_value < star:
                                                    button_class += ' opacity-60 hover:opacity-100'
                                                
                                                star_button = ui.button(
                                                    star_icon,
                                                    on_click=lambda idx=recipe_index, title=recipe.get("name", "Untitled Recipe"), r=star: rate_recipe(idx, title, r)
                                                ).classes(button_class).style('min-width: 28px; min-height: 28px;')
                                                
                                                star_labels = {1: 'Poor', 2: 'Fair', 3: 'Good', 4: 'Very Good', 5: 'Excellent'}
                                                star_button.tooltip(f'{star} star{"s" if star != 1 else ""} - {star_labels[star]}')
                                
                                with ui.row().classes('gap-8 w-full'):
                                    # Left column - Ingredients
                                    with ui.column().classes('flex-1'):
                                        with ui.row().classes('items-center gap-3 mb-4'):
                                            ui.html('<div class="text-2xl">🛒</div>')
                                            ui.html(f'<h4 class="text-lg font-semibold {theme["text_primary"]} mb-0">Ingredients</h4>')
                                        
                                        with ui.column().classes('gap-2'):
                                            for ingredient in recipe.get("ingredients", []):
                                                with ui.row().classes('items-center gap-3'):
                                                    ui.html('<div class="w-2 h-2 bg-emerald-400 rounded-full flex-shrink-0"></div>')
                                                    # Handle both string and object ingredient formats
                                                    if isinstance(ingredient, dict):
                                                        quantity = ingredient.get("quantity", "")
                                                        unit = ingredient.get("unit", "")
                                                        item = ingredient.get("item", "")
                                                        display_text = f"{quantity} {unit} {item}".strip()
                                                    else:
                                                        display_text = str(ingredient)
                                                    ui.html(f'<span class="text-sm {theme["text_primary"]}">{display_text}</span>')
                                    
                                    # Right column - Instructions
                                    with ui.column().classes('flex-1'):
                                        with ui.row().classes('items-center gap-3 mb-4'):
                                            ui.html('<div class="text-2xl">👨‍🍳</div>')
                                            ui.html(f'<h4 class="text-lg font-semibold {theme["text_primary"]} mb-0">Instructions</h4>')
                                        
                                        with ui.column().classes('gap-3'):
                                            for j, step in enumerate(recipe.get("instructions", []), 1):
                                                with ui.row().classes('items-start gap-3'):
                                                    ui.html(f'<div class="flex-shrink-0 w-8 h-8 bg-emerald-500 text-white rounded-full flex items-center justify-center text-sm font-bold">{j}</div>')
                                                    ui.html(f'<p class="text-sm {theme["text_primary"]} leading-relaxed flex-1 pt-1">{step}</p>')
            
            # Display shopping list
            if shopping_list:
                with ui.card().classes(f'recipe-card {theme["success_bg"]} {theme["border"]} rounded-3xl p-6 sm:p-8 w-full mt-8'):
                    with ui.column().classes('items-center text-center mb-6'):
                        ui.html('<div class="text-4xl mb-4">🛒</div>')
                        ui.html(f'<h2 class="text-2xl font-bold {theme["text_primary"]} mb-4">Smart Shopping List</h2>')
                        ui.html(f'<p class="text-lg {theme["text_secondary"]} max-w-2xl mx-auto">Everything you need for your {len(recipes)} recipes, intelligently optimized.</p>')
                    
                    with ui.row().classes('gap-3 flex-wrap justify-center'):
                        for item in shopping_list:
                            with ui.row().classes(f'chip-modern {theme["chip_bg"]} {theme["border"]} rounded-2xl px-6 py-3 items-center gap-3 min-w-fit'):
                                ui.html('<div class="w-3 h-3 bg-emerald-400 rounded-full flex-shrink-0"></div>')
                                ui.html(f'<span class="text-sm font-semibold {theme["text_primary"]}">{item.get("quantity", "")} {item.get("unit", "")} {item.get("item", "")}</span>')
            
            # Export button
            with ui.row().classes('justify-center w-full mt-8'):
                def export_to_pdf():
                    """Export this meal plan to PDF"""
                    try:
                        # Generate PDF with the historical data
                        pdf_data = generate_pdf_export(
                            recipes, 
                            shopping_list, 
                            meal_plan.liked_foods_snapshot.split(',') if meal_plan.liked_foods_snapshot else [],
                            meal_plan.disliked_foods_snapshot.split(',') if meal_plan.disliked_foods_snapshot else [],
                            meal_plan.serving_size
                        )
                        
                        # Create download with meal plan name and date
                        filename = f"FoodPal_{meal_plan.name.replace(' ', '_')}_{meal_plan.created_at.strftime('%Y%m%d')}.pdf"
                        
                        # Trigger download
                        ui.download(pdf_data, filename)
                        ui.notify('PDF exported successfully!', type='positive')
                        
                    except Exception as e:
                        ui.notify(f'Export failed: {str(e)}', type='negative')
                
                ui.button(
                    '📄 Export to PDF',
                    on_click=export_to_pdf
                ).classes(f'{theme["button_secondary"]} text-white font-semibold py-3 px-6 rounded-xl shadow-lg')
    
    except Exception as e:
        ui.notify(f'Error loading meal plan: {str(e)}', type='negative')
        ui.navigate.to('/history')

@ui.page('/history')
def history_page():
    # Check if user is logged in
    current_user = get_current_user()
    if current_user is None:
        ui.navigate.to('/login')
        return
    
    theme = get_theme_classes()
    
    # Add viewport and Material Icons
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    ui.add_head_html('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">')
    
    with ui.column().classes(f'min-h-screen {theme["bg_primary"]} {theme["text_primary"]} p-8'):
        # Header
        with ui.row().classes('items-center justify-between w-full mb-8'):
            with ui.row().classes('items-center gap-4'):
                ui.button(
                    '←',
                    on_click=lambda: ui.navigate.to('/')
                ).classes(f'{theme["button_secondary"]} rounded-full w-12 h-12 text-xl')
                ui.html(f'<h1 class="text-3xl font-bold {theme["gradient_text"]}">📈 Meal History</h1>')
            
            # User info
            ui.html(f'<span class="text-lg {theme["text_secondary"]}">{current_user["name"]}\'s Kitchen</span>')
        
        # Load meal history
        try:
            db = next(get_db())
            print(f"Loading meal history for user {current_user['id']} ({current_user['name']})")
            meal_plans = get_user_meal_plans(db, current_user['id'], limit=20)
            print(f"Found {len(meal_plans)} meal plans in database")
            
            if meal_plans:
                ui.html(f'<p class="text-lg {theme["text_secondary"]} mb-6">You\'ve created {len(meal_plans)} meal plans. Here are your recent creations:</p>')
                
                # Display meal plans
                with ui.column().classes('w-full gap-6'):
                    for meal_plan in meal_plans:
                        with ui.card().classes(f'{theme["card"]} {theme["border"]} rounded-2xl p-6 cursor-pointer hover:shadow-lg transition-shadow').on('click', lambda e, plan_id=meal_plan.id: ui.navigate.to(f'/meal-plan/{plan_id}')):
                            with ui.row().classes('items-center justify-between mb-4'):
                                with ui.column():
                                    ui.html(f'<h3 class="text-xl font-bold {theme["text_primary"]}">{meal_plan.name}</h3>')
                                    ui.html(f'<p class="text-sm {theme["text_secondary"]}">{meal_plan.created_at.strftime("%B %d, %Y at %I:%M %p")}</p>')
                                
                                with ui.row().classes('gap-2'):
                                    ui.html(f'<span class="{theme["chip_bg"]} {theme["border"]} rounded-full px-3 py-1 text-sm">{meal_plan.recipe_count} recipes</span>')
                                    ui.html(f'<span class="{theme["chip_bg"]} {theme["border"]} rounded-full px-3 py-1 text-sm">{meal_plan.serving_size} servings</span>')
                            
                            # Show preferences snapshot
                            if meal_plan.liked_foods_snapshot or meal_plan.disliked_foods_snapshot:
                                with ui.row().classes('gap-4 text-sm'):
                                    if meal_plan.liked_foods_snapshot:
                                        ui.html(f'<span class="{theme["text_secondary"]}">💚 Liked: {meal_plan.liked_foods_snapshot[:50]}...</span>')
                                    if meal_plan.disliked_foods_snapshot:
                                        ui.html(f'<span class="{theme["text_secondary"]}">🚫 Avoided: {meal_plan.disliked_foods_snapshot[:50]}...</span>')
                            
                            # Click to view details hint
                            with ui.row().classes('mt-4 items-center gap-2'):
                                ui.html(f'<span class="text-sm {theme["text_secondary"]}">👆 Click to view full recipes and shopping list</span>')
                                
                            # Improved rating system
                            with ui.column().classes('mt-4 space-y-3'):
                                # Rating header with current rating display
                                current_rating = meal_plan.rating or 0
                                if current_rating > 0:
                                    rating_text = f'Your Rating: {"⭐" * current_rating}{"☆" * (5-current_rating)} ({current_rating}/5)'
                                    ui.html(f'<span class="text-sm {theme["text_primary"]} font-medium">{rating_text}</span>')
                                else:
                                    ui.html(f'<span class="text-sm {theme["text_secondary"]}">Rate this meal plan:</span>')
                                
                                # Interactive star rating
                                def rate_meal_plan(plan_id: int, rating: int):
                                    try:
                                        db = next(get_db())
                                        plan = db.query(MealPlan).filter(MealPlan.id == plan_id).first()
                                        if plan:
                                            plan.rating = rating
                                            db.commit()
                                            ui.notify(f'Rated {rating} star{"s" if rating != 1 else ""} - Thank you!', type='positive')
                                            ui.navigate.reload()
                                    except Exception as e:
                                        ui.notify(f'Rating failed: {str(e)}', type='negative')
                                
                                with ui.row().classes('gap-1'):
                                    for i in range(1, 6):
                                        # Show filled stars up to current rating, empty stars after
                                        if current_rating >= i:
                                            star_icon = '⭐'
                                            button_class = f'text-xl bg-transparent border-none p-2 hover:scale-110 transition-transform cursor-pointer'
                                        else:
                                            star_icon = '☆'
                                            button_class = f'text-xl bg-transparent border-none p-2 hover:scale-110 transition-transform cursor-pointer opacity-60 hover:opacity-100'
                                        
                                        # Create button with tooltip
                                        star_button = ui.button(
                                            star_icon,
                                            on_click=lambda plan_id=meal_plan.id, rating=i: rate_meal_plan(plan_id, rating)
                                        ).classes(button_class).style('min-width: 40px; min-height: 40px;')
                                        
                                        # Add tooltip for better UX
                                        star_labels = {1: 'Poor', 2: 'Fair', 3: 'Good', 4: 'Very Good', 5: 'Excellent'}
                                        star_button.tooltip(f'{i} star{"s" if i != 1 else ""} - {star_labels[i]}')
            else:
                # Empty state
                with ui.card().classes(f'{theme["card"]} {theme["border"]} rounded-2xl p-12 text-center'):
                    ui.html('<div class="text-6xl mb-4">🍽️</div>')
                    ui.html(f'<h2 class="text-2xl font-bold {theme["text_primary"]} mb-4">No meal history yet</h2>')
                    ui.html(f'<p class="text-lg {theme["text_secondary"]} mb-6">Start creating personalized recipes to see your meal history here!</p>')
                    ui.button(
                        'Create Your First Meal Plan',
                        on_click=lambda: ui.navigate.to('/')
                    ).classes(f'{theme["button_primary"]} text-white py-3 px-6 rounded-xl')
        
        except Exception as e:
            ui.notify(f'Error loading meal history: {str(e)}', type='negative')

# Mount NiceGUI with FastAPI
app.mount('/api', fastapi_app)

if __name__ in {"__main__", "__mp_main__"}:
    # Generate or use a storage secret for session management
    storage_secret = os.getenv("NICEGUI_STORAGE_SECRET", "foodpal-secret-key-2024-change-in-production")
    ui.run(port=8080, title="FoodPal Recipe Generator", storage_secret=storage_secret)