from nicegui import ui
from typing import Dict, Any, List, Optional, Callable
import json

def create_modern_recipe_card(
    recipe: Dict[str, Any], 
    index: int, 
    theme: Dict[str, str],
    on_rate: Optional[Callable] = None,
    saved_meal_plan_id: Optional[int] = None,
    show_rating: bool = True,
    show_image: bool = True,
    card_style: str = "default"  # "default", "compact", "featured"
) -> ui.card:
    """Create a modern, interactive recipe card with multiple style variants"""
    
    # Card style configurations
    card_styles = {
        "default": {
            "container_classes": f'{theme["card_elevated"]} rounded-2xl p-6 w-full transition-all duration-300',
            "image_height": "16rem",
            "show_full_details": True
        },
        "compact": {
            "container_classes": f'{theme["card"]} rounded-xl p-4 w-full transition-all duration-300',
            "image_height": "12rem", 
            "show_full_details": False
        },
        "featured": {
            "container_classes": f'{theme["card_elevated"]} rounded-3xl p-8 w-full transition-all duration-300 border-2 {theme["border_accent"]}',
            "image_height": "20rem",
            "show_full_details": True
        }
    }
    
    style_config = card_styles.get(card_style, card_styles["default"])
    
    with ui.card().classes(style_config["container_classes"]).props(f'role="article" aria-labelledby="recipe-title-{index}" tabindex="0"') as card:
        # Recipe header section
        with ui.column().classes('w-full mb-6'):
            # Recipe image with modern styling
            if show_image and recipe.get("image_path"):
                with ui.row().classes('justify-center mb-4'):
                    _create_recipe_image(recipe, style_config["image_height"], theme)
            elif show_image:
                # Elegant placeholder
                with ui.row().classes('justify-center mb-4'):
                    _create_image_placeholder(style_config["image_height"], theme)
            
            # Recipe title and metadata
            _create_recipe_header(recipe, index, theme, style_config["show_full_details"])
            
            # Tags and badges
            if style_config["show_full_details"]:
                _create_recipe_tags(recipe, theme)
        
        # Progressive disclosure content
        content_container = ui.column().classes('w-full')
        
        if card_style == "compact":
            # Compact view - show summary with expand option
            _create_compact_content(recipe, theme, content_container)
        else:
            # Full view - show all details
            _create_full_content(recipe, theme, style_config["show_full_details"])
        
        # Rating section (if enabled)
        if show_rating and saved_meal_plan_id and on_rate:
            _create_rating_section(recipe, index, theme, on_rate, saved_meal_plan_id)
    
    return card

def _create_recipe_image(recipe: Dict[str, Any], height: str, theme: Dict[str, str]):
    """Create optimized recipe image with fallback"""
    try:
        from ..imagegen.image_utils import get_image_display_url
        
        # Try base64 first for reliability
        base64_url = get_image_display_url(recipe["image_path"], use_base64=True)
        
        if base64_url:
            ui.html(f'''
                <div class="relative group overflow-hidden rounded-xl shadow-lg">
                    <img src="{base64_url}" 
                         alt="{recipe.get('name', 'Recipe image')}"
                         class="w-full object-cover transition-transform duration-300 group-hover:scale-105"
                         style="height: {height}; max-width: 28rem; margin: 0 auto; display: block;"
                         loading="lazy"
                         onload="this.style.opacity='1'"
                         onerror="this.parentElement.innerHTML='<div class=&quot;w-full h-full bg-gradient-to-br from-emerald-100 to-teal-100 flex items-center justify-center rounded-xl&quot;><div class=&quot;text-4xl opacity-60&quot;>🍽️</div></div>'"
                    />
                    <div class="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </div>
            ''')
        else:
            _create_image_placeholder(height, theme)
            
    except Exception as e:
        print(f"Error creating recipe image: {e}")
        _create_image_placeholder(height, theme)

def _create_image_placeholder(height: str, theme: Dict[str, str]):
    """Create an elegant image placeholder"""
    ui.html(f'''
        <div class="relative overflow-hidden rounded-xl {theme["bg_accent"]} flex items-center justify-center group cursor-pointer"
             style="height: {height}; max-width: 28rem; margin: 0 auto;">
            <div class="text-center transition-transform duration-300 group-hover:scale-110">
                <div class="text-6xl opacity-40 mb-2">🍽️</div>
                <p class="text-sm {theme["text_muted"]}">Recipe Image</p>
            </div>
        </div>
    ''')

def _create_recipe_header(recipe: Dict[str, Any], index: int, theme: Dict[str, str], show_details: bool):
    """Create recipe header with title and basic info"""
    with ui.row().classes('items-start gap-4 w-full'):
        # Recipe number badge
        ui.html(f'''
            <div class="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-600 text-white rounded-full flex items-center justify-center text-lg font-bold shadow-lg">
                {index}
            </div>
        ''')
        
        # Title and description
        with ui.column().classes('flex-1 min-w-0'):
            ui.html(f'''
                <h3 id="recipe-title-{index}" class="text-xl font-bold {theme["text_primary"]} mb-1 line-clamp-2" role="heading" aria-level="3">
                    {recipe.get("name", "Untitled Recipe")}
                </h3>
            ''')
            
            if show_details and recipe.get("description"):
                ui.html(f'''
                    <p class="text-sm {theme["text_secondary"]} italic line-clamp-2">
                        {recipe.get("description", "")}
                    </p>
                ''')

def _create_recipe_tags(recipe: Dict[str, Any], theme: Dict[str, str]):
    """Create recipe tags and metadata badges"""
    with ui.row().classes('gap-2 flex-wrap mt-3'):
        # Cuisine tag
        if recipe.get("cuisine_inspiration"):
            ui.html(f'''
                <span class="{theme["chip_bg"]} rounded-full px-3 py-1 text-xs font-medium border {theme["border"]} transition-colors duration-200">
                    🌍 {recipe.get("cuisine_inspiration")}
                </span>
            ''')
        
        # Difficulty badge
        if recipe.get("difficulty"):
            difficulty_colors = {
                "Easy": "bg-green-100 text-green-700 border-green-200",
                "Medium": "bg-yellow-100 text-yellow-700 border-yellow-200", 
                "Advanced": "bg-red-100 text-red-700 border-red-200"
            }
            difficulty_emoji = {"Easy": "👶", "Medium": "👨‍🍳", "Advanced": "🧑‍🍳"}
            color_class = difficulty_colors.get(recipe.get("difficulty"), theme["chip_bg"])
            
            ui.html(f'''
                <span class="{color_class} rounded-full px-3 py-1 text-xs font-medium border transition-all duration-200 hover:scale-105">
                    {difficulty_emoji.get(recipe.get("difficulty"), "👨‍🍳")} {recipe.get("difficulty")}
                </span>
            ''')
        
        # Time badges
        if recipe.get("prep_time"):
            ui.html(f'''
                <span class="{theme["badge_bg"]} rounded-full px-3 py-1 text-xs font-medium border {theme["border"]} transition-all duration-200 hover:scale-105">
                    ⏱️ {recipe.get("prep_time")}
                </span>
            ''')
        
        if recipe.get("cook_time"):
            ui.html(f'''
                <span class="{theme["badge_bg"]} rounded-full px-3 py-1 text-xs font-medium border {theme["border"]} transition-all duration-200 hover:scale-105">
                    🔥 {recipe.get("cook_time")}
                </span>
            ''')

def _create_compact_content(recipe: Dict[str, Any], theme: Dict[str, str], container):
    """Create compact recipe content with expand option"""
    with container:
        # Quick preview
        with ui.row().classes('gap-4 text-sm'):
            ingredients_count = len(recipe.get("ingredients", []))
            instructions_count = len(recipe.get("instructions", []))
            
            ui.html(f'''
                <span class="{theme["text_secondary"]}">
                    📝 {ingredients_count} ingredients • {instructions_count} steps
                </span>
            ''')
        
        # Expand button
        expanded = {"value": False}
        expand_container = ui.column().classes('w-full mt-4')
        
        def toggle_expand():
            expanded["value"] = not expanded["value"]
            expand_container.clear()
            
            if expanded["value"]:
                with expand_container:
                    ui.html('<div class="slide-down">')
                    _create_full_content(recipe, theme, True)
                    ui.html('</div>')
                expand_btn.text = "Show Less ▲"
            else:
                expand_btn.text = "Show More ▼"
        
        expand_btn = ui.button(
            "Show More ▼", 
            on_click=toggle_expand
        ).classes(f'{theme["button_ghost"]} text-sm py-2 px-4 rounded-lg')

def _create_full_content(recipe: Dict[str, Any], theme: Dict[str, str], show_details: bool = True):
    """Create full recipe content with ingredients and instructions"""
    with ui.row().classes('gap-8 w-full mt-6'):
        # Ingredients column
        with ui.column().classes('flex-1'):
            ui.html(f'''
                <div class="flex items-center gap-3 mb-4">
                    <div class="text-2xl" aria-hidden="true">🛒</div>
                    <h4 class="text-lg font-semibold {theme["text_primary"]}" role="heading" aria-level="4">Ingredients</h4>
                </div>
            ''')
            
            _create_ingredients_list(recipe, theme)
        
        # Instructions column  
        with ui.column().classes('flex-1'):
            ui.html(f'''
                <div class="flex items-center gap-3 mb-4">
                    <div class="text-2xl" aria-hidden="true">👨‍🍳</div>
                    <h4 class="text-lg font-semibold {theme["text_primary"]}" role="heading" aria-level="4">Instructions</h4>
                </div>
            ''')
            
            _create_instructions_list(recipe, theme)
    
    # Additional sections (tips, presentation)
    if show_details:
        _create_additional_sections(recipe, theme)

def _create_ingredients_list(recipe: Dict[str, Any], theme: Dict[str, str]):
    """Create styled ingredients list with proper semantic markup"""
    with ui.column().classes('gap-2').props('role="list" aria-label="Recipe ingredients"'):
        for ingredient in recipe.get("ingredients", []):
            with ui.row().classes('items-start gap-3 py-1').props('role="listitem"'):
                # Bullet point
                ui.html(f'<div class="w-2 h-2 bg-emerald-400 rounded-full flex-shrink-0 mt-2" aria-hidden="true"></div>')
                
                # Ingredient text
                if isinstance(ingredient, dict):
                    quantity = ingredient.get("quantity", "")
                    unit = ingredient.get("unit", "")
                    item = ingredient.get("item", "")
                    display_text = f"{quantity} {unit} {item}".strip()
                    
                    with ui.column().classes('flex-1'):
                        ui.html(f'<span class="text-sm {theme["text_primary"]} leading-relaxed">{display_text}</span>')
                        
                        if ingredient.get("notes"):
                            ui.html(f'<span class="text-xs {theme["text_muted"]} italic ml-2">💡 {ingredient.get("notes")}</span>')
                else:
                    display_text = str(ingredient) if ingredient else ""
                    if display_text:
                        ui.html(f'<span class="text-sm {theme["text_primary"]} leading-relaxed flex-1">{display_text}</span>')

def _create_instructions_list(recipe: Dict[str, Any], theme: Dict[str, str]):
    """Create styled instructions list with proper semantic markup"""
    with ui.column().classes('gap-3').props('role="list" aria-label="Recipe instructions"'):
        for j, step in enumerate(recipe.get("instructions", []), 1):
            if step and step.strip():
                with ui.row().classes('items-start gap-3').props('role="listitem"'):
                    # Step number
                    ui.html(f'''
                        <div class="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-emerald-500 to-teal-600 text-white rounded-full flex items-center justify-center text-sm font-bold shadow-sm" aria-label="Step {j}">
                            {j}
                        </div>
                    ''')
                    
                    # Step text
                    ui.html(f'<p class="text-sm {theme["text_primary"]} leading-relaxed flex-1">{step}</p>')

def _create_additional_sections(recipe: Dict[str, Any], theme: Dict[str, str]):
    """Create chef tips and presentation sections"""
    if recipe.get("chef_tips") or recipe.get("presentation"):
        with ui.column().classes('w-full mt-8 pt-6 border-t'):
            ui.html(f'<div class="border-t {theme["divider"]} w-full"></div>')
            
            with ui.row().classes('gap-8 w-full mt-6'):
                # Chef Tips
                if recipe.get("chef_tips"):
                    with ui.column().classes('flex-1'):
                        ui.html(f'''
                            <div class="flex items-center gap-3 mb-4">
                                <div class="text-2xl">💡</div>
                                <h4 class="text-lg font-semibold {theme["text_primary"]}">Chef Tips</h4>
                            </div>
                        ''')
                        
                        with ui.column().classes('gap-2'):
                            for tip in recipe.get("chef_tips", []):
                                with ui.row().classes('items-start gap-3'):
                                    ui.html('<div class="w-2 h-2 bg-yellow-400 rounded-full flex-shrink-0 mt-2"></div>')
                                    ui.html(f'<p class="text-sm {theme["text_primary"]} leading-relaxed flex-1">{tip}</p>')
                
                # Presentation
                if recipe.get("presentation"):
                    with ui.column().classes('flex-1'):
                        ui.html(f'''
                            <div class="flex items-center gap-3 mb-4">
                                <div class="text-2xl">🎨</div>
                                <h4 class="text-lg font-semibold {theme["text_primary"]}">Presentation</h4>
                            </div>
                        ''')
                        ui.html(f'<p class="text-sm {theme["text_primary"]} leading-relaxed">{recipe.get("presentation")}</p>')

def _create_rating_section(
    recipe: Dict[str, Any], 
    index: int, 
    theme: Dict[str, str],
    on_rate: Callable,
    saved_meal_plan_id: int
):
    """Create interactive rating section"""
    with ui.row().classes('justify-end mt-6 pt-4 border-t'):
        ui.html(f'<div class="border-t {theme["divider"]} w-full mb-4"></div>')
        
        with ui.column().classes('items-end'):
            ui.html(f'<span class="text-sm {theme["text_secondary"]} mb-2">Rate this recipe:</span>')
            
            with ui.row().classes('gap-1'):
                for star in range(1, 6):
                    star_button = ui.button(
                        '⭐',
                        on_click=lambda idx=index-1, title=recipe.get("name", "Untitled Recipe"), r=star: on_rate(idx, title, r)
                    ).classes(f'''
                        text-lg bg-transparent border-none p-1 hover:scale-110 transition-all duration-200 
                        cursor-pointer opacity-60 hover:opacity-100 rounded-lg hover:bg-yellow-50 touch-target focus-visible
                    ''').style('min-width: 44px; min-height: 44px;').props(f'aria-label="Rate recipe {star} star{"s" if star != 1 else ""}" role="button" tabindex="0"')
                    
                    star_labels = {1: 'Poor', 2: 'Fair', 3: 'Good', 4: 'Very Good', 5: 'Excellent'}
                    star_button.tooltip(f'{star} star{"s" if star != 1 else ""} - {star_labels[star]}')

def create_loading_recipe_card(theme: Dict[str, str]) -> ui.card:
    """Create a loading skeleton for recipe cards"""
    with ui.card().classes(f'{theme["card"]} rounded-2xl p-6 w-full') as card:
        # Image skeleton
        with ui.row().classes('justify-center mb-4'):
            ui.html(f'''
                <div class="loading-shimmer rounded-xl" style="width: 24rem; height: 16rem;"></div>
            ''')
        
        # Header skeleton  
        with ui.row().classes('items-center gap-4 mb-4'):
            ui.html('<div class="loading-shimmer w-12 h-12 rounded-full"></div>')
            with ui.column().classes('flex-1 gap-2'):
                ui.html('<div class="loading-shimmer h-6 w-3/4 rounded"></div>')
                ui.html('<div class="loading-shimmer h-4 w-1/2 rounded"></div>')
        
        # Tags skeleton
        with ui.row().classes('gap-2 mb-6'):
            ui.html('<div class="loading-shimmer h-6 w-20 rounded-full"></div>')
            ui.html('<div class="loading-shimmer h-6 w-16 rounded-full"></div>')
            ui.html('<div class="loading-shimmer h-6 w-24 rounded-full"></div>')
        
        # Content skeleton
        with ui.row().classes('gap-8'):
            with ui.column().classes('flex-1 gap-2'):
                ui.html('<div class="loading-shimmer h-5 w-32 rounded mb-4"></div>')
                for _ in range(4):
                    ui.html('<div class="loading-shimmer h-4 w-full rounded mb-2"></div>')
            
            with ui.column().classes('flex-1 gap-2'):
                ui.html('<div class="loading-shimmer h-5 w-32 rounded mb-4"></div>')
                for _ in range(6):
                    ui.html('<div class="loading-shimmer h-4 w-full rounded mb-2"></div>')
    
    return card

def create_compact_loading_card(theme: Dict[str, str]) -> ui.card:
    """Create a compact loading skeleton for smaller cards"""
    with ui.card().classes(f'{theme["card"]} rounded-xl p-4 w-full') as card:
        # Header skeleton
        with ui.row().classes('items-center gap-3 mb-3'):
            ui.html('<div class="loading-shimmer w-8 h-8 rounded-full"></div>')
            with ui.column().classes('flex-1 gap-1'):
                ui.html('<div class="loading-shimmer h-4 w-2/3 rounded"></div>')
                ui.html('<div class="loading-shimmer h-3 w-1/2 rounded"></div>')
        
        # Content skeleton
        with ui.column().classes('gap-2'):
            for _ in range(2):
                ui.html('<div class="loading-shimmer h-3 w-full rounded"></div>')
            ui.html('<div class="loading-shimmer h-3 w-3/4 rounded"></div>')
    
    return card

def create_loading_meal_plan_card(theme: Dict[str, str]) -> ui.card:
    """Create a loading skeleton for meal plan cards"""
    with ui.card().classes(f'{theme["card_interactive"]} rounded-2xl p-8 border {theme["border"]} w-full') as card:
        with ui.row().classes('items-start justify-between w-full'):
            with ui.column().classes('flex-1'):
                # Header skeleton
                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.html('<div class="loading-shimmer w-16 h-16 rounded-xl"></div>')
                    with ui.column().classes('flex-1 gap-2'):
                        ui.html('<div class="loading-shimmer h-6 w-3/4 rounded"></div>')
                        ui.html('<div class="loading-shimmer h-4 w-1/2 rounded"></div>')
                
                # Badges skeleton
                with ui.row().classes('gap-3 mb-4'):
                    ui.html('<div class="loading-shimmer h-8 w-24 rounded-full"></div>')
                    ui.html('<div class="loading-shimmer h-8 w-20 rounded-full"></div>')
                
                # Preferences skeleton
                with ui.column().classes('gap-2'):
                    ui.html('<div class="loading-shimmer h-4 w-full rounded"></div>')
                    ui.html('<div class="loading-shimmer h-4 w-5/6 rounded"></div>')
            
            # Arrow skeleton
            ui.html('<div class="loading-shimmer w-6 h-6 rounded"></div>')
    
    return card

def create_loading_search_results(theme: Dict[str, str], container) -> None:
    """Create loading skeletons for search results"""
    with container:
        ui.html(f'<div class="text-center mb-6"><div class="loading-shimmer h-6 w-48 rounded mx-auto mb-2"></div><div class="loading-shimmer h-4 w-32 rounded mx-auto"></div></div>')
        
        with ui.row().classes('gap-4 flex-wrap'):
            for _ in range(6):
                create_compact_loading_card(theme)

def create_progressive_loading_state(
    container, 
    theme: Dict[str, str], 
    stage: str = "initializing",
    progress: float = 0.0,
    message: str = ""
) -> None:
    """Create a progressive loading state with different stages"""
    container.clear()
    
    stages = {
        "initializing": {"icon": "⚙️", "title": "Initializing", "color": "blue"},
        "generating": {"icon": "🧠", "title": "Generating Recipes", "color": "emerald"},
        "processing": {"icon": "⚡", "title": "Processing Content", "color": "purple"},
        "finalizing": {"icon": "✨", "title": "Finalizing Results", "color": "teal"}
    }
    
    stage_info = stages.get(stage, stages["initializing"])
    
    with container:
        with ui.card().classes(f'{theme["card_elevated"]} rounded-2xl p-8 text-center border {theme["border"]}'):
            # Animated icon
            ui.html(f'''
                <div class="w-20 h-20 bg-gradient-to-br from-{stage_info["color"]}-100 to-{stage_info["color"]}-200 rounded-full flex items-center justify-center text-4xl mb-6 mx-auto animate-pulse">
                    {stage_info["icon"]}
                </div>
            ''')
            
            # Title and message
            ui.html(f'<h3 class="text-2xl font-bold {theme["text_primary"]} mb-2">{stage_info["title"]}</h3>')
            if message:
                ui.html(f'<p class="text-lg {theme["text_secondary"]} mb-6">{message}</p>')
            
            # Progress bar
            if progress > 0:
                ui.html(f'<div class="w-full bg-{stage_info["color"]}-100 rounded-full h-3 mb-4">')
                ui.html(f'<div class="bg-gradient-to-r from-{stage_info["color"]}-500 to-{stage_info["color"]}-600 h-3 rounded-full transition-all duration-300" style="width: {progress}%"></div>')
                ui.html('</div>')
                ui.html(f'<p class="text-sm {theme["text_muted"]} font-medium">{int(progress)}% Complete</p>')
            else:
                # Indeterminate loading bar
                ui.html(f'''
                    <div class="w-full bg-{stage_info["color"]}-100 rounded-full h-3 mb-4 overflow-hidden">
                        <div class="bg-gradient-to-r from-{stage_info["color"]}-500 to-{stage_info["color"]}-600 h-3 rounded-full animate-pulse" style="width: 40%; animation: slide 2s ease-in-out infinite alternate;"></div>
                    </div>
                ''')

def create_error_state(
    container, 
    theme: Dict[str, str], 
    title: str = "Something went wrong",
    message: str = "Please try again",
    retry_callback: Optional[Callable] = None
) -> None:
    """Create a user-friendly error state with recovery options"""
    container.clear()
    
    with container:
        with ui.card().classes(f'{theme["error_bg"]} rounded-2xl p-8 text-center border {theme["border"]}'):
            # Error icon
            ui.html(f'''
                <div class="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center text-4xl mb-6 mx-auto">
                    😕
                </div>
            ''')
            
            # Error content
            ui.html(f'<h3 class="text-2xl font-bold {theme["error_text"]} mb-2">{title}</h3>')
            ui.html(f'<p class="text-lg {theme["text_secondary"]} mb-6">{message}</p>')
            
            # Action buttons
            with ui.row().classes('gap-4 justify-center'):
                if retry_callback:
                    ui.button(
                        'Try Again',
                        on_click=retry_callback
                    ).classes(f'{theme["button_primary"]} px-6 py-3 rounded-xl font-medium')
                
                ui.button(
                    'Go Back',
                    on_click=lambda: ui.navigate.back()
                ).classes(f'{theme["button_ghost"]} px-6 py-3 rounded-xl font-medium')

def create_empty_state(
    container,
    theme: Dict[str, str],
    title: str = "Nothing here yet",
    message: str = "Get started by creating your first item",
    action_text: str = "Get Started",
    action_callback: Optional[Callable] = None,
    icon: str = "📦"
) -> None:
    """Create an engaging empty state with clear next steps"""
    container.clear()
    
    with container:
        with ui.card().classes(f'{theme["card_elevated"]} rounded-2xl p-16 text-center border {theme["border"]}'):
            # Empty state illustration
            ui.html(f'''
                <div class="w-32 h-32 bg-gradient-to-br from-slate-100 to-slate-200 rounded-full flex items-center justify-center text-6xl mb-8 mx-auto opacity-60">
                    {icon}
                </div>
            ''')
            
            # Content
            ui.html(f'<h2 class="text-3xl font-bold {theme["text_primary"]} mb-4">{title}</h2>')
            ui.html(f'<p class="text-lg {theme["text_secondary"]} mb-8 max-w-md mx-auto">{message}</p>')
            
            # Action button
            if action_callback:
                with ui.button(on_click=action_callback).classes(f'{theme["button_primary"]} font-bold py-4 px-8 rounded-xl text-lg shadow-lg transition-all duration-300 hover:scale-105'):
                    with ui.row().classes('items-center gap-3'):
                        ui.html('<span class="text-xl">✨</span>')
                        ui.html(f'<span>{action_text}</span>')