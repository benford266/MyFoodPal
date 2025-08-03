from nicegui import ui
import json
from datetime import datetime
from typing import List, Dict, Any

from ..database.connection import get_db
from ..database.operations import create_or_update_recipe_rating
from ..utils.pdf_export import generate_pdf_export
from .components import create_modern_recipe_card, create_loading_recipe_card

def _create_shopping_item(item: Dict[str, str], theme: Dict[str, str]):
    """Create a modern shopping list item chip"""
    quantity = item.get("quantity", "")
    unit = item.get("unit", "")
    item_name = item.get("item", "")
    
    if item_name:
        display_text = f"{quantity} {unit} {item_name}".strip()
        ui.html(f'''
            <div class="{theme["chip_bg"]} rounded-xl px-4 py-3 flex items-center gap-3 min-w-fit transition-all duration-200 hover:scale-105 hover:shadow-md border {theme["border"]} group cursor-pointer">
                <div class="w-3 h-3 bg-emerald-400 rounded-full flex-shrink-0 group-hover:bg-emerald-500 transition-colors"></div>
                <span class="text-sm font-medium {theme["text_primary"]} whitespace-nowrap">{display_text}</span>
            </div>
        ''')

def display_recipes_and_shopping_list(container, recipes: List[Dict[str, Any]], shopping_list: List[Dict[str, str]], theme: Dict[str, str], current_user: Dict, saved_meal_plan_id: int = None):
    """Display recipes and shopping list in the main page"""
    container.clear()
    
    with container:
        # Display recipes using modern components
        if recipes:
            ui.html(f'<h2 class="text-3xl font-bold {theme["gradient_text"]} mb-8 text-center">🍽️ Your Personalized Recipes</h2>')
            
            with ui.column().classes('gap-8'):
                for i, recipe in enumerate(recipes, 1):
                    # Handle error recipes
                    if not isinstance(recipe, dict):
                        with ui.card().classes(f'{theme["error_bg"]} rounded-2xl p-6 text-center border {theme["border"]}'):
                            ui.html('<div class="text-4xl mb-4">❌</div>')
                            ui.html(f'<h3 class="text-xl font-bold {theme["error_text"]} mb-4">Recipe {i} Generation Failed</h3>')
                            ui.html(f'<p class="text-sm {theme["text_secondary"]}">Unexpected response format</p>')
                        continue
                    
                    if "error" in recipe:
                        with ui.card().classes(f'{theme["error_bg"]} rounded-2xl p-6 text-center border {theme["border"]}'):
                            ui.html('<div class="text-4xl mb-4">❌</div>')
                            ui.html(f'<h3 class="text-xl font-bold {theme["error_text"]} mb-4">Recipe {i} Generation Failed</h3>')
                            ui.html(f'<p class="text-sm {theme["text_secondary"]}">{recipe.get("error", "Unknown error")}</p>')
                        continue
                    
                    # Create rating handler
                    def rate_recipe(recipe_idx: int, recipe_title: str, rating: int):
                        try:
                            db = next(get_db())
                            create_or_update_recipe_rating(
                                db, current_user['id'], saved_meal_plan_id, recipe_idx, recipe_title, rating
                            )
                            ui.notify(f'Rated "{recipe_title}" {rating} star{"s" if rating != 1 else ""} ⭐', type='positive')
                        except Exception as e:
                            ui.notify(f'Rating failed: {str(e)}', type='negative')
                    
                    # Create modern recipe card
                    create_modern_recipe_card(
                        recipe=recipe,
                        index=i,
                        theme=theme,
                        on_rate=rate_recipe if saved_meal_plan_id else None,
                        saved_meal_plan_id=saved_meal_plan_id,
                        show_rating=bool(saved_meal_plan_id),
                        show_image=True,
                        card_style="featured" if i == 1 else "default"  # First recipe gets featured styling
                    )
        
        # Display shopping list with modern design
        if shopping_list:
            with ui.card().classes(f'{theme["card_elevated"]} rounded-3xl p-8 w-full mt-12 border {theme["border"]}'):
                # Header section
                with ui.column().classes('items-center text-center mb-8'):
                    ui.html(f'''
                        <div class="w-20 h-20 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-full flex items-center justify-center text-4xl text-white shadow-lg mb-4">
                            🛒
                        </div>
                    ''')
                    ui.html(f'<h2 class="text-3xl font-bold {theme["gradient_text"]} mb-4">Smart Shopping List</h2>')
                    ui.html(f'<p class="text-lg {theme["text_secondary"]} max-w-3xl mx-auto">Everything you need for your {len(recipes)} recipes, intelligently optimized and organized for efficient shopping.</p>')
                
                # Shopping list items with modern grid layout
                with ui.column().classes('gap-6'):
                    # Group items by category (if available) or show in grid
                    categorized_items = {}
                    uncategorized_items = []
                    
                    for item in shopping_list:
                        if item.get("item"):
                            category = item.get("category", "Other")
                            if category and category != "Other":
                                if category not in categorized_items:
                                    categorized_items[category] = []
                                categorized_items[category].append(item)
                            else:
                                uncategorized_items.append(item)
                    
                    # Display categorized items
                    for category, items in categorized_items.items():
                        with ui.column().classes('mb-6'):
                            ui.html(f'<h3 class="text-lg font-semibold {theme["text_primary"]} mb-3 flex items-center gap-2">')
                            
                            # Category icons
                            category_icons = {
                                "Proteins": "🥩", "Vegetables": "🥬", "Fruits": "🍎", 
                                "Dairy": "🥛", "Grains": "🌾", "Spices": "🧂",
                                "Pantry": "🥫", "Frozen": "🧊", "Bakery": "🥖"
                            }
                            icon = category_icons.get(category, "📦")
                            
                            ui.html(f'{icon} {category}</h3>')
                            
                            with ui.row().classes('gap-3 flex-wrap'):
                                for item in items:
                                    _create_shopping_item(item, theme)
                    
                    # Display uncategorized items
                    if uncategorized_items:
                        if categorized_items:  # Only show "Other" header if there are categories
                            ui.html(f'<h3 class="text-lg font-semibold {theme["text_primary"]} mb-3 flex items-center gap-2">📦 Other Items</h3>')
                        
                        with ui.row().classes('gap-3 flex-wrap'):
                            for item in uncategorized_items:
                                _create_shopping_item(item, theme)
        
        # Modern action buttons
        with ui.row().classes('justify-center w-full mt-12 gap-6'):
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
                    ui.notify('📄 PDF exported successfully!', type='positive')
                    
                except Exception as e:
                    ui.notify(f'Export failed: {str(e)}', type='negative')
            
            # Export button with icon and modern styling
            with ui.button(on_click=export_to_pdf).classes(f'{theme["button_secondary"]} font-semibold py-4 px-8 rounded-xl shadow-lg transition-all duration-200'):
                with ui.row().classes('items-center gap-3'):
                    ui.html('<span class="text-xl">📄</span>')
                    ui.html('<span>Export to PDF</span>')
            
            # View meal plan button (if available)
            if saved_meal_plan_id:
                with ui.button(on_click=lambda: ui.navigate.to(f'/meal-plan/{saved_meal_plan_id}')).classes(f'{theme["button_primary"]} font-semibold py-4 px-8 rounded-xl shadow-lg transition-all duration-200'):
                    with ui.row().classes('items-center gap-3'):
                        ui.html('<span class="text-xl">📋</span>')
                        ui.html('<span>View Meal Plan</span>')
                        
            # Share button (future feature)
            with ui.button().classes(f'{theme["button_ghost"]} font-semibold py-4 px-8 rounded-xl transition-all duration-200').props('disabled'):
                with ui.row().classes('items-center gap-3'):
                    ui.html('<span class="text-xl">🔗</span>')
                    ui.html('<span>Share Recipes</span>')