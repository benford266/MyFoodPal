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
from ..utils.theme import get_theme_classes, get_theme_manager
from .navigation import ModernNavigation, create_floating_action_button, create_bottom_navigation
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
    
    # Modern layout with theme support
    theme_manager = get_theme_manager()
    theme_manager.apply_theme()  # Apply theme CSS
    
    with ui.column().classes(f'min-h-screen {theme["bg_primary"]}'):
        
        # Modern navigation header
        navigation = ModernNavigation(current_user, theme)
        navigation.create_header("home")
        
        # Main content with modern layout
        with ui.row().classes('flex-1 p-8 gap-8 max-w-7xl mx-auto w-full'):
            
            # Left panel - Smart preferences with modern design
            with ui.card().classes(f'{theme["card_elevated"]} rounded-2xl p-8 border {theme["border"]}').style('width: 420px; height: fit-content;'):
                # Header with icon
                with ui.row().classes('items-center gap-3 mb-6'):
                    ui.html(f'''
                        <div class="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center text-2xl text-white">
                            🎯
                        </div>
                    ''')
                    ui.html(f'<h2 class="text-xl font-bold {theme["gradient_text"]}">Your Preferences</h2>')
                
                # Enhanced form inputs with modern styling
                liked_foods_input = ui.textarea(
                    label='Foods You Love',
                    placeholder='e.g., chicken, pasta, vegetables, fresh herbs...',
                    value=current_user_data.liked_foods if current_user_data else ""
                ).classes(f'{theme["textarea_bg"]} w-full mb-6 rounded-xl border-2 p-4').props('rows=3')
                
                disliked_foods_input = ui.textarea(
                    label='Foods You Avoid', 
                    placeholder='e.g., mushrooms, seafood, dairy...',
                    value=current_user_data.disliked_foods if current_user_data else ""
                ).classes(f'{theme["textarea_bg"]} w-full mb-6 rounded-xl border-2 p-4').props('rows=3')
                
                must_use_input = ui.textarea(
                    label='Must Use (Expiring Soon)',
                    placeholder='e.g., leftover chicken, spinach, tomatoes...',
                    value=current_user_data.must_use_ingredients if hasattr(current_user_data, 'must_use_ingredients') and current_user_data.must_use_ingredients else ""
                ).classes(f'{theme["textarea_bg"]} w-full mb-6 rounded-xl border-2 p-4').props('rows=2')
                
                # Recipe configuration with modern inputs
                with ui.row().classes('gap-4 w-full mb-6'):
                    with ui.column().classes('flex-1'):
                        ui.html(f'<label class="text-sm font-medium {theme["text_secondary"]} mb-2 block">Number of Recipes</label>')
                        recipe_count_input = ui.number(value=5, min=1, max=10).classes(f'{theme["input_bg"]} w-full rounded-xl border-2 p-3')
                    
                    with ui.column().classes('flex-1'):
                        ui.html(f'<label class="text-sm font-medium {theme["text_secondary"]} mb-2 block">Serving Size</label>')
                        serving_size_input = ui.number(value=4, min=1, max=12).classes(f'{theme["input_bg"]} w-full rounded-xl border-2 p-3')
                
                # Generation mode with enhanced styling
                with ui.card().classes(f'{theme["bg_surface"]} rounded-xl p-6 border {theme["border"]}'):
                    with ui.row().classes('items-center gap-3 mb-3'):
                        ui.html('<span class="text-2xl">⚡</span>')
                        ui.html(f'<span class="text-lg font-semibold {theme["text_primary"]}">Generation Mode</span>')
                    
                    background_mode = ui.switch('Generate in Background', value=False).classes('mb-2')
                    ui.html(f'<p class="text-sm {theme["text_muted"]}">Background mode lets you navigate away while recipes generate. Perfect for multitasking!</p>')
            
            # Right panel - Smart results area
            with ui.column().classes('flex-1'):
                results_container = ui.column().classes('w-full')
                
                with results_container:
                    with ui.card().classes(f'{theme["card_elevated"]} rounded-2xl p-12 text-center border {theme["border"]}'):
                        # Hero section
                        ui.html(f'''
                            <div class="w-24 h-24 bg-gradient-to-br from-emerald-100 to-teal-100 rounded-full flex items-center justify-center text-5xl mb-6 mx-auto">
                                🍽️
                            </div>
                        ''')
                        ui.html(f'<h2 class="text-3xl font-bold {theme["gradient_text"]} mb-4">Ready to Create Magic?</h2>')
                        ui.html(f'<p class="text-lg {theme["text_secondary"]} max-w-2xl mx-auto mb-8">Tell us your preferences and we\'ll craft personalized recipes with AI-powered ingredient optimization and a smart shopping list.</p>')
                        
                        # Feature highlights
                        with ui.row().classes('gap-6 justify-center mb-8 flex-wrap'):
                            features = [
                                {"icon": "🎯", "text": "Personalized"},
                                {"icon": "🛒", "text": "Smart Shopping"},
                                {"icon": "⚡", "text": "Lightning Fast"},
                                {"icon": "🖼️", "text": "Visual Recipes"}
                            ]
                            
                            for feature in features:
                                with ui.column().classes('items-center'):
                                    ui.html(f'<span class="text-2xl mb-2">{feature["icon"]}</span>')
                                    ui.html(f'<span class="text-sm {theme["text_muted"]} font-medium">{feature["text"]}</span>')
                        
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
                            
                            # Check for immediate vs background generation
                            if not background_mode.value:
                                # Immediate generation (existing behavior)
                                await _generate_immediately()
                            else:
                                # Background generation (new behavior)
                                await _generate_in_background()
                        
                        async def _generate_immediately():
                            """Generate recipes immediately with live progress"""
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
                        
                        async def _generate_in_background():
                            """Start background generation and show status"""
                            try:
                                # Import background task service
                                from ..database.operations import create_generation_task
                                from ..services.background_tasks import start_background_generation
                                
                                # Create generation task record
                                db = next(get_db())
                                task = create_generation_task(
                                    db=db,
                                    user_id=current_user['id'],
                                    recipe_count=int(recipe_count_input.value),
                                    serving_size=int(serving_size_input.value),
                                    liked_foods=liked_foods_input.value,
                                    disliked_foods=disliked_foods_input.value,
                                    must_use_ingredients=must_use_input.value
                                )
                                
                                # Start background task
                                await start_background_generation(task.id)
                                
                                # Show background generation status
                                results_container.clear()
                                with results_container:
                                    with ui.card().classes('p-8 text-center bg-blue-50'):
                                        ui.icon('schedule', size='3rem').classes('text-blue-500 mb-4')
                                        ui.label('Generation Started in Background!').classes('text-xl font-bold text-blue-800 mb-4')
                                        ui.label(f'Your {int(recipe_count_input.value)} recipes are being generated in the background.').classes('text-blue-600 mb-4')
                                        ui.label('You can navigate to other pages and we\'ll notify you when complete.').classes('text-blue-600 mb-6')
                                        
                                        with ui.row().classes('gap-4'):
                                            ui.button('View Meal Plans', on_click=lambda: ui.navigate.to('/history')).props('color=primary')
                                            ui.button('Check Status', on_click=lambda: _check_task_status(task.id)).props('color=secondary')
                                
                                ui.notify(f'Recipe generation started in background (Task #{task.id})', type='positive')
                                
                            except Exception as e:
                                ui.notify(f'Failed to start background generation: {str(e)}', type='negative')
                        
                        def _check_task_status(task_id: int):
                            """Check and display task status"""
                            try:
                                from ..database.operations import get_generation_task
                                db = next(get_db())
                                task = get_generation_task(db, task_id)
                                
                                if task:
                                    status_msg = f"Task #{task_id}: {task.status.value} ({task.progress}%)"
                                    if task.current_step:
                                        status_msg += f" - {task.current_step}"
                                    ui.notify(status_msg, type='info')
                                    
                                    if task.status.value == 'completed' and task.meal_plan_id:
                                        ui.notify('Generation complete! Check your meal plans.', type='positive')
                                        ui.navigate.to('/history')
                                else:
                                    ui.notify(f'Task #{task_id} not found', type='warning')
                            except Exception as e:
                                ui.notify(f'Error checking task status: {str(e)}', type='negative')
                        
                        # Modern generate button
                        with ui.button(on_click=generate_recipes_handler).classes(f'{theme["button_primary"]} font-bold py-4 px-12 rounded-xl text-lg shadow-lg transition-all duration-300 hover:scale-105'):
                            with ui.row().classes('items-center gap-3'):
                                ui.html('<span class="text-2xl">✨</span>')
                                ui.html('<span>Generate Recipes</span>')
        
        # Add floating action button for quick access
        create_floating_action_button(theme, generate_recipes_handler)
        
        # Add bottom navigation for mobile
        create_bottom_navigation("home", theme)

@ui.page('/kitchen')
def kitchen_page():
    # Check if user is logged in
    current_user = get_current_user()
    if current_user is None:
        ui.navigate.to('/login')
        return
    
    theme = get_theme_classes()
    theme_manager = get_theme_manager()
    theme_manager.apply_theme()
    
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    
    from .search import ModernSearchBar, AdvancedFilterPanel, QuickFilters
    from .components import create_loading_recipe_card
    
    with ui.column().classes(f'min-h-screen {theme["bg_primary"]}'):
        # Modern navigation header
        navigation = ModernNavigation(current_user, theme)
        navigation.create_header("kitchen")
        
        # Kitchen Dashboard Content
        with ui.column().classes('flex-1 p-8 max-w-7xl mx-auto w-full'):
            # Page header
            with ui.row().classes('items-center justify-between mb-8'):
                with ui.column():
                    ui.html(f'<h1 class="text-4xl font-bold {theme["gradient_text"]} mb-2">🍳 My Kitchen</h1>')
                    ui.html(f'<p class="text-lg {theme["text_secondary"]}">{current_user["name"]}\'s culinary command center</p>')
            
            # Search and filters section
            with ui.card().classes(f'{theme["card_elevated"]} rounded-2xl p-8 mb-8 border {theme["border"]}'):
                ui.html(f'<h2 class="text-2xl font-bold {theme["text_primary"]} mb-6 flex items-center gap-3"><span class="text-2xl">🔍</span> Recipe Discovery</h2>')
                
                # Search functionality
                def handle_search(search_term: str):
                    ui.notify(f'Searching for: {search_term}' if search_term else 'Search cleared', type='info')
                
                def handle_filter_change(filters: Dict):
                    active_filters = sum(len(v) if isinstance(v, list) else (1 if v else 0) for v in filters.values())
                    ui.notify(f'Applied {active_filters} filter{"s" if active_filters != 1 else ""}', type='info')
                
                def handle_quick_filter(filter_type: str):
                    ui.notify(f'Applied quick filter: {filter_type}', type='info')
                
                # Create search components
                search_bar = ModernSearchBar(theme, handle_search)
                search_bar.create_search_bar()
                
                # Quick filters
                ui.html(f'<h3 class="text-lg font-semibold {theme["text_primary"]} mt-6 mb-4">Quick Filters</h3>')
                quick_filters = QuickFilters(theme, handle_quick_filter)
                quick_filters.create_quick_filters()
                
                # Advanced filters (collapsible)
                advanced_expanded = {"value": False}
                
                def toggle_advanced():
                    advanced_expanded["value"] = not advanced_expanded["value"]
                    advanced_container.clear()
                    
                    if advanced_expanded["value"]:
                        with advanced_container:
                            ui.html('<div class="slide-down">')
                            filter_panel = AdvancedFilterPanel(theme, handle_filter_change)
                            filter_panel.create_filter_panel()
                            ui.html('</div>')
                        toggle_btn.text = "Hide Advanced Filters ▲"
                    else:
                        toggle_btn.text = "Show Advanced Filters ▼"
                
                with ui.row().classes('items-center justify-between mt-6'):
                    toggle_btn = ui.button(
                        "Show Advanced Filters ▼",
                        on_click=toggle_advanced
                    ).classes(f'{theme["button_ghost"]} text-sm py-2 px-4 rounded-lg')
                
                advanced_container = ui.column().classes('w-full mt-4')
            
            # Kitchen inventory section
            with ui.row().classes('gap-8 w-full'):
                # Left column - Inventory
                with ui.column().classes('flex-1'):
                    _create_inventory_section(theme, current_user)
                
                # Right column - Quick recipes and suggestions
                with ui.column().classes('flex-1'):
                    _create_recipe_suggestions_section(theme, current_user)
        
        # Add bottom navigation for mobile
        create_bottom_navigation("kitchen", theme)

def _create_inventory_section(theme: Dict[str, str], current_user: Dict):
    """Create the kitchen inventory management section"""
    with ui.card().classes(f'{theme["card_elevated"]} rounded-2xl p-8 border {theme["border"]} h-fit'):
        # Header
        with ui.row().classes('items-center justify-between mb-6'):
            ui.html(f'<h2 class="text-2xl font-bold {theme["gradient_text"]} flex items-center gap-3"><span class="text-2xl">📦</span> Kitchen Inventory</h2>')
            ui.button(
                '+ Add Item',
                on_click=lambda: ui.notify('Add item feature coming soon!', type='info')
            ).classes(f'{theme["button_primary"]} px-4 py-2 rounded-xl text-sm')
        
        # Quick stats
        with ui.row().classes('gap-4 mb-6'):
            stats = [
                {"label": "Items", "value": "24", "color": "emerald"},
                {"label": "Expiring Soon", "value": "3", "color": "amber"},
                {"label": "Out of Stock", "value": "1", "color": "red"}
            ]
            
            for stat in stats:
                with ui.card().classes(f'{theme["bg_surface"]} p-4 rounded-xl border {theme["border"]} flex-1 text-center'):
                    ui.html(f'<div class="text-2xl font-bold text-{stat["color"]}-600 mb-1">{stat["value"]}</div>')
                    ui.html(f'<div class="text-sm {theme["text_muted"]}">{stat["label"]}</div>')
        
        # Sample inventory items
        inventory_items = [
            {"name": "Chicken Breast", "quantity": "2 lbs", "expires": "3 days", "status": "good"},
            {"name": "Fresh Spinach", "quantity": "1 bag", "expires": "2 days", "status": "expiring"},
            {"name": "Milk", "quantity": "1 gallon", "expires": "5 days", "status": "good"},
            {"name": "Tomatoes", "quantity": "6 pieces", "expires": "1 day", "status": "expiring"},
            {"name": "Rice", "quantity": "2 cups", "expires": "Never", "status": "good"},
        ]
        
        ui.html(f'<h3 class="text-lg font-semibold {theme["text_primary"]} mb-4">Current Items</h3>')
        
        with ui.column().classes('gap-3'):
            for item in inventory_items:
                status_colors = {
                    "good": "bg-green-100 text-green-700",
                    "expiring": "bg-amber-100 text-amber-700", 
                    "expired": "bg-red-100 text-red-700"
                }
                
                with ui.row().classes(f'{theme["bg_surface"]} rounded-xl p-4 items-center justify-between border {theme["border"]} hover:shadow-md transition-shadow'):
                    with ui.column().classes('flex-1'):
                        ui.html(f'<div class="font-semibold {theme["text_primary"]}">{item["name"]}</div>')
                        ui.html(f'<div class="text-sm {theme["text_muted"]}">{item["quantity"]} • Expires in {item["expires"]}</div>')
                    
                    with ui.row().classes('items-center gap-3'):
                        # Status badge
                        status_class = status_colors.get(item["status"], "bg-gray-100 text-gray-700")
                        ui.html(f'<span class="{status_class} px-3 py-1 rounded-full text-xs font-medium">{item["status"].title()}</span>')
                        
                        # Action button
                        ui.button(
                            '🍽️',
                            on_click=lambda name=item["name"]: ui.notify(f'Finding recipes with {name}...', type='info')
                        ).classes(f'{theme["button_ghost"]} w-8 h-8 rounded-lg text-lg').tooltip(f'Find recipes with {item["name"]}')

def _create_recipe_suggestions_section(theme: Dict[str, str], current_user: Dict):
    """Create recipe suggestions based on available ingredients"""
    with ui.card().classes(f'{theme["card_elevated"]} rounded-2xl p-8 border {theme["border"]} h-fit'):
        # Header
        ui.html(f'<h2 class="text-2xl font-bold {theme["gradient_text"]} mb-6 flex items-center gap-3"><span class="text-2xl">✨</span> Smart Suggestions</h2>')
        
        # Cook Now section
        ui.html(f'<h3 class="text-lg font-semibold {theme["text_primary"]} mb-4 flex items-center gap-2"><span class="text-lg">🔥</span> Cook Now (Using Available Items)</h3>')
        
        suggested_recipes = [
            {"name": "Chicken Spinach Stir-fry", "time": "25 min", "match": "95%", "ingredients": ["Chicken Breast", "Fresh Spinach"]},
            {"name": "Creamy Chicken Rice", "time": "30 min", "match": "90%", "ingredients": ["Chicken Breast", "Rice", "Milk"]},
            {"name": "Fresh Garden Salad", "time": "10 min", "match": "85%", "ingredients": ["Fresh Spinach", "Tomatoes"]},
        ]
        
        with ui.column().classes('gap-4 mb-8'):
            for recipe in suggested_recipes:
                with ui.card().classes(f'{theme["card_interactive"]} p-6 rounded-xl border {theme["border"]}'):
                    with ui.row().classes('items-start justify-between'):
                        with ui.column().classes('flex-1'):
                            ui.html(f'<h4 class="font-bold {theme["text_primary"]} mb-2">{recipe["name"]}</h4>')
                            ui.html(f'<p class="text-sm {theme["text_muted"]} mb-3">⏱️ {recipe["time"]} • 🎯 {recipe["match"]} match</p>')
                            
                            # Ingredient tags
                            with ui.row().classes('gap-2 flex-wrap'):
                                for ingredient in recipe["ingredients"]:
                                    ui.html(f'<span class="{theme["badge_bg"]} px-3 py-1 rounded-full text-xs font-medium border {theme["border"]}">{ingredient}</span>')
                        
                        # Action buttons
                        with ui.column().classes('gap-2'):
                            ui.button(
                                '👁️',
                                on_click=lambda r=recipe["name"]: ui.notify(f'Viewing {r}...', type='info')
                            ).classes(f'{theme["button_ghost"]} w-10 h-10 rounded-lg').tooltip('View Recipe')
                            
                            ui.button(
                                '🍳',
                                on_click=lambda r=recipe["name"]: ui.notify(f'Starting to cook {r}!', type='positive')
                            ).classes(f'{theme["button_primary"]} w-10 h-10 rounded-lg text-white').tooltip('Start Cooking')
        
        # Meal planning section
        ui.html(f'<h3 class="text-lg font-semibold {theme["text_primary"]} mb-4 flex items-center gap-2"><span class="text-lg">📅</span> This Week\'s Plan</h3>')
        
        with ui.row().classes('gap-4'):
            ui.button(
                'Plan This Week',
                on_click=lambda: ui.notify('Weekly meal planning coming soon!', type='info')
            ).classes(f'{theme["button_secondary"]} px-6 py-3 rounded-xl font-medium')
            
            ui.button(
                'Auto-Generate',
                on_click=lambda: ui.navigate.to('/')
            ).classes(f'{theme["button_primary"]} px-6 py-3 rounded-xl font-medium')

@ui.page('/history')
def history_page():
    # Check if user is logged in
    current_user = get_current_user()
    if current_user is None:
        ui.navigate.to('/login')
        return
    
    theme = get_theme_classes()
    theme_manager = get_theme_manager()
    theme_manager.apply_theme()
    
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    
    with ui.column().classes(f'min-h-screen {theme["bg_primary"]}'):
        # Modern navigation header
        navigation = ModernNavigation(current_user, theme)
        navigation.create_header("plans")
        
        # Content with modern styling
        with ui.column().classes('flex-1 p-8 max-w-6xl mx-auto w-full'):
            # Check for active background tasks
            try:
                from ..database.operations import get_user_active_generation_tasks, get_user_recent_generation_tasks
                db = next(get_db())
                active_tasks = get_user_active_generation_tasks(db, current_user['id'])
                
                if active_tasks:
                    with ui.card().classes(f'{theme["card_elevated"]} rounded-2xl p-8 mb-8 border {theme["border"]} {theme["warning_bg"]}'):
                        ui.html(f'<h3 class="text-xl font-bold {theme["warning_text"]} mb-6 flex items-center gap-3"><span class="text-2xl">🔄</span> {len(active_tasks)} Background Generation{"s" if len(active_tasks) != 1 else ""} in Progress</h3>')
                        
                        for task in active_tasks:
                            with ui.row().classes('items-center justify-between w-full mb-2'):
                                with ui.column().classes('flex-1'):
                                    ui.label(f'Task #{task.id}: {task.recipe_count} recipes ({task.status.value})').classes('font-medium text-blue-700')
                                    if task.current_step:
                                        ui.label(task.current_step).classes('text-sm text-blue-600')
                                with ui.column().classes('items-end'):
                                    ui.label(f'{task.progress}%').classes('text-sm font-bold text-blue-800')
                                    if task.progress > 0:
                                        ui.linear_progress(value=task.progress/100).classes('w-24')
                        
                        def refresh_status():
                            ui.navigate.to('/history')  # Simple refresh
                        
                        ui.button('Refresh Status', on_click=refresh_status).props('color=primary size=sm').classes('mt-2')
                
            except Exception as e:
                print(f"Error checking background tasks: {e}")
            
            try:
                db = next(get_db())
                meal_plans = get_user_meal_plans(db, current_user['id'], limit=20)
                
                if meal_plans:
                    ui.html(f'<h2 class="text-2xl font-bold {theme["gradient_text"]} mb-8 text-center">Your Meal Plans ({len(meal_plans)})</h2>')
                    
                    with ui.column().classes('gap-6'):
                        for meal_plan in meal_plans:
                            with ui.card().classes(f'{theme["card_interactive"]} rounded-2xl p-8 border {theme["border"]} transition-all duration-300').on('click', lambda e, plan_id=meal_plan.id: ui.navigate.to(f'/meal-plan/{plan_id}')):
                                with ui.row().classes('items-start justify-between w-full'):
                                    with ui.column().classes('flex-1'):
                                        # Meal plan header
                                        with ui.row().classes('items-center gap-4 mb-4'):
                                            ui.html(f'''
                                                <div class="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center text-2xl text-white">
                                                    📋
                                                </div>
                                            ''')
                                            with ui.column():
                                                ui.html(f'<h3 class="text-xl font-bold {theme["text_primary"]} mb-1">{meal_plan.name}</h3>')
                                                ui.html(f'<p class="text-sm {theme["text_muted"]}">{meal_plan.created_at.strftime("%B %d, %Y at %I:%M %p")}</p>')
                                        
                                        # Stats badges
                                        with ui.row().classes('gap-3 mb-4'):
                                            ui.html(f'<span class="{theme["badge_bg"]} rounded-full px-4 py-2 text-sm font-medium border {theme["border"]}">🍽️ {meal_plan.recipe_count} recipes</span>')
                                            ui.html(f'<span class="{theme["badge_bg"]} rounded-full px-4 py-2 text-sm font-medium border {theme["border"]}">👥 {meal_plan.serving_size} servings</span>')
                                        
                                        # Preferences preview
                                        if meal_plan.liked_foods_snapshot or meal_plan.disliked_foods_snapshot:
                                            with ui.column().classes('gap-2'):
                                                if meal_plan.liked_foods_snapshot:
                                                    preview_text = meal_plan.liked_foods_snapshot[:60] + '...' if len(meal_plan.liked_foods_snapshot) > 60 else meal_plan.liked_foods_snapshot
                                                    ui.html(f'<p class="text-sm {theme["success_text"]} flex items-center gap-2"><span>💚</span> Liked: {preview_text}</p>')
                                                if meal_plan.disliked_foods_snapshot:
                                                    preview_text = meal_plan.disliked_foods_snapshot[:60] + '...' if len(meal_plan.disliked_foods_snapshot) > 60 else meal_plan.disliked_foods_snapshot
                                                    ui.html(f'<p class="text-sm {theme["error_text"]} flex items-center gap-2"><span>🚫</span> Avoided: {preview_text}</p>')
                                    
                                    # Arrow indicator
                                    ui.html(f'<div class="{theme["text_muted"]} text-2xl">→</div>')
                else:
                    # Modern empty state
                    with ui.card().classes(f'{theme["card_elevated"]} rounded-2xl p-16 text-center border {theme["border"]}'):
                        ui.html(f'''
                            <div class="w-32 h-32 bg-gradient-to-br from-slate-100 to-slate-200 rounded-full flex items-center justify-center text-6xl mb-8 mx-auto opacity-60">
                                📋
                            </div>
                        ''')
                        ui.html(f'<h2 class="text-3xl font-bold {theme["text_primary"]} mb-4">No Meal Plans Yet</h2>')
                        ui.html(f'<p class="text-lg {theme["text_secondary"]} mb-8 max-w-md mx-auto">Start creating personalized recipes to see them here! Each meal plan saves your preferences and makes future planning easier.</p>')
                        
                        with ui.button(on_click=lambda: ui.navigate.to('/')).classes(f'{theme["button_primary"]} font-bold py-4 px-8 rounded-xl text-lg shadow-lg transition-all duration-300 hover:scale-105'):
                            with ui.row().classes('items-center gap-3'):
                                ui.html('<span class="text-xl">✨</span>')
                                ui.html('<span>Create First Meal Plan</span>')
        
        # Add bottom navigation for mobile
        create_bottom_navigation("plans", theme)
            
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