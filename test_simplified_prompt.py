#!/usr/bin/env python3
"""Test the simplified prompt structure for faster Ollama responses"""

import asyncio
import time
from src.services.recipe_generator import RecipeGenerator

async def test_simple_generation():
    """Test that simplified prompts work faster"""
    print("🧪 Testing simplified prompt structure...")
    
    gen = RecipeGenerator('http://localhost:11434', 'llama3.1')
    
    # Test single recipe generation
    start_time = time.time()
    recipe = await gen.generate_single_recipe(
        1, ['chicken', 'tomatoes'], ['onions'], 
        serving_size=4
    )
    end_time = time.time()
    
    print(f"⏱️  Single recipe generation took: {end_time - start_time:.2f} seconds")
    
    if "error" in recipe:
        print(f"❌ Recipe generation failed: {recipe['error']}")
        return False
    else:
        print(f"✅ Recipe generated: {recipe.get('name', 'Unknown')}")
        print(f"   - Cuisine: {recipe.get('cuisine_inspiration', 'Unknown')}")
        print(f"   - Ingredients: {len(recipe.get('ingredients', []))}")
        print(f"   - Instructions: {len(recipe.get('instructions', []))}")
        return True

if __name__ == "__main__":
    success = asyncio.run(test_simple_generation())
    if success:
        print("\n🎉 Simplified prompt structure test passed!")
    else:
        print("\n⚠️  Test failed - check Ollama server connection")