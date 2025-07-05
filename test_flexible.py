#!/usr/bin/env python3
"""
Test flexible recipe generation
"""

import asyncio
import sys
sys.path.append('.')

from src.services.recipe_generator import RecipeGenerator
from src.config import OLLAMA_BASE_URL, OLLAMA_MODEL

async def test_flexibility():
    print("Testing flexible recipe generation...")
    
    generator = RecipeGenerator(OLLAMA_BASE_URL, OLLAMA_MODEL)
    
    test_cases = [
        {
            "name": "Empty preferences",
            "liked": [],
            "disliked": [],
            "must_use": []
        },
        {
            "name": "Only likes chicken",
            "liked": ["chicken"],
            "disliked": [],
            "must_use": []
        },
        {
            "name": "Avoids mushrooms only",
            "liked": [],
            "disliked": ["mushrooms"],
            "must_use": []
        },
        {
            "name": "Likes pasta, must use spinach",
            "liked": ["pasta"],
            "disliked": [],
            "must_use": ["spinach"]
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Test: {test_case['name']}")
        print(f"   Likes: {test_case['liked'] or 'None'}")
        print(f"   Dislikes: {test_case['disliked'] or 'None'}")
        print(f"   Must use: {test_case['must_use'] or 'None'}")
        
        try:
            recipes = await generator.generate_recipes(
                liked_foods=test_case['liked'],
                disliked_foods=test_case['disliked'],
                recipe_count=1,  # Just one recipe per test
                serving_size=4,
                progress_callback=None,
                user_id=None,
                db_session=None,
                must_use_ingredients=test_case['must_use']
            )
            
            if recipes and len(recipes) > 0:
                recipe = recipes[0]
                if isinstance(recipe, dict) and 'error' not in recipe:
                    print(f"   ✅ Generated: {recipe.get('name', 'Unknown')}")
                    
                    # Check ingredients
                    ingredients = recipe.get('ingredients', [])
                    ingredient_names = []
                    for ing in ingredients:
                        if isinstance(ing, dict):
                            ingredient_names.append(ing.get('item', ''))
                    
                    print(f"   📝 Ingredients: {', '.join(ingredient_names[:5])}...")
                    
                    # Check if liked foods are included when specified
                    if test_case['liked']:
                        for liked in test_case['liked']:
                            recipe_text = str(recipe).lower()
                            if liked.lower() in recipe_text:
                                print(f"   💚 Includes preferred: {liked}")
                    
                    # Check if must-use ingredients are included
                    if test_case['must_use']:
                        for must_use in test_case['must_use']:
                            recipe_text = str(recipe).lower()
                            if must_use.lower() in recipe_text:
                                print(f"   🕐 Includes must-use: {must_use}")
                else:
                    print(f"   ❌ Failed: {recipe.get('error', 'Unknown error')}")
            else:
                print("   ❌ No recipes generated")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_flexibility())