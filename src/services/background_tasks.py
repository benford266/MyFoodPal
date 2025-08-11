"""Background task service for recipe generation"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import weakref
import gc

from ..database.connection import get_db_context
from ..database.operations import (
    get_generation_task, update_generation_task_progress, 
    complete_generation_task, create_meal_plan
)
from ..database.models import GenerationTaskStatus, MealPlan
from ..models.schemas import MealPlanCreate
from ..services.recipe_generator import RecipeGenerator
from ..utils.shopping_list import generate_shopping_list
from ..config import LM_STUDIO_BASE_URL, LM_STUDIO_MODEL

logger = logging.getLogger(__name__)


class BackgroundTaskService:
    """Service for managing background recipe generation tasks with resource optimization"""
    
    def __init__(self, max_concurrent_tasks: int = 3):
        self.active_tasks: Dict[int, asyncio.Task] = {}
        self.max_concurrent_tasks = max_concurrent_tasks
        self.task_semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.task_queue = asyncio.Queue(maxsize=10)  # Limit pending tasks
        self.recipe_generator = None  # Lazy initialization
        self._shutdown = False
        
        # Use weak references for cleanup
        self.task_callbacks = weakref.WeakValueDictionary()
        
        # Background cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _get_recipe_generator(self) -> RecipeGenerator:
        """Lazy initialization of recipe generator"""
        if self.recipe_generator is None:
            self.recipe_generator = RecipeGenerator(LM_STUDIO_BASE_URL, LM_STUDIO_MODEL)
        return self.recipe_generator
    
    def _start_cleanup_task(self):
        """Start background cleanup task"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def _periodic_cleanup(self):
        """Periodically clean up completed tasks and free memory"""
        while not self._shutdown:
            try:
                # Clean up completed tasks
                completed_tasks = [
                    task_id for task_id, task in self.active_tasks.items()
                    if task.done()
                ]
                
                for task_id in completed_tasks:
                    task = self.active_tasks.pop(task_id, None)
                    if task:
                        try:
                            # Get result to prevent warnings
                            await task
                        except Exception as e:
                            logger.warning(f"Background task {task_id} completed with error: {e}")
                        logger.info(f"Cleaned up completed task {task_id}")
                
                # Force garbage collection if we have many completed tasks
                if len(completed_tasks) > 2:
                    gc.collect()
                
                # Wait before next cleanup
                await asyncio.sleep(60)  # Clean up every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
                await asyncio.sleep(60)
    
    async def start_generation_task(self, task_id: int):
        """Start a background generation task with resource limits"""
        if task_id in self.active_tasks:
            logger.warning(f"Task {task_id} already running")
            return
        
        # Check if we've hit the concurrent task limit
        if len(self.active_tasks) >= self.max_concurrent_tasks:
            logger.warning(f"Maximum concurrent tasks ({self.max_concurrent_tasks}) reached, queuing task {task_id}")
            try:
                await asyncio.wait_for(self.task_queue.put(task_id), timeout=5.0)
                logger.info(f"Task {task_id} queued for later execution")
                return
            except asyncio.TimeoutError:
                logger.error(f"Task queue full, rejecting task {task_id}")
                return None
        
        # Create asyncio task for background execution with resource limits
        task = asyncio.create_task(self._run_generation_task_with_limits(task_id))
        self.active_tasks[task_id] = task
        
        logger.info(f"Started background generation task {task_id}")
        return task
    
    async def _run_generation_task_with_limits(self, task_id: int):
        """Run generation task with semaphore limits"""
        async with self.task_semaphore:
            try:
                await self._run_generation_task(task_id)
            finally:
                # Process queued tasks after this one completes
                try:
                    if not self.task_queue.empty():
                        next_task_id = await asyncio.wait_for(self.task_queue.get(), timeout=0.1)
                        logger.info(f"Starting queued task {next_task_id}")
                        await self.start_generation_task(next_task_id)
                except asyncio.TimeoutError:
                    pass  # No queued tasks
    
    async def _run_generation_task(self, task_id: int):
        """Run the actual generation task with proper resource management"""
        try:
            with get_db_context() as db:
                generation_task = get_generation_task(db, task_id)
                
                if not generation_task:
                    logger.error(f"Generation task {task_id} not found")
                    return
        
                logger.info(f"Running generation task {task_id} for user {generation_task.user_id}")
                
                # Parse input parameters
                liked_foods = [f.strip() for f in generation_task.liked_foods.split(',') if f.strip()]
                disliked_foods = [f.strip() for f in generation_task.disliked_foods.split(',') if f.strip()]
                must_use_ingredients = [f.strip() for f in generation_task.must_use_ingredients.split(',') if f.strip()]
                
                # Create progress callback with database context
                async def progress_callback(message: str):
                    try:
                        with get_db_context() as progress_db:
                            # Parse progress from message
                            progress = 0
                            status = GenerationTaskStatus.GENERATING_RECIPES
                            
                            if "Generating recipe" in message and "/" in message:
                                try:
                                    parts = message.split('/')
                                    if len(parts) >= 2:
                                        recipe_num = int(parts[0].split()[-1])
                                        total_recipes = int(parts[1].split()[0])
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
                                        progress = int(50 + (image_num / total_images) * 50)
                                        status = GenerationTaskStatus.GENERATING_IMAGES
                                except:
                                    pass
                            elif "Generating recipe images..." in message:
                                progress = 50
                                status = GenerationTaskStatus.GENERATING_IMAGES
                            
                            # Update database
                            update_generation_task_progress(progress_db, task_id, status, progress, message)
                            logger.debug(f"Task {task_id} progress: {progress}% - {message}")
                    except Exception as e:
                        logger.error(f"Error updating progress for task {task_id}: {e}")
                
                # Generate recipes with images
                recipe_generator = self._get_recipe_generator()
                recipes = await recipe_generator.generate_recipes_with_images(
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
                
                # Save meal plan in new database context
                await progress_callback("Saving meal plan...")
                with get_db_context() as save_db:
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
                    
                    meal_plan = create_meal_plan(save_db, meal_plan_data, generation_task.user_id)
                    
                    # Mark task as completed
                    complete_generation_task(save_db, task_id, meal_plan.id)
                    
                    logger.info(f"Background generation task {task_id} completed successfully")
                    logger.info(f"Created meal plan {meal_plan.id} with {len(recipes)} recipes")
                    
        except Exception as e:
            logger.error(f"Background generation task {task_id} failed: {str(e)}")
            try:
                with get_db_context() as error_db:
                    complete_generation_task(error_db, task_id, error_message=str(e))
            except Exception as cleanup_error:
                logger.error(f"Failed to mark task {task_id} as failed: {cleanup_error}")
        
        finally:
            # Clean up task reference
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                logger.debug(f"Cleaned up task reference for {task_id}")
            
            # Force garbage collection for large tasks
            gc.collect()
    
    def get_task_status(self, task_id: int) -> bool:
        """Check if a task is currently running"""
        return task_id in self.active_tasks
    
    def cancel_task(self, task_id: int):
        """Cancel a running task"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
            del self.active_tasks[task_id]
            logger.info(f"Cancelled background generation task {task_id}")
    
    async def shutdown(self):
        """Gracefully shutdown the background service"""
        logger.info("Shutting down background task service...")
        self._shutdown = True
        
        # Cancel all active tasks
        for task_id, task in list(self.active_tasks.items()):
            logger.info(f"Cancelling active task {task_id}")
            task.cancel()
            try:
                await asyncio.wait_for(task, timeout=5.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
        
        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Clear all tasks
        self.active_tasks.clear()
        logger.info("Background task service shutdown complete")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics for monitoring"""
        return {
            'active_tasks': len(self.active_tasks),
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'queue_size': self.task_queue.qsize(),
            'shutdown': self._shutdown,
            'active_task_ids': list(self.active_tasks.keys())
        }


# Global instance
background_service = BackgroundTaskService()


async def start_background_generation(task_id: int):
    """Convenience function to start a background generation task"""
    return await background_service.start_generation_task(task_id)