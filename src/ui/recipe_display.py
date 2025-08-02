from nicegui import ui
import json
from datetime import datetime
from typing import List, Dict, Any

from ..database.connection import get_db
from ..database.operations import create_or_update_recipe_rating
from ..utils.pdf_export import generate_pdf_export

def display_recipes_and_shopping_list(container, recipes: List[Dict[str, Any]], shopping_list: List[Dict[str, str]], theme: Dict[str, str], current_user: Dict, saved_meal_plan_id: int = None):
    """Display recipes and shopping list in the main page"""
    container.clear()
    
    with container:
        # Display recipes
        if recipes:
            ui.html(f'<h2 class="text-2xl font-bold {theme["text_primary"]} mb-6">🍽️ Your Personalized Recipes</h2>')
            
            with ui.column().classes('gap-6'):
                for i, recipe in enumerate(recipes, 1):
                    # Handle error recipes
                    if not isinstance(recipe, dict):
                        with ui.card().classes(f'{theme["error_bg"]} {theme["border"]} rounded-3xl p-6 text-center'):
                            ui.html('<div class="text-4xl mb-4">❌</div>')
                            ui.html(f'<h3 class="text-xl font-bold {theme["text_primary"]} mb-4">Recipe {i} Generation Failed</h3>')
                            ui.html(f'<p class="text-sm {theme["text_secondary"]}">Unexpected response format</p>')
                        continue
                    
                    if "error" in recipe:
                        with ui.card().classes(f'{theme["error_bg"]} {theme["border"]} rounded-3xl p-6 text-center'):
                            ui.html('<div class="text-4xl mb-4">❌</div>')
                            ui.html(f'<h3 class="text-xl font-bold {theme["text_primary"]} mb-4">Recipe {i} Generation Failed</h3>')
                            ui.html(f'<p class="text-sm {theme["text_secondary"]}">{recipe.get("error", "Unknown error")}</p>')
                        continue
                    
                    with ui.card().classes(f'recipe-card {theme["card"]} {theme["border"]} rounded-3xl p-6 sm:p-8 w-full'):
                            # Recipe header with enhanced info and image
                            with ui.column().classes('mb-6'):
                                # Recipe image (if available)
                                if recipe.get("image_path"):
                                    with ui.row().classes('justify-center mb-4'):
                                        try:
                                            ui.image(f'/{recipe["image_path"]}').classes('w-full max-w-md h-64 object-cover rounded-2xl shadow-lg')
                                        except Exception as e:
                                            print(f"Error displaying image for {recipe.get('name')}: {e}")
                                            # Show placeholder if image fails to load
                                            with ui.card().classes('w-full max-w-md h-64 bg-gray-100 rounded-2xl flex items-center justify-center'):
                                                ui.html('<div class="text-6xl opacity-50">🍽️</div>')
                                
                                with ui.row().classes('items-center gap-4 mb-3'):
                                    ui.html(f'<div class="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-emerald-400 to-teal-500 text-white rounded-full flex items-center justify-center text-xl font-bold">{i}</div>')
                                    with ui.column().classes('flex-1'):
                                        ui.html(f'<h3 class="text-2xl font-bold {theme["text_primary"]}">{recipe.get("name", "Untitled Recipe")}</h3>')
                                        if recipe.get("description"):
                                            ui.html(f'<p class="text-sm {theme["text_secondary"]} italic">{recipe.get("description")}</p>')
                                
                                # Creative elements row
                                with ui.row().classes('gap-4 flex-wrap'):
                                    if recipe.get("cuisine_inspiration"):
                                        ui.html(f'<span class="{theme["chip_bg"]} {theme["border"]} rounded-full px-3 py-1 text-xs">🌍 {recipe.get("cuisine_inspiration")}</span>')
                                    if recipe.get("difficulty"):
                                        difficulty_emoji = {"Easy": "👶", "Medium": "👨‍🍳", "Advanced": "🧑‍🍳"}
                                        ui.html(f'<span class="{theme["chip_bg"]} {theme["border"]} rounded-full px-3 py-1 text-xs">{difficulty_emoji.get(recipe.get("difficulty"), "👨‍🍳")} {recipe.get("difficulty")}</span>')
                                    if recipe.get("prep_time"):
                                        ui.html(f'<span class="{theme["chip_bg"]} {theme["border"]} rounded-full px-3 py-1 text-xs">⏱️ {recipe.get("prep_time")}</span>')
                                    if recipe.get("cook_time"):
                                        ui.html(f'<span class="{theme["chip_bg"]} {theme["border"]} rounded-full px-3 py-1 text-xs">🔥 {recipe.get("cook_time")}</span>')
                                
                                # Signature element highlight
                                if recipe.get("signature_element"):
                                    with ui.row().classes('items-center gap-2 mt-2'):
                                        ui.html('<div class="text-lg">✨</div>')
                                        ui.html(f'<span class="text-sm font-medium {theme["text_primary"]}">{recipe.get("signature_element")}</span>')
                            
                            # Rating section
                            if saved_meal_plan_id:
                                with ui.row().classes('justify-end mb-4'):
                                    with ui.column().classes('items-end'):
                                        ui.html(f'<span class="text-sm {theme["text_secondary"]} mb-1">Rate this recipe:</span>')
                                        
                                        def rate_recipe(recipe_idx: int, recipe_title: str, rating: int):
                                            try:
                                                db = next(get_db())
                                                create_or_update_recipe_rating(
                                                    db, current_user['id'], saved_meal_plan_id, recipe_idx, recipe_title, rating
                                                )
                                                ui.notify(f'Rated "{recipe_title}" {rating} star{"s" if rating != 1 else ""} ⭐', type='positive')
                                            except Exception as e:
                                                ui.notify(f'Rating failed: {str(e)}', type='negative')
                                        
                                        with ui.row().classes('gap-1 mt-2'):
                                            for star in range(1, 6):
                                                star_button = ui.button(
                                                    '⭐',
                                                    on_click=lambda idx=i-1, title=recipe.get("name", "Untitled Recipe"), r=star: rate_recipe(idx, title, r)
                                                ).classes('text-lg bg-transparent border-none p-1 hover:scale-110 transition-transform cursor-pointer opacity-60 hover:opacity-100').style('min-width: 28px; min-height: 28px;')
                                                
                                                star_labels = {1: 'Poor', 2: 'Fair', 3: 'Good', 4: 'Very Good', 5: 'Excellent'}
                                                star_button.tooltip(f'{star} star{"s" if star != 1 else ""} - {star_labels[star]}')
                            
                            with ui.row().classes('gap-8 w-full'):
                                # Left column - Ingredients
                                with ui.column().classes('flex-1'):
                                    with ui.row().classes('items-center gap-3 mb-4'):
                                        ui.html('<div class="text-2xl">🛒</div>')
                                        ui.html(f'<h4 class="text-lg font-semibold {theme["text_primary"]} mb-0">Ingredients</h4>')
                                    
                                    with ui.column().classes('gap-2'):
                                        for ingredient in recipe.get("ingredients", []):
                                            with ui.column().classes('gap-1'):
                                                with ui.row().classes('items-center gap-3'):
                                                    ui.html('<div class="w-2 h-2 bg-emerald-400 rounded-full flex-shrink-0"></div>')
                                                    # Handle both string and object ingredient formats
                                                    if isinstance(ingredient, dict):
                                                        quantity = ingredient.get("quantity", "")
                                                        unit = ingredient.get("unit", "")
                                                        item = ingredient.get("item", "")
                                                        display_text = f"{quantity} {unit} {item}".strip()
                                                        
                                                        # Show ingredient notes if available
                                                        if ingredient.get("notes"):
                                                            ui.html(f'<div class="flex-1"><span class="text-sm {theme["text_primary"]}">{display_text}</span><br><span class="text-xs {theme["text_secondary"]} italic ml-5">💡 {ingredient.get("notes")}</span></div>')
                                                        else:
                                                            ui.html(f'<span class="text-sm {theme["text_primary"]}">{display_text}</span>')
                                                    else:
                                                        display_text = str(ingredient) if ingredient else ""
                                                        if display_text:
                                                            ui.html(f'<span class="text-sm {theme["text_primary"]}">{display_text}</span>')
                                
                                # Right column - Instructions
                                with ui.column().classes('flex-1'):
                                    with ui.row().classes('items-center gap-3 mb-4'):
                                        ui.html('<div class="text-2xl">👨‍🍳</div>')
                                        ui.html(f'<h4 class="text-lg font-semibold {theme["text_primary"]} mb-0">Instructions</h4>')
                                    
                                    with ui.column().classes('gap-3'):
                                        for j, step in enumerate(recipe.get("instructions", []), 1):
                                            if step and step.strip():
                                                with ui.row().classes('items-start gap-3'):
                                                    ui.html(f'<div class="flex-shrink-0 w-8 h-8 bg-emerald-500 text-white rounded-full flex items-center justify-center text-sm font-bold">{j}</div>')
                                                    ui.html(f'<p class="text-sm {theme["text_primary"]} leading-relaxed flex-1 pt-1">{step}</p>')
                            
                            # Chef Tips and Presentation (if available)
                            if recipe.get("chef_tips") or recipe.get("presentation"):
                                with ui.row().classes('gap-8 w-full mt-6 pt-6 border-t'):
                                    # Chef Tips
                                    if recipe.get("chef_tips"):
                                        with ui.column().classes('flex-1'):
                                            with ui.row().classes('items-center gap-3 mb-4'):
                                                ui.html('<div class="text-2xl">💡</div>')
                                                ui.html(f'<h4 class="text-lg font-semibold {theme["text_primary"]} mb-0">Chef Tips</h4>')
                                            with ui.column().classes('gap-2'):
                                                for tip in recipe.get("chef_tips", []):
                                                    with ui.row().classes('items-start gap-3'):
                                                        ui.html('<div class="w-2 h-2 bg-yellow-400 rounded-full flex-shrink-0 mt-2"></div>')
                                                        ui.html(f'<p class="text-sm {theme["text_primary"]} leading-relaxed flex-1">{tip}</p>')
                                    
                                    # Presentation
                                    if recipe.get("presentation"):
                                        with ui.column().classes('flex-1'):
                                            with ui.row().classes('items-center gap-3 mb-4'):
                                                ui.html('<div class="text-2xl">🎨</div>')
                                                ui.html(f'<h4 class="text-lg font-semibold {theme["text_primary"]} mb-0">Presentation</h4>')
                                            ui.html(f'<p class="text-sm {theme["text_primary"]} leading-relaxed">{recipe.get("presentation")}</p>')
        
        # Display shopping list
        if shopping_list:
            with ui.card().classes(f'recipe-card {theme["success_bg"]} {theme["border"]} rounded-3xl p-6 sm:p-8 w-full mt-8'):
                with ui.column().classes('items-center text-center mb-6'):
                    ui.html('<div class="text-4xl mb-4">🛒</div>')
                    ui.html(f'<h2 class="text-2xl font-bold {theme["text_primary"]} mb-4">Smart Shopping List</h2>')
                    ui.html(f'<p class="text-lg {theme["text_secondary"]} max-w-2xl mx-auto">Everything you need for your {len(recipes)} recipes, intelligently optimized.</p>')
                
                with ui.row().classes('gap-3 flex-wrap justify-center'):
                    for item in shopping_list:
                        quantity = item.get("quantity", "")
                        unit = item.get("unit", "")
                        item_name = item.get("item", "")
                        
                        # Only display if we have an item name
                        if item_name:
                            display_text = f"{quantity} {unit} {item_name}".strip()
                            with ui.row().classes(f'chip-modern {theme["chip_bg"]} {theme["border"]} rounded-2xl px-6 py-3 items-center gap-3 min-w-fit'):
                                ui.html('<div class="w-3 h-3 bg-emerald-400 rounded-full flex-shrink-0"></div>')
                                ui.html(f'<span class="text-sm font-semibold {theme["text_primary"]}">{display_text}</span>')
        
        # Export and save buttons
        with ui.row().classes('justify-center w-full mt-8 gap-4'):
            def export_to_pdf():
                """Export recipes to PDF"""
                try:
                    # Get current user preferences for PDF
                    liked_foods = []
                    disliked_foods = []
                    serving_size = recipes[0].get("servings", 4) if recipes else 4
                    
                    # Try to get preferences from database
                    try:
                        db = next(get_db())
                        from ..database.models import User
                        user = db.query(User).filter(User.id == current_user['id']).first()
                        if user:
                            liked_foods = [f.strip() for f in user.liked_foods.split(',') if f.strip()] if user.liked_foods else []
                            disliked_foods = [f.strip() for f in user.disliked_foods.split(',') if f.strip()] if user.disliked_foods else []
                    except Exception as e:
                        print(f"Error loading user preferences for PDF: {e}")
                    
                    pdf_data = generate_pdf_export(recipes, shopping_list, liked_foods, disliked_foods, serving_size)
                    
                    # Create download
                    filename = f"FoodPal_Recipes_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                    ui.download(pdf_data, filename)
                    ui.notify('PDF exported successfully!', type='positive')
                    
                except Exception as e:
                    ui.notify(f'Export failed: {str(e)}', type='negative')
            
            ui.button(
                '📄 Export to PDF',
                on_click=export_to_pdf
            ).classes(f'{theme["button_secondary"]} text-white font-semibold py-3 px-6 rounded-xl shadow-lg')
            
            if saved_meal_plan_id:
                ui.button(
                    '📋 View Meal Plan',
                    on_click=lambda: ui.navigate.to(f'/meal-plan/{saved_meal_plan_id}')
                ).classes(f'{theme["button_primary"]} text-white font-semibold py-3 px-6 rounded-xl shadow-lg')