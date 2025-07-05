#!/usr/bin/env python3
"""
Test script to debug recipe generation issues
"""

import asyncio
import sys
sys.path.append('.')

from src.services.recipe_generator import RecipeGenerator
from src.config import OLLAMA_BASE_URL, OLLAMA_MODEL

async def test_recipe_generation():
    print(f"Testing recipe generation with:")
    print(f"  Ollama URL: {OLLAMA_BASE_URL}")
    print(f"  Model: {OLLAMA_MODEL}")
    print()
    
    generator = RecipeGenerator(OLLAMA_BASE_URL, OLLAMA_MODEL)
    
    # Test with simple preferences
    liked_foods = ["chicken", "pasta", "garlic"]
    disliked_foods = ["mushrooms"]
    must_use_ingredients = ["spinach", "tomatoes"]
    
    print("Generating a single test recipe...")
    print(f"  Liked foods: {', '.join(liked_foods)}")
    print(f"  Disliked foods: {', '.join(disliked_foods)}")
    print(f"  Must use: {', '.join(must_use_ingredients)}")
    print()
    
    try:
        # Set up must-use tracking like the main generation does
        generator._must_use_recipe = 1
        
        recipe = await generator.generate_single_recipe(
            recipe_number=1,
            liked_foods=liked_foods,
            disliked_foods=disliked_foods,
            existing_ingredients=None,
            progress_callback=None,
            total_recipes=1,
            serving_size=4,
            used_carbs=None,
            user_id=None,
            db_session=None,
            must_use_ingredients=must_use_ingredients
        )
        
        print("✅ Recipe generation successful!")
        print(f"Recipe name: {recipe.get('name', 'Unknown')}")
        print(f"Has ingredients: {'ingredients' in recipe}")
        print(f"Has instructions: {'instructions' in recipe}")
        
        if "error" in recipe:
            print(f"❌ Recipe has error: {recipe['error']}")
            if "raw_response" in recipe:
                print(f"Raw response: {recipe['raw_response'][:200]}...")
        else:
            print("Recipe looks good!")
            
            # Check if must-use ingredients are in the recipe
            ingredients_text = str(recipe.get('ingredients', [])).lower()
            instructions_text = str(recipe.get('instructions', [])).lower()
            
            for ingredient in must_use_ingredients:
                if ingredient.lower() in ingredients_text or ingredient.lower() in instructions_text:
                    print(f"✅ Found must-use ingredient: {ingredient}")
                else:
                    print(f"⚠️  Missing must-use ingredient: {ingredient}")
        
    except Exception as e:
        print(f"❌ Recipe generation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_recipe_generation())