import httpx
import json
import re
from typing import List, Dict, Any

class RecipeGenerator:
    def __init__(self, ollama_url: str, model: str):
        self.ollama_url = ollama_url
        self.model = model
        self.reset_diversity_tracking()
    
    def reset_diversity_tracking(self):
        """Reset diversity tracking for a new meal plan"""
        self.used_cooking_methods = []
        self.used_spice_profiles = []
        self.used_sauce_bases = []
        self.used_cooking_inspirations = []
    
    async def generate_single_recipe(self, recipe_number: int, liked_foods: List[str], disliked_foods: List[str], 
                                   existing_ingredients: List[str] = None, progress_callback=None, total_recipes: int = 5, serving_size: int = 4, used_carbs: List[str] = None, user_id: int = None, db_session=None, must_use_ingredients: List[str] = None) -> Dict[str, Any]:
        """Generate a single recipe, optionally using existing ingredients"""
        
        existing_ingredients_text = ""
        if existing_ingredients:
            existing_ingredients_text = f"""
        SHARED INGREDIENTS TO USE (if possible): {', '.join(existing_ingredients)}
        Try to incorporate some of these ingredients to minimize shopping."""
        
        # Add must-use ingredients section - only for the designated recipe
        must_use_text = ""
        if must_use_ingredients and hasattr(self, '_must_use_recipe') and recipe_number == self._must_use_recipe:
            must_use_text = f"""
- MUST USE THESE INGREDIENTS: {', '.join(must_use_ingredients)}
- REQUIREMENT: Include ALL of these ingredients in the recipe
- Build the recipe around these specific ingredients"""
        
        carb_variety_text = ""
        if used_carbs:
            carb_variety_text = f"""
        CARBOHYDRATE VARIETY REQUIREMENT:
        These carbohydrates have already been used in other recipes: {', '.join(used_carbs)}
        Please choose a DIFFERENT carbohydrate base for this recipe to add variety.
        Carbohydrate options include: rice, pasta, potatoes, quinoa, bulgur, couscous, polenta, bread, noodles, barley, sweet potatoes, lentils, chickpeas, beans, or other grains/starches."""
        
        # Add creativity elements with radical diversity
        cooking_methods = [
            "slow-braised in aromatic liquids",
            "high-heat seared and roasted",
            "marinated and grilled with char marks",
            "poached gently in flavored broths",
            "smoked low and slow",
            "pan-fried with crispy coating",
            "steamed with aromatic herbs",
            "confit in flavored oils",
            "blackened with spice crusts",
            "sous-vide with precise temperature control"
        ]
        
        spice_profiles = [
            "Mediterranean herbs (oregano, thyme, rosemary, basil)",
            "Middle Eastern spices (sumac, za'atar, baharat, harissa)",
            "Asian five-spice and aromatics (star anise, ginger, garlic, soy)",
            "Indian curry spices (turmeric, cumin, coriander, garam masala)",
            "Mexican heat and smokiness (chipotle, ancho, cumin, lime)",
            "North African warmth (ras el hanout, preserved lemon, olives)",
            "French herbes de Provence and wine reductions",
            "Caribbean jerk spices (allspice, scotch bonnet, thyme)",
            "Scandinavian dill and juniper with citrus",
            "Peruvian aji peppers and tropical fruits"
        ]
        
        sauce_bases = [
            "tomato-based sauces with herbs",
            "cream or coconut milk reductions",
            "citrus and herb marinades",
            "fermented bean pastes and umami",
            "wine and stock reductions",
            "nut-based sauces and pestos",
            "vinegar-based pickled accompaniments",
            "fruit-based chutneys and salsas",
            "yogurt and herb cooling sauces",
            "oil-based infusions and drizzles"
        ]
        
        cooking_inspirations = [
            "Japanese precision and umami depth",
            "Italian rustic simplicity and quality ingredients",
            "Indian spice layering and aromatics",
            "Mexican bold flavors and heat",
            "French classical techniques and elegance",
            "Thai balance of sweet, sour, salty, spicy",
            "Middle Eastern hospitality and exotic spices",
            "Korean fermentation and bold flavors",
            "Peruvian fresh ingredients and aji peppers",
            "Moroccan tagine cooking and warm spices"
        ]
        
        import random
        
        # Get previously used elements to avoid repetition
        used_methods = getattr(self, 'used_cooking_methods', []) if hasattr(self, 'used_cooking_methods') else []
        used_spices = getattr(self, 'used_spice_profiles', []) if hasattr(self, 'used_spice_profiles') else []
        used_sauces = getattr(self, 'used_sauce_bases', []) if hasattr(self, 'used_sauce_bases') else []
        used_inspirations = getattr(self, 'used_cooking_inspirations', []) if hasattr(self, 'used_cooking_inspirations') else []
        
        # Select diverse elements, avoiding recent ones
        available_methods = [m for m in cooking_methods if m not in used_methods[-3:]]
        available_spices = [s for s in spice_profiles if s not in used_spices[-3:]]
        available_sauces = [s for s in sauce_bases if s not in used_sauces[-3:]]
        available_inspirations = [i for i in cooking_inspirations if i not in used_inspirations[-3:]]
        
        # Fall back to full list if we've used too many
        if not available_methods: available_methods = cooking_methods
        if not available_spices: available_spices = spice_profiles
        if not available_sauces: available_sauces = sauce_bases
        if not available_inspirations: available_inspirations = cooking_inspirations
        
        selected_method = random.choice(available_methods)
        selected_spices = random.choice(available_spices)
        selected_sauce = random.choice(available_sauces)
        selected_inspiration = random.choice(available_inspirations)
        
        # Track used elements
        if not hasattr(self, 'used_cooking_methods'): self.used_cooking_methods = []
        if not hasattr(self, 'used_spice_profiles'): self.used_spice_profiles = []
        if not hasattr(self, 'used_sauce_bases'): self.used_sauce_bases = []
        if not hasattr(self, 'used_cooking_inspirations'): self.used_cooking_inspirations = []
        
        self.used_cooking_methods.append(selected_method)
        self.used_spice_profiles.append(selected_spices)
        self.used_sauce_bases.append(selected_sauce)
        self.used_cooking_inspirations.append(selected_inspiration)
        
        # Add user history context if available
        history_context = ""
        if user_id and db_session:
            try:
                from ..database.operations import get_user_recipe_history
                recent_history = get_user_recipe_history(db_session, user_id, 10)
                if recent_history:
                    recent_names = [h.recipe_name for h in recent_history[:5]]
                    recent_methods = [h.cooking_method.split()[0] for h in recent_history[:5]]
                    recent_spices = [h.spice_profile.split()[0] for h in recent_history[:5]]
                    
                    history_context = f"""
        ⚠️ AVOID REPEATING RECENT USER HISTORY:
        Recent recipe names: {', '.join(recent_names)}
        Recent cooking methods: {', '.join(set(recent_methods))}
        Recent spice profiles: {', '.join(set(recent_spices))}
        
        CRITICAL: This recipe must be completely different from these recent recipes.
        Use different name patterns, cooking techniques, and spice combinations."""
            except Exception as e:
                print(f"Warning: Could not load user history: {e}")
        
        # Simplified prompt for smaller models
        ingredients_requirement = ""
        ingredients_example = '"item": "ingredient", "quantity": "500", "unit": "g"'
        
        if must_use_ingredients and hasattr(self, '_must_use_recipe') and recipe_number == self._must_use_recipe:
            ingredients_requirement = f"IMPORTANT: This recipe MUST include these ingredients: {', '.join(must_use_ingredients)}"
            # Create explicit examples with must-use ingredients
            must_use_examples = []
            for ingredient in must_use_ingredients:
                must_use_examples.append(f'{{"item": "{ingredient}", "quantity": "200", "unit": "g"}}')
            ingredients_example = ',\n        '.join(must_use_examples + ['"item": "other ingredient", "quantity": "300", "unit": "g"'])
        
        prompt = f"""Create a dinner recipe in JSON format.

{ingredients_requirement}

User preferences:
- LIKES: {', '.join(liked_foods)}
- DISLIKES: {', '.join(disliked_foods)}
- SERVES: {serving_size} people
{existing_ingredients_text}

Requirements:
- Cooking style: {selected_method}
- Flavor profile: {selected_spices}
- Use metric units (grams, ml)
- Include prep and cook times

Return valid JSON only:
{{
    "name": "Recipe Name",
    "prep_time": "15 minutes",
    "cook_time": "30 minutes",
    "servings": {serving_size},
    "cuisine_inspiration": "{selected_inspiration}",
    "difficulty": "Easy",
    "ingredients": [
        {ingredients_example}
    ],
    "instructions": [
        "Step 1: Prepare ingredients",
        "Step 2: Cook main components",
        "Step 3: Combine and serve"
    ]
}}"""
        
        try:
            if progress_callback:
                await progress_callback(f"Generating recipe {recipe_number}/{total_recipes}...")
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=60.0  # Reduced timeout to prevent hanging
                )
                
                if response.status_code == 200:
                    result = response.json()
                    from ..utils.recipe_parser import parse_recipe_response
                    recipe = parse_recipe_response(result['response'], recipe_number, serving_size)
                    
                    # Check for similarity with user history if available
                    if user_id and db_session and "error" not in recipe:
                        try:
                            from ..database.operations import check_recipe_similarity, save_recipe_to_history
                            
                            # Check if too similar to recent recipes
                            is_similar = check_recipe_similarity(
                                db_session, user_id, recipe, 
                                selected_method, selected_spices, selected_sauce, selected_inspiration
                            )
                            
                            if is_similar:
                                print(f"🔄 Recipe {recipe_number} too similar to recent history, will need regeneration")
                                # Could implement retry logic here if needed
                                recipe["_warning"] = "Similar to recent recipes"
                            else:
                                # Save to history for future reference
                                save_recipe_to_history(
                                    db_session, user_id, recipe,
                                    selected_method, selected_spices, selected_sauce, selected_inspiration
                                )
                                print(f"✅ Recipe {recipe_number} saved to user history")
                                
                        except Exception as e:
                            print(f"Warning: History check failed for recipe {recipe_number}: {e}")
                    
                    return recipe
                else:
                    return {"error": f"Ollama API error for recipe {recipe_number}: {response.status_code}"}
        
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
            methods_used = self.used_cooking_methods
            spices_used = self.used_spice_profiles
            
            print(f"🎨 Generated {len(recipes)} radically diverse recipes:")
            print(f"   - Cuisines: {', '.join(list(set(cuisines_used))[:3])}..." if cuisines_used else 'Various')
            print(f"   - Cooking methods: {', '.join([m.split()[0] for m in methods_used[:3]])}..." if methods_used else "")
            print(f"   - Spice profiles: {', '.join([s.split()[0] for s in spices_used[:3]])}..." if spices_used else "")
            print(f"   - Carb variety: {', '.join(carbs_used[:3])}..." if carbs_used else "")
            
            if must_use_ingredients and hasattr(self, '_must_use_recipe'):
                print(f"   - Must-use ingredients incorporated into recipe #{self._must_use_recipe}")
        
        # Clear the must-use recipe designation for next generation
        if hasattr(self, '_must_use_recipe'):
            delattr(self, '_must_use_recipe')
        
        return recipes