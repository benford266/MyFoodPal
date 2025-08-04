"""
Recipe Generation API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import json

from ...database.connection import get_db
from ...database.models import User, GenerationTask, GenerationTaskStatus, MealPlan
from ...models.schemas import (
    RecipeGenerationRequest, 
    GenerationTaskResponse, 
    MealPlanResponse
)
from ...services.auth import AuthService
from ...services.recipe_generator import RecipeGeneratorService
from ...utils.shopping_list import generate_shopping_list

router = APIRouter()
auth_service = AuthService()


async def background_recipe_generation(
    task_id: int,
    user_id: int,
    request: RecipeGenerationRequest,
    db: Session
):
    """Background task for recipe generation"""
    try:
        # Update task status
        task = db.query(GenerationTask).filter(GenerationTask.id == task_id).first()
        task.status = GenerationTaskStatus.GENERATING_RECIPES
        task.current_step = "Starting recipe generation..."
        db.commit()
        
        # Initialize recipe generator
        recipe_service = RecipeGeneratorService()
        
        # Progress callback
        async def progress_callback(message: str):
            task = db.query(GenerationTask).filter(GenerationTask.id == task_id).first()
            if task:
                task.current_step = message
                # Simple progress estimation based on message content
                if "recipe 1/" in message:
                    task.progress = 20
                elif "recipe 2/" in message:
                    task.progress = 40
                elif "recipe 3/" in message:
                    task.progress = 60
                elif "recipe 4/" in message:
                    task.progress = 80
                elif "recipe 5/" in message:
                    task.progress = 90
                elif "image" in message.lower():
                    task.status = GenerationTaskStatus.GENERATING_IMAGES
                    task.progress = 95
                db.commit()
        
        # Generate recipes
        recipes = await recipe_service.generate_recipes_with_images(
            liked_foods=request.liked_foods,
            disliked_foods=request.disliked_foods,
            recipe_count=request.recipe_count,
            serving_size=request.serving_size,
            must_use_ingredients=request.must_use_ingredients,
            generate_images=request.generate_images,
            progress_callback=progress_callback,
            user_id=user_id,
            db_session=db
        )
        
        # Generate shopping list
        shopping_list = generate_shopping_list(recipes)
        
        # Save meal plan
        meal_plan = MealPlan(
            user_id=user_id,
            name=f"Meal Plan - {task.created_at.strftime('%Y-%m-%d')}",
            serving_size=request.serving_size,
            recipe_count=request.recipe_count,
            recipes_json=json.dumps(recipes),
            shopping_list_json=json.dumps(shopping_list),
            liked_foods_snapshot=",".join(request.liked_foods),
            disliked_foods_snapshot=",".join(request.disliked_foods),
            must_use_ingredients_snapshot=",".join(request.must_use_ingredients)
        )
        
        db.add(meal_plan)
        db.commit()
        db.refresh(meal_plan)
        
        # Update task as completed
        task = db.query(GenerationTask).filter(GenerationTask.id == task_id).first()
        task.status = GenerationTaskStatus.COMPLETED
        task.progress = 100
        task.current_step = "Recipe generation completed!"
        task.meal_plan_id = meal_plan.id
        db.commit()
        
    except Exception as e:
        # Update task as failed
        task = db.query(GenerationTask).filter(GenerationTask.id == task_id).first()
        if task:
            task.status = GenerationTaskStatus.FAILED
            task.error_message = str(e)
            task.current_step = f"Error: {str(e)}"
            db.commit()


@router.post("/generate", response_model=GenerationTaskResponse)
async def generate_recipes(
    request: RecipeGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Start recipe generation as background task"""
    
    # Create generation task
    task = GenerationTask(
        user_id=current_user.id,
        recipe_count=request.recipe_count,
        serving_size=request.serving_size,
        liked_foods=",".join(request.liked_foods),
        disliked_foods=",".join(request.disliked_foods),
        must_use_ingredients=",".join(request.must_use_ingredients)
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Add background task
    background_tasks.add_task(
        background_recipe_generation,
        task.id,
        current_user.id,
        request,
        db
    )
    
    return task


@router.get("/generate/{task_id}/status", response_model=GenerationTaskResponse)
async def get_generation_status(
    task_id: int,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get status of recipe generation task"""
    task = db.query(GenerationTask).filter(
        GenerationTask.id == task_id,
        GenerationTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@router.post("/generate-sync", response_model=MealPlanResponse)
async def generate_recipes_sync(
    request: RecipeGenerationRequest,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Generate recipes synchronously (for testing/simple cases)"""
    
    try:
        # Initialize recipe generator
        recipe_service = RecipeGeneratorService()
        
        # Generate recipes
        recipes = await recipe_service.generate_recipes_with_images(
            liked_foods=request.liked_foods,
            disliked_foods=request.disliked_foods,
            recipe_count=request.recipe_count,
            serving_size=request.serving_size,
            must_use_ingredients=request.must_use_ingredients,
            generate_images=request.generate_images,
            user_id=current_user.id,
            db_session=db
        )
        
        # Generate shopping list
        shopping_list = generate_shopping_list(recipes)
        
        # Save meal plan
        meal_plan = MealPlan(
            user_id=current_user.id,
            name=f"Meal Plan - {GenerationTask().created_at.strftime('%Y-%m-%d') if hasattr(GenerationTask(), 'created_at') else 'Now'}",
            serving_size=request.serving_size,
            recipe_count=request.recipe_count,
            recipes_json=json.dumps(recipes),
            shopping_list_json=json.dumps(shopping_list),
            liked_foods_snapshot=",".join(request.liked_foods),
            disliked_foods_snapshot=",".join(request.disliked_foods),
            must_use_ingredients_snapshot=",".join(request.must_use_ingredients)
        )
        
        db.add(meal_plan)
        db.commit()
        db.refresh(meal_plan)
        
        # Convert to response format
        return MealPlanResponse(
            id=meal_plan.id,
            name=meal_plan.name,
            serving_size=meal_plan.serving_size,
            recipe_count=meal_plan.recipe_count,
            recipes=recipes,
            shopping_list=shopping_list,
            created_at=meal_plan.created_at,
            rating=meal_plan.rating,
            notes=meal_plan.notes
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recipe generation failed: {str(e)}")


@router.get("/", response_model=List[MealPlanResponse])
async def get_user_meal_plans(
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get all meal plans for current user"""
    meal_plans = db.query(MealPlan).filter(
        MealPlan.user_id == current_user.id
    ).order_by(MealPlan.created_at.desc()).all()
    
    result = []
    for meal_plan in meal_plans:
        recipes = json.loads(meal_plan.recipes_json)
        shopping_list = json.loads(meal_plan.shopping_list_json)
        
        result.append(MealPlanResponse(
            id=meal_plan.id,
            name=meal_plan.name,
            serving_size=meal_plan.serving_size,
            recipe_count=meal_plan.recipe_count,
            recipes=recipes,
            shopping_list=shopping_list,
            created_at=meal_plan.created_at,
            rating=meal_plan.rating,
            notes=meal_plan.notes
        ))
    
    return result


@router.get("/{meal_plan_id}", response_model=MealPlanResponse)
async def get_meal_plan(
    meal_plan_id: int,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific meal plan"""
    meal_plan = db.query(MealPlan).filter(
        MealPlan.id == meal_plan_id,
        MealPlan.user_id == current_user.id
    ).first()
    
    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    recipes = json.loads(meal_plan.recipes_json)
    shopping_list = json.loads(meal_plan.shopping_list_json)
    
    return MealPlanResponse(
        id=meal_plan.id,
        name=meal_plan.name,
        serving_size=meal_plan.serving_size,
        recipe_count=meal_plan.recipe_count,
        recipes=recipes,
        shopping_list=shopping_list,
        created_at=meal_plan.created_at,
        rating=meal_plan.rating,
        notes=meal_plan.notes
    )