#!/usr/bin/env python3
"""
Test multiple recipe generation
"""

import asyncio
import sys
sys.path.append('.')

from src.services.recipe_generator import RecipeGenerator
from src.config import OLLAMA_BASE_URL, OLLAMA_MODEL

async def test_multiple():
    print("Testing multiple recipe generation...")
    
    generator = RecipeGenerator(OLLAMA_BASE_URL, OLLAMA_MODEL)
    
    try:
        recipes = await generator.generate_recipes(
            liked_foods=["chicken"],
            disliked_foods=[],
            recipe_count=2,  # Just 2 recipes to keep it fast
            serving_size=4,
            progress_callback=None,
            user_id=None,
            db_session=None,
            must_use_ingredients=["spinach"]
        )
        
        print(f"✅ Generated {len(recipes)} recipes")
        for i, recipe in enumerate(recipes, 1):
            print(f"Recipe {i}: type={type(recipe)}")
            if isinstance(recipe, dict):
                print(f"  Name: {recipe.get('name', 'Unknown')}")
                print(f"  Has error: {'error' in recipe}")
            
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_multiple())