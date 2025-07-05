from nicegui import ui, app
from fastapi import Depends
import json
from datetime import datetime
from typing import List, Dict, Any

from ..database.connection import get_db
from ..database.operations import (
    authenticate_user, get_user_by_email, create_user, 
    create_meal_plan, get_user_meal_plans, get_meal_plan_recipe_ratings,
    create_or_update_recipe_rating
)
from ..database.models import MealPlan, User
from ..models.schemas import UserCreate, MealPlanCreate
from ..services.recipe_generator import RecipeGenerator
from ..utils.session import get_current_user, set_current_user, clear_current_user
from ..utils.theme import get_theme_classes
from ..utils.shopping_list import generate_shopping_list
from ..utils.pdf_export import generate_pdf_export
from ..config import OLLAMA_BASE_URL, OLLAMA_MODEL

@ui.page('/login')
def login_page():
    theme = get_theme_classes()
    
    # Add viewport and Material Icons
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    ui.add_head_html('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">')
    
    with ui.column().classes(f'min-h-screen {theme["bg_primary"]} {theme["text_primary"]} items-center justify-center p-4 sm:p-8'):
        with ui.card().classes(f'{theme["card"]} {theme["border"]} rounded-3xl p-6 sm:p-8 w-full max-w-md shadow-2xl'):
            # Logo and title
            ui.html('<div class="text-6xl text-center mb-6">🍽️</div>')
            ui.html(f'<h1 class="text-2xl sm:text-3xl font-bold {theme["gradient_text"]} text-center mb-4">Welcome to FoodPal</h1>')
            ui.html(f'<p class="text-sm {theme["text_secondary"]} text-center mb-8">Your AI-powered recipe companion</p>')
            
            # Login/Register toggle
            is_login = {'value': True}
            toggle_container = ui.row().classes('w-full mb-6')
            form_container = ui.column().classes('w-full gap-4')
            
            def set_login_mode():
                is_login['value'] = True
                update_form()
                update_buttons()
            
            def set_register_mode():
                is_login['value'] = False
                update_form()
                update_buttons()
            
            def update_buttons():
                toggle_container.clear()
                with toggle_container:
                    if is_login['value']:
                        ui.button('Login', on_click=set_login_mode).classes('flex-1 py-3 px-4 rounded-l-xl font-semibold').style(
                            'background-color: #059669; color: white; border: none; font-weight: 600; min-height: 48px;'
                        )
                        ui.button('Register', on_click=set_register_mode).classes('flex-1 py-3 px-4 rounded-r-xl font-semibold').style(
                            'background-color: white; color: #374151; border: 1px solid #d1d5db; font-weight: 600; min-height: 48px;'
                        )
                    else:
                        ui.button('Login', on_click=set_login_mode).classes('flex-1 py-3 px-4 rounded-l-xl font-semibold').style(
                            'background-color: white; color: #374151; border: 1px solid #d1d5db; font-weight: 600; min-height: 48px;'
                        )
                        ui.button('Register', on_click=set_register_mode).classes('flex-1 py-3 px-4 rounded-r-xl font-semibold').style(
                            'background-color: #059669; color: white; border: none; font-weight: 600; min-height: 48px;'
                        )
            
            def update_form():
                form_container.clear()
                with form_container:
                    if is_login['value']:
                        # Login form
                        email_input = ui.input('Email', placeholder='your@email.com').classes(
                            f'{theme["input_bg"]} rounded-xl border-2 {theme["border"]} p-4 w-full'
                        )
                        password_input = ui.input('Password', password=True).classes(
                            f'{theme["input_bg"]} rounded-xl border-2 {theme["border"]} p-4 w-full'
                        )
                        
                        async def handle_login():
                            try:
                                db = next(get_db())
                                user = authenticate_user(db, email_input.value, password_input.value)
                                if user:
                                    set_current_user(user)
                                    ui.notify(f'Welcome back, {user.name}!', type='positive')
                                    ui.navigate.to('/')
                                else:
                                    ui.notify('Invalid email or password', type='negative')
                            except Exception as e:
                                ui.notify(f'Login failed: {str(e)}', type='negative')
                        
                        ui.button('Login', on_click=handle_login).classes(
                            f'{theme["button_primary"]} text-white w-full py-4 rounded-xl text-lg font-semibold'
                        )
                    else:
                        # Register form
                        name_input = ui.input('Full Name', placeholder='John Doe').classes(
                            f'{theme["input_bg"]} rounded-xl border-2 {theme["border"]} p-4 w-full'
                        )
                        email_input = ui.input('Email', placeholder='your@email.com').classes(
                            f'{theme["input_bg"]} rounded-xl border-2 {theme["border"]} p-4 w-full'
                        )
                        password_input = ui.input('Password', password=True).classes(
                            f'{theme["input_bg"]} rounded-xl border-2 {theme["border"]} p-4 w-full'
                        )
                        
                        async def handle_register():
                            try:
                                db = next(get_db())
                                if get_user_by_email(db, email_input.value):
                                    ui.notify('Email already registered', type='negative')
                                    return
                                
                                user_data = UserCreate(
                                    email=email_input.value,
                                    password=password_input.value,
                                    name=name_input.value
                                )
                                user = create_user(db, user_data)
                                set_current_user(user)
                                ui.notify(f'Welcome to FoodPal, {user.name}!', type='positive')
                                ui.navigate.to('/')
                            except Exception as e:
                                ui.notify(f'Registration failed: {str(e)}', type='negative')
                        
                        ui.button('Create Account', on_click=handle_register).classes(
                            f'{theme["button_primary"]} text-white w-full py-4 rounded-xl text-lg font-semibold'
                        )
            
            update_buttons()
            update_form()

@ui.page('/')
def main_page():
    # Check if user is logged in
    current_user = get_current_user()
    if current_user is None:
        ui.navigate.to('/login')
        return
    
    theme = get_theme_classes()
    
    # Add viewport and Material Icons
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    ui.add_head_html('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">')
    
    # Create recipe generator
    recipe_generator = RecipeGenerator(OLLAMA_BASE_URL, OLLAMA_MODEL)
    
    with ui.column().classes(f'min-h-screen {theme["bg_primary"]} {theme["text_primary"]} p-4 sm:p-8'):
        # Header with logout
        with ui.row().classes('items-center justify-between w-full mb-8'):
            ui.html(f'<h1 class="text-3xl sm:text-4xl font-bold {theme["gradient_text"]}">🍽️ FoodPal</h1>')
            with ui.row().classes('items-center gap-4'):
                ui.html(f'<span class="text-lg {theme["text_secondary"]}">{current_user["name"]}\'s Kitchen</span>')
                with ui.row().classes('gap-2'):
                    ui.button(
                        'Meal Plans',
                        on_click=lambda: ui.navigate.to('/history')
                    ).classes(f'{theme["button_secondary"]} rounded-xl px-3 py-2 text-sm').style('color: #1f2937 !important;')
                    ui.button(
                        'Recipe History',
                        on_click=lambda: ui.navigate.to('/recipe-history')
                    ).classes(f'{theme["button_secondary"]} rounded-xl px-3 py-2 text-sm').style('color: #1f2937 !important;')
                ui.button(
                    'Logout',
                    on_click=lambda: [clear_current_user(), ui.navigate.to('/login')]
                ).classes(f'{theme["button_secondary"]} rounded-xl px-4 py-2').style('color: #1f2937 !important;')
        
        # Main content area
        with ui.row().classes('gap-8 w-full'):
            # Left column - Settings
            with ui.column().classes('flex-1 max-w-md'):
                with ui.card().classes(f'{theme["card"]} {theme["border"]} rounded-3xl p-6 sm:p-8'):
                    ui.html(f'<h2 class="text-2xl font-bold {theme["text_primary"]} mb-4">🎯 Your Preferences</h2>')
                    ui.html(f'<p class="text-sm {theme["text_secondary"]} mb-6">💡 <strong>Tip:</strong> Recipes can include any ingredients! "Love" preferences are favored when possible, "Avoid" foods are never used, and empty fields mean anything goes.</p>')
                    
                    # Load current preferences from user
                    db = next(get_db())
                    current_user_data = db.query(User).filter(User.id == current_user['id']).first()
                    
                    liked_foods_input = ui.textarea(
                        'Foods You Love (Optional) 💚',
                        placeholder='e.g., chicken, broccoli, pasta, garlic... (recipes will try to include these when possible)',
                        value=current_user_data.liked_foods if current_user_data else ""
                    ).classes(f'{theme["input_bg"]} rounded-xl border-2 {theme["border"]} p-4 w-full h-24')
                    
                    disliked_foods_input = ui.textarea(
                        'Foods You Avoid 🚫',
                        placeholder='e.g., mushrooms, seafood, spicy food... (recipes will never include these)',
                        value=current_user_data.disliked_foods if current_user_data else ""
                    ).classes(f'{theme["input_bg"]} rounded-xl border-2 {theme["border"]} p-4 w-full h-24')
                    
                    must_use_input = ui.textarea(
                        'Must Use (Expiring Soon) 🕐',
                        placeholder='e.g., leftover chicken, spinach expiring tomorrow...',
                        value=current_user_data.must_use_ingredients if hasattr(current_user_data, 'must_use_ingredients') and current_user_data.must_use_ingredients else ""
                    ).classes(f'{theme["input_bg"]} rounded-xl border-2 border-orange-300 p-4 w-full h-24')
                    
                    with ui.row().classes('gap-4 w-full mt-4'):
                        recipe_count_input = ui.number('Number of Recipes', value=5, min=1, max=10).classes(
                            f'{theme["input_bg"]} rounded-xl border-2 {theme["border"]} p-4 flex-1'
                        )
                        serving_size_input = ui.number('Serving Size', value=4, min=1, max=12).classes(
                            f'{theme["input_bg"]} rounded-xl border-2 {theme["border"]} p-4 flex-1'
                        )
            
            # Right column - Results
            with ui.column().classes('flex-2'):
                results_container = ui.column().classes('w-full')
                
                with results_container:
                    # Welcome message
                    with ui.card().classes(f'{theme["success_bg"]} {theme["border"]} rounded-3xl p-6 sm:p-8 text-center'):
                        ui.html('<div class="text-4xl mb-4">👋</div>')
                        ui.html(f'<h2 class="text-2xl font-bold {theme["text_primary"]} mb-4">Ready to Cook Something Amazing?</h2>')
                        ui.html(f'<p class="text-lg {theme["text_secondary"]} mb-6">We\'ll create diverse, delicious recipes! Share your preferences to personalize them, or leave blank for surprise recipes. We only avoid foods you specifically dislike.</p>')
                        
                        async def generate_recipes_handler():
                            # Update user preferences in database
                            try:
                                db = next(get_db())
                                user = db.query(User).filter(User.id == current_user['id']).first()
                                if user:
                                    user.liked_foods = liked_foods_input.value
                                    user.disliked_foods = disliked_foods_input.value
                                    user.must_use_ingredients = must_use_input.value
                                    db.commit()
                            except Exception as e:
                                print(f"Error updating preferences: {e}")
                            
                            # Clear results and show progress
                            results_container.clear()
                            with results_container:
                                with ui.card().classes(f'{theme["card"]} {theme["border"]} rounded-3xl p-6 sm:p-8 text-center'):
                                    ui.html('<div class="text-4xl mb-4">🍳</div>')
                                    ui.html(f'<h2 class="text-2xl font-bold {theme["text_primary"]} mb-4">Cooking Up Your Recipes...</h2>')
                                    progress_label = ui.html(f'<p class="text-lg {theme["text_secondary"]}">Initializing...</p>')
                                    progress_bar = ui.linear_progress(value=0).classes('w-full')
                            
                            # Generate recipes
                            try:
                                liked_foods = [f.strip() for f in liked_foods_input.value.split(',') if f.strip()]
                                disliked_foods = [f.strip() for f in disliked_foods_input.value.split(',') if f.strip()]
                                must_use_ingredients = [f.strip() for f in must_use_input.value.split(',') if f.strip()]
                                
                                async def progress_callback(message: str):
                                    progress_label.content = f'<p class="text-lg {theme["text_secondary"]}">{message}</p>'
                                    # Update progress bar based on recipe number
                                    if "recipe" in message.lower():
                                        try:
                                            parts = message.split('/')
                                            if len(parts) >= 2:
                                                current = int(parts[0].split()[-1])
                                                total = int(parts[1].split()[0])
                                                progress_bar.value = current / total
                                        except:
                                            pass
                                
                                # Get database session for history tracking
                                db = next(get_db())
                                
                                recipes = await recipe_generator.generate_recipes(
                                    liked_foods, disliked_foods, 
                                    int(recipe_count_input.value), 
                                    int(serving_size_input.value),
                                    progress_callback,
                                    current_user['id'],  # Pass user ID for history tracking
                                    db,                  # Pass database session
                                    must_use_ingredients # Pass must-use ingredients
                                )
                                
                                # Generate shopping list
                                shopping_list = generate_shopping_list(recipes)
                                
                                # Save meal plan to database
                                try:
                                    meal_plan_data = MealPlanCreate(
                                        name=f"Meal Plan - {datetime.now().strftime('%B %d, %Y')}",
                                        serving_size=int(serving_size_input.value),
                                        recipe_count=int(recipe_count_input.value),
                                        recipes_json=json.dumps(recipes),
                                        shopping_list_json=json.dumps(shopping_list),
                                        liked_foods_snapshot=liked_foods_input.value,
                                        disliked_foods_snapshot=disliked_foods_input.value,
                                        must_use_ingredients_snapshot=must_use_input.value
                                    )
                                    saved_meal_plan = create_meal_plan(db, meal_plan_data, current_user['id'])
                                    print(f"Successfully saved meal plan with ID: {saved_meal_plan.id}")
                                except Exception as e:
                                    print(f"Error saving meal plan: {e}")
                                
                                # Display results
                                from .recipe_display import display_recipes_and_shopping_list
                                display_recipes_and_shopping_list(results_container, recipes, shopping_list, theme, current_user, saved_meal_plan.id if 'saved_meal_plan' in locals() else None)
                                
                            except Exception as e:
                                results_container.clear()
                                with results_container:
                                    with ui.card().classes(f'{theme["error_bg"]} {theme["border"]} rounded-3xl p-6 text-center'):
                                        ui.html('<div class="text-4xl mb-4">❌</div>')
                                        ui.html(f'<h2 class="text-xl font-bold {theme["text_primary"]} mb-4">Generation Failed</h2>')
                                        ui.html(f'<p class="text-sm {theme["text_secondary"]}">{str(e)}</p>')
                        
                        ui.button(
                            '✨ Generate My Recipes',
                            on_click=generate_recipes_handler
                        ).classes(f'{theme["button_primary"]} text-white text-xl font-bold py-4 px-8 rounded-2xl shadow-lg')

@ui.page('/history')
def history_page():
    # Check if user is logged in
    current_user = get_current_user()
    if current_user is None:
        ui.navigate.to('/login')
        return
    
    theme = get_theme_classes()
    
    # Add viewport and Material Icons
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    ui.add_head_html('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">')
    
    with ui.column().classes(f'min-h-screen {theme["bg_primary"]} {theme["text_primary"]} p-8'):
        # Header
        with ui.row().classes('items-center justify-between w-full mb-8'):
            with ui.row().classes('items-center gap-4'):
                ui.button(
                    '←',
                    on_click=lambda: ui.navigate.to('/')
                ).classes(f'{theme["button_secondary"]} rounded-full w-12 h-12 text-xl').style('color: #1f2937 !important;')
                ui.html(f'<h1 class="text-3xl font-bold {theme["gradient_text"]}">📚 Your Meal Plans</h1>')
            
            # User info
            with ui.column().classes('text-right'):
                ui.html(f'<span class="text-lg {theme["text_secondary"]}">{current_user["name"]}\'s Kitchen</span>')
        
        # Load meal plans
        try:
            db = next(get_db())
            meal_plans = get_user_meal_plans(db, current_user['id'], limit=20)
            
            if meal_plans:
                ui.html(f'<p class="text-lg {theme["text_secondary"]} mb-6">You\'ve created {len(meal_plans)} meal plans. Here are your recent creations:</p>')
                
                with ui.column().classes('gap-6 w-full'):
                    for meal_plan in meal_plans:
                        with ui.card().classes(f'{theme["card"]} {theme["border"]} rounded-2xl p-6 cursor-pointer hover:shadow-lg transition-shadow').on('click', lambda e, plan_id=meal_plan.id: ui.navigate.to(f'/meal-plan/{plan_id}')):
                            with ui.row().classes('items-start justify-between gap-6'):
                                with ui.column().classes('flex-1'):
                                    ui.html(f'<h3 class="text-xl font-bold {theme["text_primary"]}">{meal_plan.name}</h3>')
                                    ui.html(f'<p class="text-sm {theme["text_secondary"]}">{meal_plan.created_at.strftime("%B %d, %Y at %I:%M %p")}</p>')
                                    
                                    with ui.row().classes('gap-2 mt-3'):
                                        ui.html(f'<span class="{theme["chip_bg"]} {theme["border"]} rounded-full px-3 py-1 text-sm">{meal_plan.recipe_count} recipes</span>')
                                        ui.html(f'<span class="{theme["chip_bg"]} {theme["border"]} rounded-full px-3 py-1 text-sm">{meal_plan.serving_size} servings</span>')
                                    
                                    if meal_plan.liked_foods_snapshot or meal_plan.disliked_foods_snapshot:
                                        with ui.column().classes('mt-3 gap-1'):
                                            if meal_plan.liked_foods_snapshot:
                                                ui.html(f'<span class="{theme["text_secondary"]}">💚 Liked: {meal_plan.liked_foods_snapshot[:50]}...</span>')
                                            if meal_plan.disliked_foods_snapshot:
                                                ui.html(f'<span class="{theme["text_secondary"]}">🚫 Avoided: {meal_plan.disliked_foods_snapshot[:50]}...</span>')
            else:
                # No meal plans yet
                with ui.card().classes(f'{theme["card"]} {theme["border"]} rounded-3xl p-8 text-center'):
                    ui.html('<div class="text-6xl mb-6">📝</div>')
                    ui.html(f'<h2 class="text-2xl font-bold {theme["text_primary"]} mb-4">No Meal Plans Yet</h2>')
                    ui.html(f'<p class="text-lg {theme["text_secondary"]} mb-6">Start creating personalized recipes to see them here!</p>')
                    ui.button(
                        '✨ Create First Meal Plan',
                        on_click=lambda: ui.navigate.to('/')
                    ).classes(f'{theme["button_primary"]} text-white font-semibold py-3 px-6 rounded-xl')
        
        except Exception as e:
            ui.notify(f'Error loading meal plans: {str(e)}', type='negative')

@ui.page('/recipe-history')
def recipe_history_page():
    # Check if user is logged in
    current_user = get_current_user()
    if current_user is None:
        ui.navigate.to('/login')
        return
    
    theme = get_theme_classes()
    
    # Add viewport and Material Icons
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    ui.add_head_html('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">')
    
    with ui.column().classes(f'min-h-screen {theme["bg_primary"]} {theme["text_primary"]} p-8'):
        # Header
        with ui.row().classes('items-center justify-between w-full mb-8'):
            with ui.row().classes('items-center gap-4'):
                ui.button(
                    '←',
                    on_click=lambda: ui.navigate.to('/')
                ).classes(f'{theme["button_secondary"]} rounded-full w-12 h-12 text-xl').style('color: #1f2937 !important;')
                ui.html(f'<h1 class="text-3xl font-bold {theme["gradient_text"]}">🍳 Your Recipe History</h1>')
            
            # User info
            with ui.column().classes('text-right'):
                ui.html(f'<span class="text-lg {theme["text_secondary"]}">{current_user["name"]}\'s Kitchen</span>')
        
        # Load recipe history
        try:
            db = next(get_db())
            from ..database.operations import get_user_recipe_history
            recipe_history = get_user_recipe_history(db, current_user['id'], 30)
            
            if recipe_history:
                ui.html(f'<p class="text-lg {theme["text_secondary"]} mb-6">Your last {len(recipe_history)} unique recipes. We track these to ensure you never get repetitive meal plans!</p>')
                
                with ui.column().classes('gap-4 w-full'):
                    for i, recipe in enumerate(recipe_history):
                        with ui.card().classes(f'{theme["card"]} {theme["border"]} rounded-2xl p-6'):
                            with ui.row().classes('items-start justify-between gap-6'):
                                with ui.column().classes('flex-1'):
                                    with ui.row().classes('items-center gap-3 mb-3'):
                                        ui.html(f'<span class="{theme["chip_bg"]} {theme["border"]} rounded-full px-3 py-1 text-sm font-bold">#{len(recipe_history) - i}</span>')
                                        ui.html(f'<h3 class="text-xl font-bold {theme["text_primary"]}">{recipe.recipe_name}</h3>')
                                    
                                    ui.html(f'<p class="text-sm {theme["text_secondary"]} mb-3">{recipe.created_at.strftime("%B %d, %Y at %I:%M %p")}</p>')
                                    
                                    # Show recipe diversity elements
                                    with ui.row().classes('gap-2 mb-3 flex-wrap'):
                                        # Cooking method
                                        cooking_method = recipe.cooking_method.split()[0] if recipe.cooking_method else "Unknown"
                                        ui.html(f'<span class="bg-blue-100 text-blue-800 rounded-full px-3 py-1 text-sm">🔥 {cooking_method.title()}</span>')
                                        
                                        # Spice profile
                                        spice_profile = recipe.spice_profile.split()[0] if recipe.spice_profile else "Unknown"
                                        ui.html(f'<span class="bg-green-100 text-green-800 rounded-full px-3 py-1 text-sm">🌶️ {spice_profile.title()}</span>')
                                        
                                        # Cuisine inspiration
                                        cuisine = recipe.cuisine_inspiration.split()[0] if recipe.cuisine_inspiration else "Unknown"
                                        ui.html(f'<span class="bg-purple-100 text-purple-800 rounded-full px-3 py-1 text-sm">🌍 {cuisine.title()}</span>')
                                    
                                    # Main ingredients
                                    if recipe.main_ingredients:
                                        ingredients_preview = recipe.main_ingredients[:60] + '...' if len(recipe.main_ingredients) > 60 else recipe.main_ingredients
                                        ui.html(f'<span class="{theme["text_secondary"]} text-sm">🥘 Key ingredients: {ingredients_preview}</span>')
            else:
                # No recipe history yet
                with ui.card().classes(f'{theme["card"]} {theme["border"]} rounded-3xl p-8 text-center'):
                    ui.html('<div class="text-6xl mb-6">📖</div>')
                    ui.html(f'<h2 class="text-2xl font-bold {theme["text_primary"]} mb-4">No Recipe History Yet</h2>')
                    ui.html(f'<p class="text-lg {theme["text_secondary"]} mb-6">Start creating meal plans to build your recipe history! We\'ll track your recipes to ensure maximum variety.</p>')
                    ui.button(
                        '✨ Create First Meal Plan',
                        on_click=lambda: ui.navigate.to('/')
                    ).classes(f'{theme["button_primary"]} text-white font-semibold py-3 px-6 rounded-xl')
        
        except Exception as e:
            ui.notify(f'Error loading recipe history: {str(e)}', type='negative')
            with ui.card().classes(f'{theme["error_bg"]} {theme["border"]} rounded-3xl p-6 text-center'):
                ui.html('<div class="text-4xl mb-4">❌</div>')
                ui.html(f'<h2 class="text-xl font-bold {theme["text_primary"]} mb-4">Error Loading History</h2>')
                ui.html(f'<p class="text-sm {theme["text_secondary"]}">{str(e)}</p>')

@ui.page('/meal-plan/{meal_plan_id}')
def meal_plan_detail_page(meal_plan_id: int):
    # Check if user is logged in
    current_user = get_current_user()
    if current_user is None:
        ui.navigate.to('/login')
        return
    
    theme = get_theme_classes()
    
    # Add viewport and Material Icons
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    ui.add_head_html('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">')
    
    try:
        # Load meal plan from database
        db = next(get_db())
        meal_plan = db.query(MealPlan).filter(
            MealPlan.id == meal_plan_id, 
            MealPlan.user_id == current_user['id']
        ).first()
        
        if not meal_plan:
            ui.notify('Meal plan not found', type='negative')
            ui.navigate.to('/history')
            return
        
        # Parse JSON data
        try:
            recipes = json.loads(meal_plan.recipes_json)
            shopping_list = json.loads(meal_plan.shopping_list_json)
            recipe_ratings = get_meal_plan_recipe_ratings(db, current_user['id'], meal_plan_id)
            ratings_dict = {r.recipe_index: r for r in recipe_ratings}
        except json.JSONDecodeError:
            ui.notify('Error loading meal plan data', type='negative')
            ui.navigate.to('/history')
            return
        
        # Display meal plan details
        from .meal_plan_display import display_meal_plan_details
        display_meal_plan_details(meal_plan, recipes, shopping_list, ratings_dict, theme, current_user, meal_plan_id)
        
    except Exception as e:
        ui.notify(f'Error loading meal plan: {str(e)}', type='negative')
        ui.navigate.to('/history')