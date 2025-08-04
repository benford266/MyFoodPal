"""
Shopping List Generation Utilities
"""
from typing import List, Dict, Any


def generate_shopping_list(recipes: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Generate a consolidated shopping list from multiple recipes
    
    Args:
        recipes: List of recipe dictionaries with ingredients
        
    Returns:
        List of consolidated shopping list items
    """
    ingredient_totals = {}
    recipe_usage = {}  # Track which recipes use each ingredient
    
    for recipe_idx, recipe in enumerate(recipes):
        recipe_name = recipe.get("name", f"Recipe {recipe_idx + 1}")
        
        if "ingredients" in recipe and isinstance(recipe["ingredients"], list):
            for ingredient in recipe["ingredients"]:
                if isinstance(ingredient, dict) and "item" in ingredient:
                    item_name = ingredient["item"].lower().strip()
                    quantity = ingredient.get("quantity", "")
                    unit = ingredient.get("unit", "")
                    
                    # Track recipe usage
                    if item_name not in recipe_usage:
                        recipe_usage[item_name] = []
                    recipe_usage[item_name].append(recipe_name)
                    
                    # Simple aggregation by item name
                    if item_name in ingredient_totals:
                        # For now, just append quantities (could be enhanced with unit conversion)
                        existing = ingredient_totals[item_name]
                        if existing["unit"] == unit:
                            try:
                                existing_qty = float(existing["quantity"])
                                new_qty = float(quantity)
                                ingredient_totals[item_name]["quantity"] = str(existing_qty + new_qty)
                            except (ValueError, TypeError):
                                ingredient_totals[item_name]["quantity"] = f"{existing['quantity']}, {quantity}"
                        else:
                            ingredient_totals[item_name]["quantity"] = f"{existing['quantity']} {existing['unit']}, {quantity} {unit}"
                            ingredient_totals[item_name]["unit"] = ""
                    else:
                        ingredient_totals[item_name] = {
                            "ingredient": ingredient["item"],  # Use original case
                            "quantity": quantity,
                            "unit": unit
                        }
    
    # Add recipe usage information to shopping list
    shopping_list = []
    for item_key, item_data in ingredient_totals.items():
        item_data["used_in_recipes"] = recipe_usage.get(item_key, [])
        shopping_list.append(item_data)
    
    # Sort by ingredient name for better organization
    shopping_list.sort(key=lambda x: x["ingredient"].lower())
    
    return shopping_list