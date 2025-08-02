import httpx
import json
import re
import aiohttp
from typing import List, Dict, Any

class RecipeGenerator:
    def __init__(self, lm_studio_url: str, model: str):
        self.lm_studio_url = lm_studio_url
        self.model = model
        self.reset_diversity_tracking()
    
    def reset_diversity_tracking(self):
        """Reset diversity tracking for a new meal plan"""
        self.used_cooking_inspirations = []
    
    async def generate_single_recipe(self, recipe_number: int, liked_foods: List[str], disliked_foods: List[str], 
                                   existing_ingredients: List[str] = None, progress_callback=None, total_recipes: int = 5, serving_size: int = 4, used_carbs: List[str] = None, user_id: int = None, db_session=None, must_use_ingredients: List[str] = None) -> Dict[str, Any]:
        """Generate a single recipe with cuisine diversity and carb variety"""
        
        # Simplified cuisine/style selection
        cuisines = ["Italian", "Asian", "Mexican", "Mediterranean", "Indian", "French", "Thai", "Middle Eastern"]
        import random
        
        # Get previously used elements to avoid repetition
        used_inspirations = getattr(self, 'used_cooking_inspirations', []) if hasattr(self, 'used_cooking_inspirations') else []
        
        # Select diverse cuisine, avoiding recent ones
        available_cuisines = [c for c in cuisines if c not in used_inspirations[-3:]]
        if not available_cuisines: available_cuisines = cuisines
        
        selected_cuisine = random.choice(available_cuisines)
        
        # Track used elements
        if not hasattr(self, 'used_cooking_inspirations'): self.used_cooking_inspirations = []
        self.used_cooking_inspirations.append(selected_cuisine)
        
        # Build simplified prompt components
        must_use_text = ""
        if must_use_ingredients and hasattr(self, '_must_use_recipe') and recipe_number == self._must_use_recipe:
            must_use_text = f"MUST INCLUDE: {', '.join(must_use_ingredients)}. "
        
        # Simplify preferences - only use top 2 of each
        preferences = []
        if liked_foods:
            preferences.append(f"Include: {', '.join(liked_foods[:2])}")
        if disliked_foods:
            preferences.append(f"Avoid: {', '.join(disliked_foods[:2])}")
        
        preferences_text = ". ".join(preferences) if preferences else ""
        
        # Add carb variety constraint
        carb_text = ""
        if used_carbs:
            carb_text = f"Use a different carbohydrate base than these already used: {', '.join(used_carbs[:2])}. Choose something different like rice, pasta, potatoes, quinoa, etc. "
        
        # Add some variety to prevent model from getting stuck in patterns
        recipe_styles = ["hearty", "light and fresh", "comfort food", "restaurant-style", "family-friendly"]
        import random
        style_hint = random.choice(recipe_styles)
        
        # Enhanced prompt with better context and guidance
        prompt = f"""You are a professional chef creating a delicious {selected_cuisine} dinner recipe for {serving_size} people. Make this a {style_hint} dish.

REQUIREMENTS:
- Create a complete, practical recipe that can be cooked at home
- {must_use_text}{carb_text}{preferences_text}
- Use realistic ingredient quantities and cooking times
- Provide clear, step-by-step instructions
- Ensure the recipe is balanced and nutritious
- Make this recipe unique and different from typical generic recipes

RESPONSE FORMAT: Return ONLY valid JSON with no additional text or explanations.

{{
    "name": "Descriptive Recipe Name (e.g., 'Garlic Herb Grilled Chicken with Roasted Vegetables')",
    "prep_time": "realistic prep time (e.g., '15 minutes')",
    "cook_time": "realistic cooking time (e.g., '25 minutes')", 
    "servings": {serving_size},
    "cuisine_inspiration": "{selected_cuisine}",
    "difficulty": "Easy/Medium/Hard",
    "ingredients": [
        {{"item": "specific ingredient name", "quantity": "precise amount", "unit": "g/ml/tbsp/tsp/cup/piece"}},
        {{"item": "main protein (chicken/beef/fish/tofu)", "quantity": "400-600", "unit": "g"}},
        {{"item": "fresh vegetables (be specific)", "quantity": "200-400", "unit": "g"}},
        {{"item": "carbohydrate (rice/pasta/potatoes)", "quantity": "200-300", "unit": "g"}},
        {{"item": "seasonings/spices (be specific)", "quantity": "1-2", "unit": "tsp"}},
        {{"item": "cooking oil/fat", "quantity": "15-30", "unit": "ml"}}
    ],
    "instructions": [
        "Step 1: Detailed preparation instructions with timing",
        "Step 2: Cooking method with temperature/heat level",
        "Step 3: Specific cooking techniques and visual cues",
        "Step 4: How to combine ingredients properly",
        "Step 5: Final preparation and serving suggestions"
    ]
}}

Generate a complete, authentic {selected_cuisine} recipe now:"""
        
        try:
            if progress_callback:
                await progress_callback(f"Generating recipe {recipe_number}/{total_recipes}...")
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.lm_studio_url}/v1/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000
                    },
                    timeout=60.0  # Reduced timeout for simplified prompt
                )
                
                if response.status_code == 200:
                    result = response.json()
                    from ..utils.recipe_parser import parse_recipe_response
                    # LM Studio returns response in OpenAI format
                    content = result['choices'][0]['message']['content']
                    recipe = parse_recipe_response(content, recipe_number, serving_size)
                    
                    # Check for similarity with user history if available
                    if user_id and db_session and "error" not in recipe:
                        try:
                            from ..database.operations import check_recipe_similarity, save_recipe_to_history
                            
                            # Check if too similar to recent recipes
                            is_similar = check_recipe_similarity(
                                db_session, user_id, recipe, 
                                "simplified", "simplified", "simplified", selected_cuisine
                            )
                            
                            if is_similar:
                                print(f"🔄 Recipe {recipe_number} too similar to recent history, will need regeneration")
                                # Could implement retry logic here if needed
                                recipe["_warning"] = "Similar to recent recipes"
                            else:
                                # Save to history for future reference
                                save_recipe_to_history(
                                    db_session, user_id, recipe,
                                    "simplified", "simplified", "simplified", selected_cuisine
                                )
                                print(f"✅ Recipe {recipe_number} saved to user history")
                                
                        except Exception as e:
                            print(f"Warning: History check failed for recipe {recipe_number}: {e}")
                    
                    return recipe
                else:
                    return {"error": f"LM Studio API error for recipe {recipe_number}: {response.status_code}"}
        
        except Exception as e:
            # Return a simple fallback recipe instead of just an error
            fallback_name = f"Simple Recipe {recipe_number}"
            if must_use_ingredients and hasattr(self, '_must_use_recipe') and recipe_number == self._must_use_recipe:
                fallback_name = f"Recipe with {', '.join(must_use_ingredients)}"
            
            # Create a more detailed fallback recipe
            fallback_ingredients = []
            
            # Add must-use ingredients if applicable
            if must_use_ingredients and hasattr(self, '_must_use_recipe') and recipe_number == self._must_use_recipe:
                for ing in must_use_ingredients:
                    fallback_ingredients.append({"item": ing, "quantity": "200", "unit": "g"})
            
            # Add basic recipe components
            fallback_ingredients.extend([
                {"item": "chicken breast or protein of choice", "quantity": "500", "unit": "g"},
                {"item": "mixed vegetables (carrots, bell peppers, onions)", "quantity": "300", "unit": "g"},
                {"item": "rice or pasta", "quantity": "250", "unit": "g"},
                {"item": "olive oil", "quantity": "30", "unit": "ml"},
                {"item": "salt and pepper", "quantity": "1", "unit": "tsp"},
                {"item": "garlic powder", "quantity": "1", "unit": "tsp"}
            ])
            
            return {
                "name": f"Simple Home-Style {selected_cuisine} Dinner",
                "prep_time": "15 minutes",
                "cook_time": "25 minutes",
                "servings": serving_size,
                "cuisine_inspiration": selected_cuisine,
                "difficulty": "Easy",
                "ingredients": fallback_ingredients,
                "instructions": [
                    "Heat olive oil in a large skillet over medium-high heat",
                    "Season protein with salt, pepper, and garlic powder, then cook for 6-8 minutes until golden",
                    "Add chopped vegetables to the pan and cook for 5-7 minutes until tender",
                    "Meanwhile, prepare rice or pasta according to package instructions",
                    "Combine cooked protein and vegetables, adjust seasoning to taste",
                    "Serve over rice or pasta while hot"
                ],
                "_note": f"Fallback recipe generated due to API error: {str(e)}"
            }

    async def generate_recipes(self, liked_foods: List[str], disliked_foods: List[str], recipe_count: int = 5, serving_size: int = 4, progress_callback=None, user_id: int = None, db_session=None, must_use_ingredients: List[str] = None) -> List[Dict[str, Any]]:
        """Generate specified number of recipes one at a time, sharing ingredients where possible and ensuring maximum diversity"""
        # Reset diversity tracking for this meal plan
        self.reset_diversity_tracking()
        
        # If we have must-use ingredients, randomly choose which recipe will feature them
        if must_use_ingredients:
            import random
            self._must_use_recipe = random.randint(1, recipe_count)
            print(f"🕐 Must-use ingredients will be featured in recipe #{self._must_use_recipe}")
        
        recipes = []
        all_ingredients = []
        used_carbohydrates = []
        used_cooking_styles = []
        used_cuisines = []
        
        # Common carbohydrate ingredients to track for variety
        carb_keywords = ['rice', 'pasta', 'noodle', 'potato', 'quinoa', 'bulgur', 'couscous', 'polenta', 'bread', 'barley', 'sweet potato', 'lentil', 'chickpea', 'bean', 'flour', 'wheat', 'oat', 'corn', 'maize']
        
        for i in range(1, recipe_count + 1):  # Generate specified number of recipes
            # Only pass used carbs for variety, not all ingredients (which was causing issues)
            used_carbs = used_carbohydrates[-2:] if i > 1 and used_carbohydrates else None
            
            recipe = await self.generate_single_recipe(
                i, liked_foods, disliked_foods, None, progress_callback, recipe_count, serving_size, used_carbs, user_id, db_session, must_use_ingredients
            )
            
            if "error" in recipe:
                # If one recipe fails, continue with others
                recipes.append(recipe)
                continue
                
            recipes.append(recipe)
            
            # Track used styles and cuisines for variety
            if recipe.get("cuisine_inspiration"):
                used_cuisines.append(recipe["cuisine_inspiration"].lower())
            
            # Extract ingredients from this recipe for next recipes
            if "ingredients" in recipe:
                for ingredient in recipe["ingredients"]:
                    # Skip if ingredient is not a dict
                    if not isinstance(ingredient, dict):
                        continue
                        
                    item = ingredient.get("item", "").lower()
                    if item and item not in [ing.lower() for ing in all_ingredients]:
                        all_ingredients.append(ingredient.get("item", ""))
                    
                    # Check if this ingredient is a carbohydrate and track it for variety
                    for carb_keyword in carb_keywords:
                        if carb_keyword in item and item not in [carb.lower() for carb in used_carbohydrates]:
                            used_carbohydrates.append(ingredient.get("item", ""))
                            break  # Only add once per ingredient
        
        # Add generation summary for debugging/logging
        if recipes:
            cuisines_used = [r.get("cuisine_inspiration", "Unknown") for r in recipes if isinstance(r, dict) and "error" not in r]
            carbs_used = list(set(used_carbohydrates))
            inspirations_used = self.used_cooking_inspirations
            
            print(f"🎨 Generated {len(recipes)} diverse recipes:")
            print(f"   - Cuisines: {', '.join(list(set(cuisines_used))[:3])}..." if cuisines_used else 'Various')
            print(f"   - Carb variety: {', '.join(carbs_used[:3])}..." if carbs_used else "")
            
            if must_use_ingredients and hasattr(self, '_must_use_recipe'):
                print(f"   - Must-use ingredients incorporated into recipe #{self._must_use_recipe}")
        
        # Clear the must-use recipe designation for next generation
        if hasattr(self, '_must_use_recipe'):
            delattr(self, '_must_use_recipe')
        
        return recipes
    
    async def generate_recipes_with_images(
        self, 
        liked_foods: List[str], 
        disliked_foods: List[str], 
        recipe_count: int = 5, 
        serving_size: int = 4, 
        progress_callback=None, 
        user_id: int = None, 
        db_session=None, 
        must_use_ingredients: List[str] = None,
        generate_images: bool = True,
        comfyui_server: str = "192.168.4.208:8188"
    ) -> List[Dict[str, Any]]:
        """
        Generate recipes and optionally generate images for each recipe
        
        Args:
            generate_images: Whether to generate images for the recipes
            comfyui_server: ComfyUI server address
            ... (other args same as generate_recipes)
        """
        # First generate the recipes
        if progress_callback:
            await progress_callback("Generating recipes...")
        
        recipes = await self.generate_recipes(
            liked_foods, disliked_foods, recipe_count, serving_size, 
            progress_callback, user_id, db_session, must_use_ingredients
        )
        
        # Generate images if requested
        if generate_images and recipes:
            print(f"🔍 Starting image generation for {len(recipes)} recipes...")
            try:
                if progress_callback:
                    await progress_callback("Generating recipe images...")
                
                # Import here to avoid dependency issues if not needed
                print("🔍 Importing ComfyUI client...")
                from ..imagegen.comfyui_client import ComfyUIClient
                print("✅ ComfyUI client imported successfully")
                
                # Initialize ComfyUI client
                print(f"🔍 Initializing ComfyUI client for server: {comfyui_server}")
                comfyui_client = ComfyUIClient(comfyui_server)
                
                # Test server connectivity
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"http://{comfyui_server}/", timeout=aiohttp.ClientTimeout(total=5)) as response:
                            print(f"✅ ComfyUI server reachable: {response.status}")
                except Exception as e:
                    print(f"❌ ComfyUI server not reachable: {e}")
                    # Continue anyway - maybe it's just the root endpoint that's not available
                
                # Generate images for valid recipes
                valid_recipes = [(i, recipe) for i, recipe in enumerate(recipes) 
                               if isinstance(recipe, dict) and 'name' in recipe and 'error' not in recipe]
                
                if valid_recipes:
                    print(f"🖼️ Generating images for {len(valid_recipes)} recipes...")
                    
                    # Generate images one by one with progress updates
                    image_results = {}
                    for idx, (recipe_index, recipe) in enumerate(valid_recipes):
                        if progress_callback:
                            await progress_callback(f"Generating image {idx + 1}/{len(valid_recipes)}: {recipe['name']}")
                        
                        try:
                            image_path = await comfyui_client.generate_recipe_image(
                                recipe['name'],
                                output_dir="/Users/ben/Code/FoodPal/media",
                                filename_prefix=f"recipe_{recipe_index + 1}"
                            )
                            image_results[recipe_index] = image_path
                            
                            # Add image path to recipe data
                            if image_path:
                                # Store relative path for web serving
                                relative_path = image_path.replace("/Users/ben/Code/FoodPal/", "")
                                recipes[recipe_index]['image_path'] = relative_path
                                print(f"✅ Image generated for '{recipe['name']}': {relative_path}")
                            else:
                                print(f"❌ Failed to generate image for '{recipe['name']}'")
                                
                        except Exception as e:
                            print(f"❌ Error generating image for '{recipe['name']}': {str(e)}")
                            image_results[recipe_index] = None
                    
                    # Summary
                    successful_images = sum(1 for path in image_results.values() if path)
                    print(f"🎨 Image generation complete: {successful_images}/{len(valid_recipes)} successful")
                else:
                    print("ℹ️ No valid recipes found for image generation")
                    
            except ImportError:
                print("⚠️ ComfyUI client not available, skipping image generation")
            except Exception as e:
                print(f"⚠️ Image generation failed: {str(e)}")
                # Continue without images rather than failing entirely
        
        return recipes