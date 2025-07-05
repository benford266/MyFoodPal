from typing import List, Dict, Any

def generate_shopping_list(recipes: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Generate a consolidated shopping list from multiple recipes"""
    ingredient_totals = {}
    
    for recipe in recipes:
        if "ingredients" in recipe and isinstance(recipe["ingredients"], list):
            for ingredient in recipe["ingredients"]:
                if isinstance(ingredient, dict) and "item" in ingredient:
                    item_name = ingredient["item"].lower().strip()
                    quantity = ingredient.get("quantity", "")
                    unit = ingredient.get("unit", "")
                    
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
                            "item": ingredient["item"],
                            "quantity": quantity,
                            "unit": unit
                        }
    
    return list(ingredient_totals.values())