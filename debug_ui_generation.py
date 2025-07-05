#!/usr/bin/env python3
"""
Debug the UI recipe generation issue
"""

import asyncio
import sys
sys.path.append('.')

from src.services.recipe_generator import RecipeGenerator
from src.config import OLLAMA_BASE_URL, OLLAMA_MODEL

async def debug_ui_issue():
    print(f"Debugging UI generation failure...")
    print(f"  Ollama URL: {OLLAMA_BASE_URL}")
    print(f"  Model: {OLLAMA_MODEL}")
    
    generator = RecipeGenerator(OLLAMA_BASE_URL, OLLAMA_MODEL)
    
    # Simulate UI call exactly
    liked_foods = ["chicken", "pasta"]
    disliked_foods = ["mushrooms"]
    must_use_ingredients = ["spinach"]
    
    async def progress_callback(message: str):
        print(f"Progress: {message}")
    
    try:
        recipes = await generator.generate_recipes(
            liked_foods=liked_foods,
            disliked_foods=disliked_foods, 
            recipe_count=3,
            serving_size=4,
            progress_callback=progress_callback,
            user_id=None,
            db_session=None,
            must_use_ingredients=must_use_ingredients
        )
        
        print(f"\n✅ Generated {len(recipes)} recipes")
        
        for i, recipe in enumerate(recipes, 1):
            print(f"\n📋 Recipe {i}:")
            print(f"  Type: {type(recipe)}")
            
            if isinstance(recipe, str):
                print(f"  ❌ Recipe is a string: {recipe[:100]}...")
                continue
            elif isinstance(recipe, dict):
                print(f"  ✅ Recipe is dict")
                print(f"  Name: {recipe.get('name', 'Unknown')}")
                print(f"  Has error: {'error' in recipe}")
                if 'error' in recipe:
                    print(f"  Error: {recipe['error']}")
            else:
                print(f"  ⚠️  Recipe is unexpected type: {type(recipe)}")
                print(f"  Content: {recipe}")
    
    except Exception as e:
        print(f"❌ Generation failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_ui_issue())