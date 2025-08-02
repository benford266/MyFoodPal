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
from ..config import LM_STUDIO_BASE_URL, LM_STUDIO_MODEL

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
            ui.html(f'<h1 class="text-2xl sm:text-3xl font-bold {theme["gradient_text"]} text-center mb-4">Welcome to MyFoodPal</h1>')
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
                                ui.notify(f'Welcome to MyFoodPal, {user.name}!', type='positive')
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
    
    # Add viewport
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    
    # Create recipe generator
    recipe_generator = RecipeGenerator(LM_STUDIO_BASE_URL, LM_STUDIO_MODEL)
    
    # Load current preferences from user
    db = next(get_db())
    current_user_data = db.query(User).filter(User.id == current_user['id']).first()
    
    # Clean, simple layout
    with ui.column().classes('min-h-screen').style('background: #f8fafc;'):
        
        # Simple header
        with ui.row().classes('w-full bg-white shadow-sm px-6 py-4 items-center justify-between'):
            ui.label('MyFoodPal').classes('text-2xl font-bold text-gray-800')
            with ui.row().classes('gap-3'):
                ui.button('Meal Plans', on_click=lambda: ui.navigate.to('/history')).props('flat').classes('text-gray-600')
                ui.button('History', on_click=lambda: ui.navigate.to('/recipe-history')).props('flat').classes('text-gray-600')
                ui.button('Logout', on_click=lambda: [clear_current_user(), ui.navigate.to('/login')]).props('flat color=negative')
        
        # Main content
        with ui.row().classes('flex-1 p-6 gap-6 max-w-6xl mx-auto w-full'):
            
            # Left panel - preferences
            with ui.card().classes('p-6').style('width: 400px; height: fit-content;'):
                ui.label('Your Preferences').classes('text-lg font-semibold mb-4')
                
                liked_foods_input = ui.textarea(
                    label='Foods You Love',
                    placeholder='e.g., chicken, pasta, vegetables...',
                    value=current_user_data.liked_foods if current_user_data else ""
                ).classes('w-full mb-4').props('rows=3')
                
                disliked_foods_input = ui.textarea(
                    label='Foods You Avoid', 
                    placeholder='e.g., mushrooms, seafood...',
                    value=current_user_data.disliked_foods if current_user_data else ""
                ).classes('w-full mb-4').props('rows=3')
                
                must_use_input = ui.textarea(
                    label='Must Use (Expiring Soon)',
                    placeholder='e.g., leftover chicken, spinach...',
                    value=current_user_data.must_use_ingredients if hasattr(current_user_data, 'must_use_ingredients') and current_user_data.must_use_ingredients else ""
                ).classes('w-full mb-4').props('rows=2')
                
                with ui.row().classes('gap-4 w-full'):
                    recipe_count_input = ui.number(label='Number of Recipes', value=5, min=1, max=10).classes('flex-1')
                    serving_size_input = ui.number(label='Serving Size', value=4, min=1, max=12).classes('flex-1')
            
            # Right panel - results
            with ui.column().classes('flex-1'):
                results_container = ui.column().classes('w-full')
                
                with results_container:
                    with ui.card().classes('p-8 text-center'):
                        ui.icon('restaurant', size='4rem').classes('text-blue-500 mb-4')
                        ui.label('Ready to Generate Recipes?').classes('text-2xl font-bold mb-4')
                        ui.label('Tell us your preferences and we\'ll create personalized recipes with a shopping list.').classes('text-gray-600 mb-8')
                        
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
                            
                            # Show progress
                            results_container.clear()
                            with results_container:
                                with ui.card().classes('p-8 text-center'):
                                    ui.spinner(size='lg').classes('mb-4')
                                    ui.label('Generating Your Recipes & Images...').classes('text-xl font-bold mb-4')
                                    progress_label = ui.label('Getting started...').classes('text-gray-600 mb-2')
                                    
                                    # Show breakdown of what we're doing
                                    recipe_count = int(recipe_count_input.value)
                                    ui.label(f'Creating {recipe_count} recipes + {recipe_count} images = {recipe_count * 2} total steps').classes('text-sm text-gray-500 mb-4')
                                    
                                    progress_bar = ui.linear_progress(value=0).classes('w-full mb-2')
                                    progress_percentage = ui.label('0%').classes('text-sm text-gray-500')
                            
                            # Generate recipes
                            try:
                                liked_foods = [f.strip() for f in liked_foods_input.value.split(',') if f.strip()]
                                disliked_foods = [f.strip() for f in disliked_foods_input.value.split(',') if f.strip()]
                                must_use_ingredients = [f.strip() for f in must_use_input.value.split(',') if f.strip()]
                                
                                # Enhanced progress tracking for both recipes and images
                                total_steps = int(recipe_count_input.value) * 2  # recipes + images
                                current_step = 0
                                
                                async def progress_callback(message: str):
                                    nonlocal current_step
                                    progress_label.text = message
                                    
                                    # Helper function to update progress
                                    def update_progress(step):
                                        nonlocal current_step
                                        current_step = step
                                        progress_value = current_step / total_steps
                                        progress_bar.value = progress_value
                                        progress_percentage.text = f'{int(progress_value * 100)}%'
                                    
                                    # Track recipe generation progress
                                    if "Generating recipe" in message and "/" in message:
                                        try:
                                            parts = message.split('/')
                                            if len(parts) >= 2:
                                                recipe_num = int(parts[0].split()[-1])
                                                total_recipes = int(parts[1].split()[0])
                                                # Recipe generation is first half of progress
                                                update_progress(recipe_num)
                                                print(f"📊 Recipe progress: {recipe_num}/{total_recipes} (step {current_step}/{total_steps})")
                                        except Exception as e:
                                            print(f"Error parsing recipe progress: {e}")
                                    
                                    # Track image generation progress
                                    elif "Generating image" in message and "/" in message:
                                        try:
                                            parts = message.split('/')
                                            if len(parts) >= 2:
                                                # Extract numbers from "Generating image X/Y: Recipe Name"
                                                image_num = int(parts[0].split()[-1])
                                                total_images = int(parts[1].split(':')[0])
                                                # Image generation is second half of progress
                                                update_progress(int(recipe_count_input.value) + image_num)
                                                print(f"📊 Image progress: {image_num}/{total_images} (step {current_step}/{total_steps})")
                                        except Exception as e:
                                            print(f"Error parsing image progress: {e}")
                                    
                                    # Handle general progress messages
                                    elif "Generating recipes..." in message:
                                        update_progress(0.5)  # Small initial progress
                                    elif "Generating recipe images..." in message:
                                        update_progress(int(recipe_count_input.value))
                                        print(f"📊 Starting image generation (step {current_step}/{total_steps})")
                                
                                db = next(get_db())
                                
                                recipes = await recipe_generator.generate_recipes_with_images(
                                    liked_foods, disliked_foods, 
                                    int(recipe_count_input.value), 
                                    int(serving_size_input.value),
                                    progress_callback,
                                    current_user['id'],
                                    db,
                                    must_use_ingredients,
                                    generate_images=True,
                                    comfyui_server="192.168.4.208:8188"
                                )
                                
                                # Final progress update
                                progress_bar.value = 1.0
                                progress_percentage.text = "100%"
                                progress_label.text = "Generating shopping list..."
                                
                                shopping_list = generate_shopping_list(recipes)
                                
                                # Save meal plan
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
                                except Exception as e:
                                    print(f"Error saving meal plan: {e}")
                                
                                # Display results
                                from .recipe_display import display_recipes_and_shopping_list
                                display_recipes_and_shopping_list(results_container, recipes, shopping_list, theme, current_user, saved_meal_plan.id if 'saved_meal_plan' in locals() else None)
                                
                            except Exception as e:
                                results_container.clear()
                                with results_container:
                                    with ui.card().classes('p-6 text-center border-red-200').style('border-color: #fecaca;'):
                                        ui.icon('error', size='3rem').classes('text-red-500 mb-4')
                                        ui.label('Generation Failed').classes('text-lg font-bold text-red-700 mb-2')
                                        ui.label(str(e)).classes('text-red-600')
                        
                        ui.button('Generate Recipes', on_click=generate_recipes_handler).props('color=primary size=lg').classes('px-8')

@ui.page('/history')
def history_page():
    # Check if user is logged in
    current_user = get_current_user()
    if current_user is None:
        ui.navigate.to('/login')
        return
    
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    
    with ui.column().classes('min-h-screen').style('background: #f8fafc;'):
        # Simple header
        with ui.row().classes('w-full bg-white shadow-sm px-6 py-4 items-center justify-between'):
            with ui.row().classes('items-center gap-4'):
                ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/')).props('flat round')
                ui.label('My Meal Plans').classes('text-2xl font-bold text-gray-800')
            ui.label(f'{current_user["name"]}\'s Kitchen').classes('text-gray-600')
        
        # Content
        with ui.column().classes('flex-1 p-6 max-w-4xl mx-auto w-full'):
            try:
                db = next(get_db())
                meal_plans = get_user_meal_plans(db, current_user['id'], limit=20)
                
                if meal_plans:
                    ui.label(f'You have {len(meal_plans)} meal plans').classes('text-lg text-gray-600 mb-6')
                    
                    for meal_plan in meal_plans:
                        with ui.card().classes('p-6 mb-4 cursor-pointer hover:shadow-md').on('click', lambda e, plan_id=meal_plan.id: ui.navigate.to(f'/meal-plan/{plan_id}')):
                            with ui.row().classes('items-start justify-between w-full'):
                                with ui.column().classes('flex-1'):
                                    ui.label(meal_plan.name).classes('text-xl font-bold mb-2')
                                    ui.label(meal_plan.created_at.strftime("%B %d, %Y at %I:%M %p")).classes('text-gray-500 mb-4')
                                    
                                    with ui.row().classes('gap-4'):
                                        ui.chip(f'{meal_plan.recipe_count} recipes', color='primary')
                                        ui.chip(f'{meal_plan.serving_size} servings', color='secondary')
                                    
                                    if meal_plan.liked_foods_snapshot or meal_plan.disliked_foods_snapshot:
                                        with ui.column().classes('mt-4 gap-2'):
                                            if meal_plan.liked_foods_snapshot:
                                                ui.label(f'💚 Liked: {meal_plan.liked_foods_snapshot[:50]}...').classes('text-green-600 text-sm')
                                            if meal_plan.disliked_foods_snapshot:
                                                ui.label(f'🚫 Avoided: {meal_plan.disliked_foods_snapshot[:50]}...').classes('text-red-600 text-sm')
                else:
                    # No meal plans yet
                    with ui.card().classes('p-12 text-center'):
                        ui.icon('note_add', size='4rem').classes('text-gray-400 mb-4')
                        ui.label('No Meal Plans Yet').classes('text-2xl font-bold text-gray-800 mb-4')
                        ui.label('Start creating personalized recipes to see them here!').classes('text-gray-600 mb-6')
                        ui.button('Create First Meal Plan', on_click=lambda: ui.navigate.to('/')).props('color=primary size=lg')
            
            except Exception as e:
                ui.notify(f'Error loading meal plans: {str(e)}', type='negative')
                with ui.card().classes('p-6 text-center'):
                    ui.icon('error', size='3rem').classes('text-red-500 mb-4')
                    ui.label('Error Loading Meal Plans').classes('text-lg font-bold text-red-700 mb-2')
                    ui.label(str(e)).classes('text-red-600')

@ui.page('/recipe-history')
def recipe_history_page():
    # Check if user is logged in
    current_user = get_current_user()
    if current_user is None:
        ui.navigate.to('/login')
        return
    
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    
    with ui.column().classes('min-h-screen').style('background: #f8fafc;'):
        # Simple header
        with ui.row().classes('w-full bg-white shadow-sm px-6 py-4 items-center justify-between'):
            with ui.row().classes('items-center gap-4'):
                ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/')).props('flat round')
                ui.label('Recipe History').classes('text-2xl font-bold text-gray-800')
            ui.label(f'{current_user["name"]}\'s Kitchen').classes('text-gray-600')
        
        # Content
        with ui.column().classes('flex-1 p-6 max-w-4xl mx-auto w-full'):
            try:
                db = next(get_db())
                from ..database.operations import get_user_recipe_history
                recipe_history = get_user_recipe_history(db, current_user['id'], 30)
                
                if recipe_history:
                    ui.label(f'Your last {len(recipe_history)} unique recipes. We track these to ensure variety in your meal plans!').classes('text-lg text-gray-600 mb-6')
                    
                    for i, recipe in enumerate(recipe_history):
                        with ui.card().classes('p-6 mb-4'):
                            with ui.row().classes('items-start gap-4 w-full'):
                                ui.chip(f'#{len(recipe_history) - i}', color='primary')
                                with ui.column().classes('flex-1'):
                                    ui.label(recipe.recipe_name).classes('text-xl font-bold mb-2')
                                    ui.label(recipe.created_at.strftime("%B %d, %Y at %I:%M %p")).classes('text-gray-500 mb-4')
                                    
                                    # Recipe characteristics
                                    with ui.row().classes('gap-2 mb-4 flex-wrap'):
                                        if recipe.cooking_method:
                                            cooking_method = recipe.cooking_method.split()[0] if recipe.cooking_method else "Unknown"
                                            ui.chip(f'🔥 {cooking_method.title()}', color='blue')
                                        if recipe.spice_profile:
                                            spice_profile = recipe.spice_profile.split()[0] if recipe.spice_profile else "Unknown"
                                            ui.chip(f'🌶️ {spice_profile.title()}', color='green')
                                        if recipe.cuisine_inspiration:
                                            cuisine = recipe.cuisine_inspiration.split()[0] if recipe.cuisine_inspiration else "Unknown"
                                            ui.chip(f'🌍 {cuisine.title()}', color='purple')
                                    
                                    # Main ingredients
                                    if recipe.main_ingredients:
                                        ingredients_preview = recipe.main_ingredients[:60] + '...' if len(recipe.main_ingredients) > 60 else recipe.main_ingredients
                                        ui.label(f'🥘 Key ingredients: {ingredients_preview}').classes('text-gray-600 text-sm')
                else:
                    # No recipe history yet
                    with ui.card().classes('p-12 text-center'):
                        ui.icon('menu_book', size='4rem').classes('text-gray-400 mb-4')
                        ui.label('No Recipe History Yet').classes('text-2xl font-bold text-gray-800 mb-4')
                        ui.label('Start creating meal plans to build your recipe history! We\'ll track your recipes to ensure maximum variety.').classes('text-gray-600 mb-6')
                        ui.button('Create First Meal Plan', on_click=lambda: ui.navigate.to('/')).props('color=primary size=lg')
            
            except Exception as e:
                ui.notify(f'Error loading recipe history: {str(e)}', type='negative')
                with ui.card().classes('p-6 text-center'):
                    ui.icon('error', size='3rem').classes('text-red-500 mb-4')
                    ui.label('Error Loading Recipe History').classes('text-lg font-bold text-red-700 mb-2')
                    ui.label(str(e)).classes('text-red-600')

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