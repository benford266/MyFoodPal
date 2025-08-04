"""
Recipe Response Parsing Utilities
"""
import json
import re
from typing import Dict, Any


def clean_json_response(response_text: str) -> str:
    """
    Clean and extract JSON from LLM response
    
    Args:
        response_text: Raw response from LLM
        
    Returns:
        Cleaned JSON string
    """
    # Remove common prefixes/suffixes
    response_text = response_text.strip()
    
    # Remove markdown code blocks
    response_text = re.sub(r'^```json\s*', '', response_text, flags=re.MULTILINE)
    response_text = re.sub(r'^```\s*$', '', response_text, flags=re.MULTILINE)
    
    # Remove any text before the first {
    start_idx = response_text.find('{')
    if start_idx != -1:
        response_text = response_text[start_idx:]
    
    # Remove any text after the last }
    end_idx = response_text.rfind('}')
    if end_idx != -1:
        response_text = response_text[:end_idx + 1]
    
    # Fix common JSON issues
    response_text = response_text.replace("\\'", "'")  # Fix escaped quotes
    response_text = re.sub(r',\s*}', '}', response_text)  # Remove trailing commas
    response_text = re.sub(r',\s*]', ']', response_text)  # Remove trailing commas in arrays
    
    return response_text


def parse_recipe_response(response_text: str, recipe_number: int, serving_size: int = 4) -> Dict[str, Any]:
    """
    Parse recipe response with multiple fallback methods
    
    Args:
        response_text: Raw response from LLM
        recipe_number: Recipe number for fallback naming
        serving_size: Number of servings
        
    Returns:
        Parsed recipe dictionary
    """
    
    # Method 1: Direct JSON parsing
    try:
        result = json.loads(response_text)
        # If it's a list, take the first item
        if isinstance(result, list) and len(result) > 0:
            return result[0]
        return result
    except json.JSONDecodeError:
        pass
    
    # Method 2: Clean and try again
    try:
        cleaned = clean_json_response(response_text)
        result = json.loads(cleaned)
        # If it's a list, take the first item
        if isinstance(result, list) and len(result) > 0:
            return result[0]
        return result
    except json.JSONDecodeError:
        pass
    
    # Method 3: Extract key information manually
    try:
        # Extract name
        name_match = re.search(r'"name"\s*:\s*"([^"]+)"', response_text)
        name = name_match.group(1) if name_match else f"Recipe {recipe_number}"
        
        # Extract times
        prep_match = re.search(r'"prep_time"\s*:\s*"([^"]+)"', response_text)
        prep_time = prep_match.group(1) if prep_match else "20 minutes"
        
        cook_match = re.search(r'"cook_time"\s*:\s*"([^"]+)"', response_text)
        cook_time = cook_match.group(1) if cook_match else "30 minutes"
        
        # Extract cuisine
        cuisine_match = re.search(r'"cuisine_inspiration"\s*:\s*"([^"]+)"', response_text)
        cuisine = cuisine_match.group(1) if cuisine_match else "International"
        
        # Extract difficulty
        difficulty_match = re.search(r'"difficulty"\s*:\s*"([^"]+)"', response_text)
        difficulty = difficulty_match.group(1) if difficulty_match else "Medium"
        
        # Create fallback recipe
        return {
            "name": name,
            "prep_time": prep_time,
            "cook_time": cook_time,
            "servings": serving_size,
            "cuisine_inspiration": cuisine,
            "difficulty": difficulty,
            "ingredients": [
                {"item": "main ingredient", "quantity": "500", "unit": "g"},
                {"item": "vegetables", "quantity": "200", "unit": "g"},
                {"item": "seasoning", "quantity": "5", "unit": "ml"}
            ],
            "instructions": [
                "Prepare ingredients",
                "Cook main ingredient",
                "Add vegetables and seasonings",
                "Serve hot"
            ],
            "_note": "Fallback recipe - original response had parsing issues"
        }
    except Exception:
        pass
    
    # Method 4: Return error with raw response
    return {
        "error": f"Failed to parse recipe {recipe_number}",
        "raw_response": response_text[:500] + "..." if len(response_text) > 500 else response_text
    }