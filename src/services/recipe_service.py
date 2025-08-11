"""
Recipe generation service layer
Separates business logic from UI components for better maintainability
"""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import json
import asyncio
import logging

from ..database.operations import create_meal_plan
from ..models.schemas import MealPlanCreate
from ..services.recipe_generator import RecipeGenerator
from ..utils.shopping_list import generate_shopping_list
from ..utils.error_handler import safe_async_ui_operation, DatabaseException, APIException, ValidationException, validate_input, VALIDATION_RULES
from ..utils.resource_manager import managed_database_session

logger = logging.getLogger(__name__)

class RecipeGenerationRequest:
    """Recipe generation request data"""
    def __init__(
        self,
        user_id: int,
        liked_foods: List[str],
        disliked_foods: List[str],
        must_use_ingredients: List[str],
        recipe_count: int,
        serving_size: int,
        generate_images: bool = True,
        background_mode: bool = False
    ):
        self.user_id = user_id
        self.liked_foods = liked_foods
        self.disliked_foods = disliked_foods
        self.must_use_ingredients = must_use_ingredients
        self.recipe_count = recipe_count
        self.serving_size = serving_size
        self.generate_images = generate_images
        self.background_mode = background_mode
        
        # Validate inputs
        self._validate()
    
    def _validate(self):
        """Validate request parameters"""
        if not isinstance(self.user_id, int) or self.user_id <= 0:
            raise ValidationException("Invalid user ID", "INVALID_USER_ID")
        
        if not isinstance(self.recipe_count, int) or self.recipe_count < 1 or self.recipe_count > 20:
            raise ValidationException("Recipe count must be between 1 and 20", "INVALID_RECIPE_COUNT")
        
        if not isinstance(self.serving_size, int) or self.serving_size < 1 or self.serving_size > 50:
            raise ValidationException("Serving size must be between 1 and 50", "INVALID_SERVING_SIZE")

class RecipeGenerationResult:
    """Recipe generation result data"""
    def __init__(
        self,
        recipes: List[Dict[str, Any]],
        shopping_list: List[Dict[str, str]],
        meal_plan_id: Optional[int] = None,
        generation_time_seconds: Optional[float] = None
    ):
        self.recipes = recipes
        self.shopping_list = shopping_list
        self.meal_plan_id = meal_plan_id
        self.generation_time_seconds = generation_time_seconds

class RecipeService:
    """Service for recipe generation operations"""
    
    def __init__(self, lm_studio_url: str, lm_studio_model: str):
        self.recipe_generator = RecipeGenerator(lm_studio_url, lm_studio_model)
    
    @safe_async_ui_operation(
        user_message="Recipe generation failed. Please check your preferences and try again.",
        context="Recipe Generation"
    )
    async def generate_recipes(
        self,
        request: RecipeGenerationRequest,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> RecipeGenerationResult:
        """Generate recipes based on user preferences"""
        
        start_time = datetime.now()
        
        try:
            # Log request
            logger.info(f"Starting recipe generation for user {request.user_id}: "
                       f"{request.recipe_count} recipes, {request.serving_size} servings")
            
            # Generate recipes with progress tracking
            recipes = await self._generate_recipes_with_progress(request, progress_callback)
            
            # Generate shopping list
            if progress_callback:
                progress_callback("Generating optimized shopping list...")
            
            shopping_list = generate_shopping_list(recipes)
            
            # Save meal plan to database
            meal_plan_id = None
            if not request.background_mode:
                meal_plan_id = await self._save_meal_plan(request, recipes, shopping_list)
            
            # Calculate generation time
            generation_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Recipe generation completed in {generation_time:.2f} seconds")
            
            return RecipeGenerationResult(
                recipes=recipes,
                shopping_list=shopping_list,
                meal_plan_id=meal_plan_id,
                generation_time_seconds=generation_time
            )
            
        except Exception as e:
            logger.error(f"Recipe generation failed for user {request.user_id}: {e}", exc_info=True)
            
            if "timeout" in str(e).lower():
                raise APIException("Recipe generation timed out. Please try again.", "GENERATION_TIMEOUT")
            elif "connection" in str(e).lower():
                raise APIException("Unable to connect to recipe generation service. Please try again later.", "CONNECTION_ERROR")
            else:
                raise APIException(f"Recipe generation failed: {str(e)}", "GENERATION_FAILED")
    
    async def _generate_recipes_with_progress(
        self,
        request: RecipeGenerationRequest,
        progress_callback: Optional[Callable[[str], None]]
    ) -> List[Dict[str, Any]]:
        """Generate recipes with detailed progress tracking"""
        
        try:
            # Use managed database session
            with managed_database_session() as db:
                recipes = await self.recipe_generator.generate_recipes_with_images(
                    liked_foods=request.liked_foods,
                    disliked_foods=request.disliked_foods,
                    recipe_count=request.recipe_count,
                    serving_size=request.serving_size,
                    progress_callback=progress_callback,
                    user_id=request.user_id,
                    db_session=db,
                    must_use_ingredients=request.must_use_ingredients,
                    generate_images=request.generate_images,
                    comfyui_server="192.168.4.208:8188"  # TODO: Move to config
                )
            
            if not recipes:
                raise APIException("No recipes were generated. Please try different preferences.", "NO_RECIPES_GENERATED")
            
            return recipes
            
        except Exception as e:
            logger.error(f"Error in recipe generation with progress: {e}")
            raise
    
    async def _save_meal_plan(
        self,
        request: RecipeGenerationRequest,
        recipes: List[Dict[str, Any]],
        shopping_list: List[Dict[str, str]]
    ) -> int:
        """Save generated meal plan to database"""
        
        try:
            with managed_database_session() as db:
                meal_plan_data = MealPlanCreate(
                    name=f"Meal Plan - {datetime.now().strftime('%B %d, %Y')}",
                    serving_size=request.serving_size,
                    recipe_count=request.recipe_count,
                    recipes_json=json.dumps(recipes),
                    shopping_list_json=json.dumps(shopping_list),
                    liked_foods_snapshot=", ".join(request.liked_foods),
                    disliked_foods_snapshot=", ".join(request.disliked_foods),
                    must_use_ingredients_snapshot=", ".join(request.must_use_ingredients)
                )
                
                saved_meal_plan = create_meal_plan(db, meal_plan_data, request.user_id)
                logger.info(f"Saved meal plan {saved_meal_plan.id} for user {request.user_id}")
                
                return saved_meal_plan.id
                
        except Exception as e:
            logger.error(f"Error saving meal plan: {e}")
            raise DatabaseException(f"Failed to save meal plan: {str(e)}", "SAVE_MEAL_PLAN_FAILED")

class BackgroundRecipeService(RecipeService):
    """Service for background recipe generation"""
    
    async def generate_recipes_background(
        self,
        request: RecipeGenerationRequest,
        task_update_callback: Optional[Callable[[str, float], None]] = None
    ) -> int:
        """Generate recipes in background and return task ID"""
        
        try:
            from ..database.operations import create_generation_task
            from ..services.background_tasks import start_background_generation
            
            # Create generation task record
            with managed_database_session() as db:
                task = create_generation_task(
                    db=db,
                    user_id=request.user_id,
                    recipe_count=request.recipe_count,
                    serving_size=request.serving_size,
                    liked_foods=", ".join(request.liked_foods),
                    disliked_foods=", ".join(request.disliked_foods),
                    must_use_ingredients=", ".join(request.must_use_ingredients)
                )
            
            # Start background task
            await start_background_generation(task.id)
            
            logger.info(f"Started background recipe generation task {task.id} for user {request.user_id}")
            return task.id
            
        except Exception as e:
            logger.error(f"Failed to start background generation: {e}")
            raise APIException(f"Failed to start background generation: {str(e)}", "BACKGROUND_GENERATION_FAILED")

def create_recipe_service(lm_studio_url: str = None, lm_studio_model: str = None) -> RecipeService:
    """Factory function to create recipe service"""
    from ..config import LM_STUDIO_BASE_URL, LM_STUDIO_MODEL
    
    url = lm_studio_url or LM_STUDIO_BASE_URL
    model = lm_studio_model or LM_STUDIO_MODEL
    
    return RecipeService(url, model)

def create_background_recipe_service(lm_studio_url: str = None, lm_studio_model: str = None) -> BackgroundRecipeService:
    """Factory function to create background recipe service"""
    from ..config import LM_STUDIO_BASE_URL, LM_STUDIO_MODEL
    
    url = lm_studio_url or LM_STUDIO_BASE_URL
    model = lm_studio_model or LM_STUDIO_MODEL
    
    return BackgroundRecipeService(url, model)

# Input validation functions
def validate_recipe_preferences(
    liked_foods: str,
    disliked_foods: str,
    must_use_ingredients: str,
    recipe_count: int,
    serving_size: int
) -> tuple:
    """Validate and clean recipe generation inputs"""
    
    # Clean and validate text inputs
    liked_list = [f.strip() for f in liked_foods.split(',') if f.strip()] if liked_foods else []
    disliked_list = [f.strip() for f in disliked_foods.split(',') if f.strip()] if disliked_foods else []
    must_use_list = [f.strip() for f in must_use_ingredients.split(',') if f.strip()] if must_use_ingredients else []
    
    # Validate recipe count
    recipe_count = validate_input(recipe_count, VALIDATION_RULES['recipe_count'], "Recipe count")
    
    # Validate serving size
    serving_size = validate_input(serving_size, VALIDATION_RULES['serving_size'], "Serving size")
    
    # Check for conflicting preferences
    conflicts = set(liked_list) & set(disliked_list)
    if conflicts:
        raise ValidationException(f"Conflicting preferences found: {', '.join(conflicts)}", "CONFLICTING_PREFERENCES")
    
    # Validate list lengths
    if len(liked_list) > 20:
        raise ValidationException("Too many liked foods (maximum 20)", "TOO_MANY_LIKED_FOODS")
    
    if len(disliked_list) > 20:
        raise ValidationException("Too many disliked foods (maximum 20)", "TOO_MANY_DISLIKED_FOODS")
    
    if len(must_use_list) > 10:
        raise ValidationException("Too many must-use ingredients (maximum 10)", "TOO_MANY_MUST_USE")
    
    return liked_list, disliked_list, must_use_list, recipe_count, serving_size