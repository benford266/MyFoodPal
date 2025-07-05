#!/usr/bin/env python3
"""
Debug the full recipe generation process
"""

import asyncio
import sys
sys.path.append('.')

from src.services.recipe_generator import RecipeGenerator
from src.config import OLLAMA_BASE_URL, OLLAMA_MODEL

async def debug_generation():
    print(f"Debugging with {OLLAMA_MODEL}")
    
    generator = RecipeGenerator(OLLAMA_BASE_URL, OLLAMA_MODEL)
    
    # Test full generation process
    liked_foods = ["chicken", "pasta"]
    disliked_foods = ["mushrooms"]
    must_use_ingredients = ["spinach"]
    
    print("Running full recipe generation...")
    recipes = await generator.generate_recipes(
        liked_foods=liked_foods,
        disliked_foods=disliked_foods,
        recipe_count=2,
        serving_size=4,
        progress_callback=None,
        user_id=None,
        db_session=None,
        must_use_ingredients=must_use_ingredients
    )
    
    print(f"\n📋 Generated {len(recipes)} recipes:")
    for i, recipe in enumerate(recipes, 1):
        print(f"\n🍽️ Recipe {i}: {recipe.get('name', 'Unknown')}")
        if 'error' in recipe:
            print(f"   ❌ Error: {recipe['error']}")
        else:
            # Check for must-use ingredients
            recipe_text = str(recipe).lower()
            for ingredient in must_use_ingredients:
                if ingredient.lower() in recipe_text:
                    print(f"   ✅ Contains must-use: {ingredient}")
                else:
                    print(f"   ⚠️  Missing must-use: {ingredient}")
            
            print(f"   📝 Ingredients: {len(recipe.get('ingredients', []))}")
            print(f"   👨‍🍳 Instructions: {len(recipe.get('instructions', []))}")

if __name__ == "__main__":
    asyncio.run(debug_generation())