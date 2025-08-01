import httpx
import json
import re
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
        """Generate a single recipe, optionally using existing ingredients"""
        
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
            carb_text = f"Use different carb than: {', '.join(used_carbs[:2])}. "
        
        # Simplified prompt - much shorter
        prompt = f"""Create a {selected_cuisine} dinner recipe for {serving_size} people. {must_use_text}{carb_text}{preferences_text}

JSON format:
{{
    "name": "Creative Recipe Name",
    "prep_time": "15 minutes",
    "cook_time": "30 minutes", 
    "servings": {serving_size},
    "cuisine_inspiration": "{selected_cuisine}",
    "difficulty": "Medium",
    "ingredients": [
        {{"item": "protein", "quantity": "600", "unit": "g"}},
        {{"item": "vegetable", "quantity": "400", "unit": "g"}},
        {{"item": "carb", "quantity": "300", "unit": "g"}},
        {{"item": "seasonings", "quantity": "2", "unit": "tbsp"}},
        {{"item": "oil", "quantity": "30", "unit": "ml"}}
    ],
    "instructions": [
        "Prep ingredients",
        "Cook protein",
        "Cook vegetables", 
        "Combine and season",
        "Serve"
    ]
}}"""
        
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
            
            return {
                "name": fallback_name,
                "prep_time": "15 minutes",
                "cook_time": "25 minutes",
                "servings": serving_size,
                "cuisine_inspiration": "Simple",
                "difficulty": "Easy",
                "ingredients": [
                    {"item": ing, "quantity": "200", "unit": "g"} for ing in (must_use_ingredients if must_use_ingredients and hasattr(self, '_must_use_recipe') and recipe_number == self._must_use_recipe else [])
                ] + [
                    {"item": "main protein", "quantity": "400", "unit": "g"},
                    {"item": "vegetables", "quantity": "300", "unit": "g"},
                    {"item": "seasonings", "quantity": "5", "unit": "ml"}
                ],
                "instructions": [
                    "Heat oil in a large pan",
                    "Add main protein and cook until done",
                    "Add vegetables and seasonings",
                    "Cook until vegetables are tender",
                    "Serve hot"
                ],
                "_note": f"Fallback recipe due to generation timeout: {str(e)}"
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
            # After first recipe, pass existing ingredients to encourage sharing
            existing_ingredients = all_ingredients if i > 1 else None
            
            # Pass used carbohydrates to encourage variety (from second recipe onwards)
            used_carbs = used_carbohydrates if i > 1 else None
            
            recipe = await self.generate_single_recipe(
                i, liked_foods, disliked_foods, existing_ingredients, progress_callback, recipe_count, serving_size, used_carbs, user_id, db_session, must_use_ingredients
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