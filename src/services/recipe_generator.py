import httpx
import json
import re
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
import logging

# Setup logging
logger = logging.getLogger(__name__)

class RecipeGenerationError(Exception):
    """Custom exception for recipe generation errors"""
    pass

class APITimeoutError(RecipeGenerationError):
    """Exception for API timeout errors"""
    pass

class APIConnectionError(RecipeGenerationError):
    """Exception for API connection errors"""
    pass

class CircuitBreaker:
    """Simple circuit breaker implementation for API resilience"""
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """Check if we can execute the request"""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if asyncio.get_event_loop().time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record successful execution"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        """Record failed execution"""
        self.failure_count += 1
        self.last_failure_time = asyncio.get_event_loop().time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

class RecipeGenerator:
    def __init__(self, lm_studio_url: str, model: str):
        self.lm_studio_url = lm_studio_url
        self.model = model
        self.reset_diversity_tracking()
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        
        # HTTP client configuration
        self.timeout_config = httpx.Timeout(
            connect=10.0,    # Connection timeout
            read=120.0,      # Read timeout for LLM responses
            write=10.0,      # Write timeout
            pool=5.0         # Pool timeout
        )
        
        self.retry_config = {
            'max_retries': 2,
            'backoff_factor': 2,
            'retry_status_codes': [500, 502, 503, 504]
        }
    
    def reset_diversity_tracking(self):
        """Reset diversity tracking for a new meal plan"""
        self.used_cooking_inspirations = []
    
    async def generate_single_recipe(self, recipe_number: int, liked_foods: List[str], disliked_foods: List[str], 
                                   existing_ingredients: List[str] = None, progress_callback=None, total_recipes: int = 5, serving_size: int = 4, used_carbs: List[str] = None, user_id: int = None, db_session=None, must_use_ingredients: List[str] = None) -> Dict[str, Any]:
        """Generate a single recipe with cuisine diversity and carb variety"""
        
        # Enhanced cuisine/style selection with more variety
        cuisines = [
            "Italian", "Asian", "Mexican", "Mediterranean", "Indian", "French", "Thai", "Middle Eastern",
            "Japanese", "Korean", "Vietnamese", "Greek", "Spanish", "Moroccan", "Chinese", "Brazilian", 
            "Peruvian", "Turkish", "Lebanese", "Ethiopian", "Cajun", "Caribbean", "German", "Russian"
        ]
        import random
        
        # Get previously used elements to avoid repetition
        used_inspirations = getattr(self, 'used_cooking_inspirations', []) if hasattr(self, 'used_cooking_inspirations') else []
        
        # Select diverse cuisine, avoiding recent ones
        available_cuisines = [c for c in cuisines if c not in used_inspirations[-4:]]
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
        
        # Enhanced variety with multiple randomization layers
        recipe_styles = [
            "hearty", "light and fresh", "comfort food", "restaurant-style", "family-friendly",
            "gourmet", "rustic", "modern fusion", "traditional", "street food style",
            "healthy and nutritious", "indulgent", "quick and easy", "impressive dinner party"
        ]
        
        cooking_methods = [
            "grilled", "roasted", "sautéed", "braised", "steamed", "stir-fried", 
            "pan-seared", "baked", "slow-cooked", "pressure-cooked", "marinated",
            "char-grilled", "oven-baked", "pan-roasted", "caramelized"
        ]
        
        flavor_profiles = [
            "aromatic and spiced", "citrusy and bright", "rich and savory", "smoky and bold",
            "sweet and tangy", "herbal and fresh", "umami-rich", "spicy and warming",
            "cooling and refreshing", "earthy and robust", "delicate and nuanced"
        ]
        
        meal_occasions = [
            "weeknight dinner", "weekend feast", "dinner party", "cozy family meal",
            "romantic dinner", "casual entertaining", "comfort food craving", "healthy weeknight",
            "special celebration", "game day meal", "seasonal celebration"
        ]
        
        style_hint = random.choice(recipe_styles)
        cooking_method = random.choice(cooking_methods)
        flavor_profile = random.choice(flavor_profiles)
        meal_occasion = random.choice(meal_occasions)
        
        # Create dynamic prompt elements for more variety
        seasonal_elements = {
            "spring": ["asparagus", "peas", "artichokes", "spring onions", "fresh herbs"],
            "summer": ["tomatoes", "zucchini", "bell peppers", "corn", "fresh basil"],
            "fall": ["squash", "mushrooms", "root vegetables", "apples", "sage"],
            "winter": ["cabbage", "potatoes", "hearty greens", "citrus", "warming spices"]
        }
        
        current_season = random.choice(list(seasonal_elements.keys()))
        seasonal_inspiration = random.choice(seasonal_elements[current_season])
        
        # Add creative constraints for variety
        creative_constraints = [
            "incorporate a surprising ingredient combination",
            "use an unexpected cooking technique",
            "add a creative garnish or finishing touch",
            "include a homemade sauce or marinade",
            "feature a unique texture contrast",
            "use a traditional technique in a modern way",
            "incorporate fermented flavors",
            "add a signature spice blend"
        ]
        
        constraint = random.choice(creative_constraints)
        
        # Enhanced prompt with multiple layers of randomization
        prompt = f"""You are a {flavor_profile} chef creating an authentic {selected_cuisine} dinner recipe perfect for a {meal_occasion}. This should be a {style_hint} dish that serves {serving_size} people.

CREATIVE DIRECTION:
- Primary cooking method: {cooking_method}
- Flavor profile: {flavor_profile}
- Style: {style_hint}
- Creative challenge: {constraint}
- Seasonal inspiration: Consider incorporating {seasonal_inspiration} if it fits the cuisine
- Make this recipe distinctive and memorable, not generic

REQUIREMENTS:
- {must_use_text}{carb_text}{preferences_text}
- Use realistic ingredient quantities and cooking times
- Provide clear, step-by-step instructions that build flavor layers
- Balance nutrition with taste and visual appeal
- IMPORTANT: Choose ONE primary protein (chicken/beef/fish/pork/lamb/tofu/legumes) - never mix expensive proteins
- Include cooking tips and visual cues for success

RESPONSE FORMAT: Return ONLY valid JSON with no additional text or explanations.

{{
    "name": "Creative and descriptive recipe name that captures the essence",
    "prep_time": "realistic prep time in minutes",
    "cook_time": "realistic cooking time in minutes", 
    "servings": {serving_size},
    "cuisine_inspiration": "{selected_cuisine}",
    "difficulty": "Easy/Medium/Hard",
    "cooking_method": "{cooking_method}",
    "flavor_profile": "{flavor_profile}",
    "ingredients": [
        {{"item": "specific ingredient with quality notes", "quantity": "precise amount", "unit": "g/ml/tbsp/tsp/cup/piece"}},
        {{"item": "primary protein (be specific - e.g., 'chicken thighs, bone-in')", "quantity": "400-600", "unit": "g"}},
        {{"item": "fresh vegetables (name specific varieties)", "quantity": "200-400", "unit": "g"}},
        {{"item": "carbohydrate base (be specific about type/variety)", "quantity": "200-300", "unit": "g"}},
        {{"item": "aromatics (onions, garlic, ginger, etc.)", "quantity": "50-100", "unit": "g"}},
        {{"item": "signature spices/seasonings (be authentic to cuisine)", "quantity": "1-2", "unit": "tsp"}},
        {{"item": "cooking fat (olive oil, butter, coconut oil, etc.)", "quantity": "15-30", "unit": "ml"}},
        {{"item": "finishing elements (herbs, acid, garnish)", "quantity": "as needed", "unit": "to taste"}}
    ],
    "instructions": [
        "Step 1: Preparation and mise en place with timing notes",
        "Step 2: Building the flavor base - aromatics and spices",
        "Step 3: {cooking_method} the protein with technique details",
        "Step 4: Vegetable preparation and cooking method",
        "Step 5: Combining elements and final seasoning adjustments",
        "Step 6: Plating, garnishing, and serving suggestions"
    ],
    "chef_tips": [
        "Key technique tip for success",
        "Flavor balancing advice",
        "Visual cue for doneness"
    ]
}}

Create an inspiring {selected_cuisine} recipe that embodies {flavor_profile} flavors using the {cooking_method} technique:"""
        
        try:
            if progress_callback:
                progress_callback(f"Generating recipe {recipe_number}/{total_recipes}...")
            
            # Check circuit breaker
            if not self.circuit_breaker.can_execute():
                logger.warning(f"Circuit breaker open, using fallback for recipe {recipe_number}")
                return self._create_enhanced_fallback_recipe(recipe_number, selected_cuisine, serving_size, must_use_ingredients)
            
            recipe = await self._make_api_request_with_retry(prompt, recipe_number, serving_size, selected_cuisine, must_use_ingredients)
            
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
        
        except Exception as e:
            # Use the enhanced fallback method for any other errors
            logger.error(f"Unexpected error in recipe generation: {e}")
            return self._create_enhanced_fallback_recipe(recipe_number, selected_cuisine, serving_size, must_use_ingredients)

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
    
    async def _make_api_request_with_retry(self, prompt: str, recipe_number: int, serving_size: int, cuisine: str, must_use_ingredients: Optional[List[str]] = None) -> Dict[str, Any]:
        """Make API request with retry logic and proper error handling"""
        last_exception = None
        
        for attempt in range(self.retry_config['max_retries'] + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_config) as client:
                    response = await client.post(
                        f"{self.lm_studio_url}/v1/chat/completions",
                        headers={"Content-Type": "application/json"},
                        json={
                            "model": self.model,
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.7,
                            "max_tokens": 1000
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        from ..utils.recipe_parser import parse_recipe_response
                        content = result['choices'][0]['message']['content']
                        recipe = parse_recipe_response(content, recipe_number, serving_size)
                        
                        if "error" not in recipe:
                            return recipe
                        else:
                            logger.warning(f"Recipe parsing failed for recipe {recipe_number}: {recipe.get('error')}")
                            last_exception = RecipeGenerationError(f"Recipe parsing failed: {recipe.get('error')}")
                    
                    elif response.status_code in self.retry_config['retry_status_codes']:
                        last_exception = APIConnectionError(f"API returned {response.status_code}: {response.text}")
                        if attempt < self.retry_config['max_retries']:
                            await asyncio.sleep(self.retry_config['backoff_factor'] ** attempt)
                            continue
                    else:
                        last_exception = APIConnectionError(f"API error {response.status_code}: {response.text}")
                        break
            
            except httpx.TimeoutException as e:
                last_exception = APITimeoutError(f"Request timeout for recipe {recipe_number}: {str(e)}")
                if attempt < self.retry_config['max_retries']:
                    await asyncio.sleep(self.retry_config['backoff_factor'] ** attempt)
                    continue
                break
                
            except httpx.ConnectError as e:
                last_exception = APIConnectionError(f"Connection failed for recipe {recipe_number}: {str(e)}")
                if attempt < self.retry_config['max_retries']:
                    await asyncio.sleep(self.retry_config['backoff_factor'] ** attempt)
                    continue
                break
                
            except Exception as e:
                last_exception = RecipeGenerationError(f"Unexpected error for recipe {recipe_number}: {str(e)}")
                break
        
        # All retries failed, record failure and return fallback
        self.circuit_breaker.record_failure()
        logger.error(f"API request failed after all retries: {last_exception}")
        return self._create_enhanced_fallback_recipe(recipe_number, cuisine, serving_size, must_use_ingredients)
    
    def _create_enhanced_fallback_recipe(self, recipe_number: int, cuisine: str, serving_size: int, must_use_ingredients: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create an enhanced fallback recipe with much better variety"""
        import random
        
        # Expanded protein options by cuisine
        proteins_by_cuisine = {
            "Italian": ["pancetta", "prosciutto", "chicken thighs", "white fish", "mozzarella"],
            "Asian": ["pork belly", "chicken thighs", "tofu", "shrimp", "beef strips"],
            "Mexican": ["ground turkey", "chicken breast", "black beans", "chorizo", "fish fillets"],
            "Mediterranean": ["lamb", "chicken", "white beans", "feta cheese", "sardines"],
            "Indian": ["chicken thighs", "lamb", "paneer", "lentils", "chickpeas"],
            "Thai": ["chicken thighs", "shrimp", "tofu", "pork shoulder", "fish sauce"],
            "Middle Eastern": ["lamb", "chicken", "chickpeas", "ground beef", "halloumi"]
        }
        
        # Varied vegetables by season and cuisine compatibility
        vegetables_by_style = {
            "fresh": ["bell peppers", "zucchini", "cherry tomatoes", "snap peas", "cucumber"],
            "hearty": ["eggplant", "mushrooms", "carrots", "broccoli", "cauliflower"],
            "leafy": ["spinach", "kale", "chard", "arugula", "bok choy"],
            "root": ["sweet potatoes", "parsnips", "turnips", "beets", "radishes"]
        }
        
        # Diverse carbohydrate options
        carbs_by_cuisine = {
            "Italian": ["pasta", "risotto rice", "polenta", "gnocchi"],
            "Asian": ["jasmine rice", "noodles", "brown rice", "rice vermicelli"],
            "Mexican": ["black beans", "quinoa", "corn tortillas", "rice"],
            "Mediterranean": ["couscous", "bulgur", "orzo", "pita bread"],
            "Indian": ["basmati rice", "naan bread", "lentils", "chickpeas"],
            "Thai": ["jasmine rice", "rice noodles", "coconut rice"],
            "Middle Eastern": ["bulgur", "pita", "rice pilaf", "couscous"]
        }
        
        # Select with cuisine awareness
        cuisine_proteins = proteins_by_cuisine.get(cuisine, ["chicken breast", "ground beef", "tofu", "salmon"])
        selected_protein = random.choice(cuisine_proteins)
        
        veg_style = random.choice(list(vegetables_by_style.keys()))
        selected_vegetables = random.sample(vegetables_by_style[veg_style], min(2, len(vegetables_by_style[veg_style])))
        
        cuisine_carbs = carbs_by_cuisine.get(cuisine, ["rice", "pasta", "quinoa", "potatoes"])
        selected_carb = random.choice(cuisine_carbs)
        
        # Random cooking methods and flavors for variety
        cooking_methods = ["sautéed", "roasted", "braised", "grilled", "steamed"]
        flavor_enhancers = ["garlic and herbs", "ginger and spices", "citrus and herbs", "wine reduction", "coconut and spices"]
        
        method = random.choice(cooking_methods)
        enhancer = random.choice(flavor_enhancers)
        
        # Create base ingredients
        ingredients = []
        
        # Add must-use ingredients first if applicable
        if must_use_ingredients and hasattr(self, '_must_use_recipe') and recipe_number == self._must_use_recipe:
            for ing in must_use_ingredients:
                ingredients.append({"item": ing, "quantity": "200", "unit": "g"})
        
        # Add standard recipe components
        ingredients.extend([
            {"item": selected_protein, "quantity": "500", "unit": "g"},
            {"item": f"{selected_vegetables[0]} and {selected_vegetables[1]}", "quantity": "400", "unit": "g"},
            {"item": selected_carb, "quantity": "250", "unit": "g"},
            {"item": "olive oil", "quantity": "30", "unit": "ml"},
            {"item": "garlic", "quantity": "3", "unit": "cloves"},
            {"item": "onion", "quantity": "1", "unit": "medium"},
            {"item": "salt and black pepper", "quantity": "to taste", "unit": ""},
        ])
        
        # Cuisine-specific additions
        if cuisine.lower() == "italian":
            ingredients.extend([
                {"item": "basil leaves", "quantity": "15", "unit": "g"},
                {"item": "parmesan cheese", "quantity": "50", "unit": "g"}
            ])
        elif cuisine.lower() == "asian":
            ingredients.extend([
                {"item": "soy sauce", "quantity": "30", "unit": "ml"},
                {"item": "ginger", "quantity": "10", "unit": "g"}
            ])
        elif cuisine.lower() == "mexican":
            ingredients.extend([
                {"item": "cumin", "quantity": "2", "unit": "tsp"},
                {"item": "lime", "quantity": "1", "unit": "whole"}
            ])
        
        # Create more varied recipe names
        recipe_names = [
            f"{method.title()} {selected_protein.title()} with {enhancer.title()}",
            f"{cuisine} {selected_protein.title()} and {selected_vegetables[0].title()}",
            f"{selected_protein.title()} {cuisine} Style with {selected_carb.title()}",
            f"{enhancer.title()} {selected_protein.title()} - {cuisine} Inspired"
        ]
        
        recipe_name = random.choice(recipe_names)
        if must_use_ingredients and hasattr(self, '_must_use_recipe') and recipe_number == self._must_use_recipe:
            recipe_name = f"{cuisine} {selected_protein.title()} with {', '.join(must_use_ingredients)}"
        
        return {
            "name": recipe_name,
            "prep_time": "15 minutes",
            "cook_time": f"{random.randint(20, 35)} minutes",
            "servings": serving_size,
            "cuisine_inspiration": cuisine,
            "difficulty": "Easy",
            "ingredients": ingredients,
            "instructions": [
                "Heat olive oil in a large skillet over medium-high heat",
                "Sauté minced garlic and diced onion until fragrant, about 2 minutes",
                f"Add {selected_protein} and cook until golden brown and cooked through",
                f"Add {selected_vegetables[0]} and {selected_vegetables[1]}, cook until tender",
                f"Meanwhile, prepare {selected_carb} according to package instructions",
                "Season with salt, pepper, and any additional spices to taste",
                f"Serve the {selected_protein} and vegetables over {selected_carb}",
                "Garnish as desired and serve hot"
            ],
            "_note": f"High-quality fallback recipe (API unavailable) - Recipe #{recipe_number}",
            "_fallback": True
        }
    
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
            progress_callback("Generating recipes...")
        
        recipes = await self.generate_recipes(
            liked_foods, disliked_foods, recipe_count, serving_size, 
            progress_callback, user_id, db_session, must_use_ingredients
        )
        
        # Generate images if requested
        if generate_images and recipes:
            print(f"🔍 Starting image generation for {len(recipes)} recipes...")
            try:
                if progress_callback:
                    progress_callback("Generating recipe images...")
                
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
                            progress_callback(f"Generating image {idx + 1}/{len(valid_recipes)}: {recipe['name']}")
                        
                        try:
                            image_path = await comfyui_client.generate_recipe_image(
                                recipe['name'],
                                output_dir="./media",  # Use relative path
                                filename_prefix=f"recipe_{recipe_index + 1}"
                            )
                            image_results[recipe_index] = image_path
                            
                            # Add image path to recipe data
                            if image_path:
                                # Extract just the filename for web serving
                                import os
                                filename = os.path.basename(image_path)
                                web_path = f"media/{filename}"
                                recipes[recipe_index]['image_path'] = web_path
                                print(f"✅ Image generated for '{recipe['name']}': {web_path}")
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