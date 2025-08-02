"""Background task service for recipe generation"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from ..database.connection import get_db
from ..database.operations import (
    get_generation_task, update_generation_task_progress, 
    complete_generation_task, create_meal_plan
)
from ..database.models import GenerationTaskStatus, MealPlan
from ..models.schemas import MealPlanCreate
from ..services.recipe_generator import RecipeGenerator
from ..utils.shopping_list import generate_shopping_list
from ..config import LM_STUDIO_BASE_URL, LM_STUDIO_MODEL


class BackgroundTaskService:
    """Service for managing background recipe generation tasks"""
    
    def __init__(self):
        self.active_tasks: Dict[int, asyncio.Task] = {}
        self.recipe_generator = RecipeGenerator(LM_STUDIO_BASE_URL, LM_STUDIO_MODEL)
    
    async def start_generation_task(self, task_id: int):
        """Start a background generation task"""
        if task_id in self.active_tasks:
            print(f"⚠️ Task {task_id} already running")
            return
        
        # Create asyncio task for background execution
        task = asyncio.create_task(self._run_generation_task(task_id))
        self.active_tasks[task_id] = task
        
        print(f"🚀 Started background generation task {task_id}")
        return task
    
    async def _run_generation_task(self, task_id: int):
        """Run the actual generation task"""
        db = next(get_db())
        generation_task = get_generation_task(db, task_id)
        
        if not generation_task:
            print(f"❌ Generation task {task_id} not found")
            return
        
        try:
            print(f"🔍 Running generation task {task_id} for user {generation_task.user_id}")
            
            # Parse input parameters
            liked_foods = [f.strip() for f in generation_task.liked_foods.split(',') if f.strip()]
            disliked_foods = [f.strip() for f in generation_task.disliked_foods.split(',') if f.strip()]
            must_use_ingredients = [f.strip() for f in generation_task.must_use_ingredients.split(',') if f.strip()]
            
            # Create progress callback
            async def progress_callback(message: str):
                # Parse progress from message
                progress = 0
                status = GenerationTaskStatus.GENERATING_RECIPES
                
                if "Generating recipe" in message and "/" in message:
                    try:
                        parts = message.split('/')
                        if len(parts) >= 2:
                            recipe_num = int(parts[0].split()[-1])
                            total_recipes = int(parts[1].split()[0])
                            # Recipe generation is first half (0-50%)
                            progress = int((recipe_num / total_recipes) * 50)
                            status = GenerationTaskStatus.GENERATING_RECIPES
                    except:
                        pass
                elif "Generating image" in message and "/" in message:
                    try:
                        parts = message.split('/')
                        if len(parts) >= 2:
                            image_num = int(parts[0].split()[-1])
                            total_images = int(parts[1].split(':')[0])
                            # Image generation is second half (50-100%)
                            progress = int(50 + (image_num / total_images) * 50)
                            status = GenerationTaskStatus.GENERATING_IMAGES
                    except:
                        pass
                elif "Generating recipe images..." in message:
                    progress = 50
                    status = GenerationTaskStatus.GENERATING_IMAGES
                
                # Update database
                update_generation_task_progress(db, task_id, status, progress, message)
                print(f"📊 Task {task_id} progress: {progress}% - {message}")
            
            # Generate recipes with images
            recipes = await self.recipe_generator.generate_recipes_with_images(
                liked_foods=liked_foods,
                disliked_foods=disliked_foods,
                recipe_count=generation_task.recipe_count,
                serving_size=generation_task.serving_size,
                progress_callback=progress_callback,
                user_id=generation_task.user_id,
                db_session=db,
                must_use_ingredients=must_use_ingredients,
                generate_images=True,
                comfyui_server="192.168.4.208:8188"
            )
            
            # Generate shopping list
            await progress_callback("Generating shopping list...")
            shopping_list = generate_shopping_list(recipes)
            
            # Save meal plan
            await progress_callback("Saving meal plan...")
            meal_plan_data = MealPlanCreate(
                name=f"Meal Plan - {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
                serving_size=generation_task.serving_size,
                recipe_count=generation_task.recipe_count,
                recipes_json=json.dumps(recipes),
                shopping_list_json=json.dumps(shopping_list),
                liked_foods_snapshot=generation_task.liked_foods,
                disliked_foods_snapshot=generation_task.disliked_foods,
                must_use_ingredients_snapshot=generation_task.must_use_ingredients
            )
            
            meal_plan = create_meal_plan(db, meal_plan_data, generation_task.user_id)
            
            # Mark task as completed
            complete_generation_task(db, task_id, meal_plan.id)
            
            print(f"✅ Background generation task {task_id} completed successfully")
            print(f"   Created meal plan {meal_plan.id} with {len(recipes)} recipes")
            
        except Exception as e:
            print(f"❌ Background generation task {task_id} failed: {str(e)}")
            complete_generation_task(db, task_id, error_message=str(e))
        
        finally:
            # Clean up task reference
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            db.close()
    
    def get_task_status(self, task_id: int) -> bool:
        """Check if a task is currently running"""
        return task_id in self.active_tasks
    
    def cancel_task(self, task_id: int):
        """Cancel a running task"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
            del self.active_tasks[task_id]
            print(f"🚫 Cancelled background generation task {task_id}")


# Global instance
background_service = BackgroundTaskService()


async def start_background_generation(task_id: int):
    """Convenience function to start a background generation task"""
    return await background_service.start_generation_task(task_id)