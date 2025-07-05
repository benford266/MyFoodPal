#!/usr/bin/env python3
"""
Quick test of single recipe generation
"""

import asyncio
import sys
sys.path.append('.')

from src.services.recipe_generator import RecipeGenerator
from src.config import OLLAMA_BASE_URL, OLLAMA_MODEL

async def quick_test():
    print("Quick single recipe test...")
    
    generator = RecipeGenerator(OLLAMA_BASE_URL, OLLAMA_MODEL)
    
    try:
        # Test just one recipe
        generator._must_use_recipe = 1
        
        recipe = await generator.generate_single_recipe(
            recipe_number=1,
            liked_foods=["chicken"],
            disliked_foods=[],
            existing_ingredients=None,
            progress_callback=None,
            total_recipes=1,
            serving_size=4,
            used_carbs=None,
            user_id=None,
            db_session=None,
            must_use_ingredients=["spinach"]
        )
        
        print(f"Result type: {type(recipe)}")
        print(f"Result: {recipe}")
        
        if isinstance(recipe, dict):
            print("✅ Got dictionary")
            if "error" in recipe:
                print(f"❌ Has error: {recipe['error']}")
            else:
                print(f"✅ Recipe name: {recipe.get('name')}")
        else:
            print(f"❌ Not a dictionary: {recipe}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(quick_test())