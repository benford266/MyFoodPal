from nicegui import ui
import json
from typing import Dict, List, Any

from ..database.connection import get_db
from ..database.operations import create_or_update_recipe_rating
from ..utils.pdf_export import generate_pdf_export

def display_meal_plan_details(meal_plan, recipes: List[Dict[str, Any]], shopping_list: List[Dict[str, str]], ratings_dict: Dict, theme: Dict[str, str], current_user: Dict, meal_plan_id: int):
    """Display detailed meal plan view"""
    
    with ui.column().classes(f'min-h-screen {theme["bg_primary"]} {theme["text_primary"]} p-8'):
        # Header
        with ui.row().classes('items-center justify-between w-full mb-8'):
            with ui.row().classes('items-center gap-4'):
                ui.button(
                    '←',
                    on_click=lambda: ui.navigate.to('/history')
                ).classes(f'{theme["button_secondary"]} rounded-full w-12 h-12 text-xl').style('color: #1f2937 !important;')
                ui.html(f'<h1 class="text-3xl font-bold {theme["gradient_text"]}">📋 {meal_plan.name}</h1>')
            
            # User info and date
            with ui.column().classes('text-right'):
                ui.html(f'<span class="text-lg {theme["text_secondary"]}">{current_user["name"]}\'s Kitchen</span>')
                ui.html(f'<span class="text-sm {theme["text_secondary"]}">{meal_plan.created_at.strftime("%B %d, %Y at %I:%M %p")}</span>')
        
        # Meal plan info
        with ui.row().classes('gap-4 mb-8'):
            ui.html(f'<span class="{theme["chip_bg"]} {theme["border"]} rounded-full px-4 py-2 text-sm font-medium">{meal_plan.recipe_count} recipes</span>')
            ui.html(f'<span class="{theme["chip_bg"]} {theme["border"]} rounded-full px-4 py-2 text-sm font-medium">{meal_plan.serving_size} servings</span>')
            if meal_plan.rating:
                ui.html(f'<span class="{theme["chip_bg"]} {theme["border"]} rounded-full px-4 py-2 text-sm font-medium">{"⭐" * meal_plan.rating} ({meal_plan.rating}/5)</span>')
        
        # Show preferences snapshot
        if meal_plan.liked_foods_snapshot or meal_plan.disliked_foods_snapshot or getattr(meal_plan, 'must_use_ingredients_snapshot', None):
            with ui.card().classes(f'{theme["card"]} {theme["border"]} rounded-2xl p-6 mb-8'):
                ui.html(f'<h3 class="text-lg font-bold {theme["text_primary"]} mb-4">🎯 Preferences Used</h3>')
                with ui.row().classes('gap-6 text-sm'):
                    if meal_plan.liked_foods_snapshot:
                        with ui.column():
                            ui.html(f'<span class="font-medium {theme["text_primary"]}">💚 Liked Foods:</span>')
                            ui.html(f'<span class="{theme["text_secondary"]}">{meal_plan.liked_foods_snapshot}</span>')
                    if meal_plan.disliked_foods_snapshot:
                        with ui.column():
                            ui.html(f'<span class="font-medium {theme["text_primary"]}">🚫 Avoided Foods:</span>')
                            ui.html(f'<span class="{theme["text_secondary"]}">{meal_plan.disliked_foods_snapshot}</span>')
                    if getattr(meal_plan, 'must_use_ingredients_snapshot', None):
                        with ui.column():
                            ui.html(f'<span class="font-medium {theme["text_primary"]}">🕐 Must Use (Expiring):</span>')
                            ui.html(f'<span class="{theme["text_secondary"]}">{meal_plan.must_use_ingredients_snapshot}</span>')
        
        # Display recipes
        if recipes:
            ui.html(f'<h2 class="text-2xl font-bold {theme["text_primary"]} mb-6">🍽️ Your Recipes</h2>')
            
            with ui.column().classes('gap-6'):
                for i, recipe in enumerate(recipes, 1):
                    # Skip if recipe is not a dict or has an error
                    if not isinstance(recipe, dict) or "error" in recipe:
                        continue
                    
                    recipe_index = i - 1  # 0-based index for database
                    current_rating = ratings_dict.get(recipe_index)
                    
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
                                
                                # Recipe rating section
                                with ui.column().classes('items-end'):
                                    rating_value = current_rating.rating if current_rating else 0
                                    if rating_value > 0:
                                        ui.html(f'<span class="text-sm {theme["text_primary"]} font-medium mb-1">Your Rating:</span>')
                                        ui.html(f'<span class="text-lg">{"⭐" * rating_value}{"☆" * (5-rating_value)}</span>')
                                    else:
                                        ui.html(f'<span class="text-sm {theme["text_secondary"]} mb-1">Rate this recipe:</span>')
                                    
                                    # Star rating buttons
                                    def rate_recipe(recipe_idx: int, recipe_title: str, rating: int):
                                        try:
                                            db = next(get_db())
                                            create_or_update_recipe_rating(
                                                db, current_user['id'], meal_plan_id, recipe_idx, recipe_title, rating
                                            )
                                            ui.notify(f'Rated "{recipe_title}" {rating} star{"s" if rating != 1 else ""} ⭐', type='positive')
                                            # Force page refresh to show updated rating
                                            ui.navigate.to(f'/meal-plan/{meal_plan_id}', new_tab=False)
                                        except Exception as e:
                                            ui.notify(f'Rating failed: {str(e)}', type='negative')
                                    
                                    with ui.row().classes('gap-1 mt-2'):
                                        for star in range(1, 6):
                                            star_icon = '⭐' if rating_value >= star else '☆'
                                            button_class = f'text-lg bg-transparent border-none p-1 hover:scale-110 transition-transform cursor-pointer'
                                            if rating_value < star:
                                                button_class += ' opacity-60 hover:opacity-100'
                                            
                                            star_button = ui.button(
                                                star_icon,
                                                on_click=lambda idx=recipe_index, title=recipe.get("name", "Untitled Recipe"), r=star: rate_recipe(idx, title, r)
                                            ).classes(button_class).style('min-width: 28px; min-height: 28px;')
                                            
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
                                            with ui.row().classes('items-center gap-3'):
                                                ui.html('<div class="w-2 h-2 bg-emerald-400 rounded-full flex-shrink-0"></div>')
                                                # Handle both string and object ingredient formats
                                                if isinstance(ingredient, dict):
                                                    quantity = ingredient.get("quantity", "")
                                                    unit = ingredient.get("unit", "")
                                                    item = ingredient.get("item", "")
                                                    display_text = f"{quantity} {unit} {item}".strip()
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
        
        # Export button
        with ui.row().classes('justify-center w-full mt-8'):
            def export_to_pdf():
                """Export this meal plan to PDF"""
                try:
                    # Generate PDF with the historical data
                    pdf_data = generate_pdf_export(
                        recipes, 
                        shopping_list, 
                        meal_plan.liked_foods_snapshot.split(',') if meal_plan.liked_foods_snapshot else [],
                        meal_plan.disliked_foods_snapshot.split(',') if meal_plan.disliked_foods_snapshot else [],
                        meal_plan.serving_size
                    )
                    
                    # Create download with meal plan name and date
                    filename = f"FoodPal_{meal_plan.name.replace(' ', '_')}_{meal_plan.created_at.strftime('%Y%m%d')}.pdf"
                    
                    # Trigger download
                    ui.download(pdf_data, filename)
                    ui.notify('PDF exported successfully!', type='positive')
                    
                except Exception as e:
                    ui.notify(f'Export failed: {str(e)}', type='negative')
            
            ui.button(
                '📄 Export to PDF',
                on_click=export_to_pdf
            ).classes(f'{theme["button_secondary"]} text-white font-semibold py-3 px-6 rounded-xl shadow-lg')