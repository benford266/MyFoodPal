"""
Card Components

Modern, accessible card components with consistent styling and interaction patterns.
"""

from nicegui import ui
from typing import Optional, Dict, Any, List, Callable, Literal
from ..tokens.colors import get_color_token
from ..tokens.spacing import get_spacing_token
from .buttons import Button, IconButton

CardVariant = Literal["default", "elevated", "interactive", "outlined"]

class Card:
    """
    Base card component with modern styling and accessibility features.
    
    Features:
    - Multiple visual variants (default, elevated, interactive, outlined)
    - Responsive padding and spacing
    - Hover effects and micro-interactions  
    - Accessibility support with proper ARIA attributes
    - Glass morphism effects with backdrop blur
    """
    
    VARIANTS: Dict[CardVariant, Dict[str, str]] = {
        "default": {
            "light": "bg-white/90 backdrop-blur-xl border border-slate-200/60 shadow-lg",
            "dark": "bg-slate-800/50 backdrop-blur-xl border border-slate-700/40 shadow-2xl"
        },
        "elevated": {
            "light": "bg-white/90 backdrop-blur-xl border border-slate-200/70 shadow-xl hover:shadow-emerald-500/10",
            "dark": "bg-slate-800/60 backdrop-blur-xl border border-slate-700/50 shadow-2xl hover:shadow-emerald-500/10"
        },
        "interactive": {
            "light": "bg-white/70 backdrop-blur-xl border border-slate-200/50 shadow-md hover:bg-white/90 hover:border-slate-300/60 hover:shadow-xl cursor-pointer",
            "dark": "bg-slate-800/40 backdrop-blur-xl border border-slate-700/40 shadow-xl hover:bg-slate-800/60 hover:border-slate-600/50 cursor-pointer"
        },
        "outlined": {
            "light": "bg-transparent border-2 border-slate-300 hover:border-slate-400", 
            "dark": "bg-transparent border-2 border-slate-600 hover:border-slate-500"
        }
    }
    
    def __init__(
        self,
        variant: CardVariant = "default",
        padding: Literal["compact", "default", "spacious"] = "default",
        rounded: Literal["sm", "md", "lg", "xl"] = "lg",
        hover_effects: bool = True,
        full_width: bool = True,
        theme: str = "light",
        additional_classes: str = "",
        on_click: Optional[Callable] = None,
        **props
    ):
        self.variant = variant
        self.padding = padding
        self.rounded = rounded
        self.hover_effects = hover_effects
        self.full_width = full_width
        self.theme = theme
        self.additional_classes = additional_classes
        self.on_click = on_click
        self.props = props
        
        self.card_element = None
    
    def create(self) -> ui.card:
        """Create the card UI element with all styling."""
        
        # Padding configurations
        padding_classes = {
            "compact": "p-4",
            "default": "p-6", 
            "spacious": "p-8"
        }
        
        # Rounded configurations
        rounded_classes = {
            "sm": "rounded-lg",
            "md": "rounded-xl", 
            "lg": "rounded-2xl",
            "xl": "rounded-3xl"
        }
        
        # Build CSS classes
        variant_classes = self.VARIANTS[self.variant][self.theme]
        
        base_classes = [
            # Base card styles
            variant_classes,
            padding_classes[self.padding],
            rounded_classes[self.rounded],
            "transition-all duration-300 ease-out",
            
            # Conditional classes
            "w-full" if self.full_width else "",
            "hover:-translate-y-1" if self.hover_effects and self.variant == "interactive" else "",
            self.additional_classes
        ]
        
        # Create card element
        if self.on_click:
            self.card_element = ui.card().classes(" ".join(filter(None, base_classes))).on('click', self.on_click)
        else:
            self.card_element = ui.card().classes(" ".join(filter(None, base_classes)))
        
        # Add accessibility attributes
        self._add_accessibility_attributes()
        
        # Add any additional props
        for key, value in self.props.items():
            self.card_element.props(f"{key}='{value}'")
            
        return self.card_element
    
    def _add_accessibility_attributes(self):
        """Add accessibility attributes to card."""
        if self.card_element:
            if self.on_click:
                self.card_element.props('role="button" tabindex="0"')
            else:
                self.card_element.props('role="region"')


class RecipeCard(Card):
    """
    Specialized card for displaying recipe information with rich content.
    
    Features:
    - Recipe image with fallback placeholders
    - Star rating system with accessibility
    - Ingredient and instruction previews
    - Progressive disclosure for detailed content
    - Mobile-optimized layouts
    """
    
    def __init__(
        self,
        recipe: Dict[str, Any],
        index: int = 1,
        show_rating: bool = True,
        show_image: bool = True,
        show_full_content: bool = True,
        on_rate: Optional[Callable] = None,
        theme: str = "light",
        **kwargs
    ):
        super().__init__(variant="elevated", theme=theme, **kwargs)
        
        self.recipe = recipe
        self.index = index
        self.show_rating = show_rating
        self.show_image = show_image  
        self.show_full_content = show_full_content
        self.on_rate = on_rate
    
    def create(self) -> ui.card:
        """Create recipe card with rich content."""
        
        card = super().create()
        card.props(f'aria-label="Recipe {self.index}: {self.recipe.get("name", "Untitled Recipe")}"')
        
        with card:
            self._create_recipe_content()
        
        return card
    
    def _create_recipe_content(self):
        """Create the complete recipe card content."""
        
        # Recipe image section
        if self.show_image:
            self._create_image_section()
        
        # Recipe header with title and metadata
        self._create_header_section()
        
        # Recipe tags and badges
        self._create_tags_section()
        
        # Recipe content (ingredients/instructions)
        if self.show_full_content:
            self._create_content_section()
        else:
            self._create_compact_content()
        
        # Rating section
        if self.show_rating and self.on_rate:
            self._create_rating_section()
    
    def _create_image_section(self):
        """Create recipe image with modern styling and fallback."""
        
        with ui.row().classes('justify-center mb-6'):
            if self.recipe.get("image_path"):
                try:
                    # Try to load the recipe image
                    from ...imagegen.image_utils import get_image_display_url
                    
                    base64_url = get_image_display_url(self.recipe["image_path"], use_base64=True)
                    
                    if base64_url:
                        ui.html(f'''
                            <div class="relative group overflow-hidden rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300">
                                <img src="{base64_url}" 
                                     alt="{self.recipe.get('name', 'Recipe image')}"
                                     class="w-full h-64 object-cover transition-transform duration-300 group-hover:scale-105"
                                     style="max-width: 28rem; margin: 0 auto; display: block;"
                                     loading="lazy"
                                     onload="this.style.opacity='1'"
                                     onerror="this.style.display='none'"
                                />
                                <div class="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                                <div class="absolute bottom-4 left-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                                    <span class="bg-black/50 text-white px-3 py-1 rounded-full text-sm backdrop-blur-sm">
                                        View Recipe
                                    </span>
                                </div>
                            </div>
                        ''')
                    else:
                        self._create_image_placeholder()
                        
                except Exception as e:
                    print(f"Error loading recipe image: {e}")
                    self._create_image_placeholder()
            else:
                self._create_image_placeholder()
    
    def _create_image_placeholder(self):
        """Create elegant image placeholder."""
        ui.html(f'''
            <div class="relative overflow-hidden rounded-xl bg-gradient-to-br from-emerald-100 to-teal-100 flex items-center justify-center group hover:from-emerald-200 hover:to-teal-200 transition-colors duration-300"
                 style="height: 16rem; width: 28rem; max-width: 100%;">
                <div class="text-center transition-transform duration-300 group-hover:scale-110">
                    <div class="text-6xl opacity-60 mb-3">🍽️</div>
                    <p class="text-sm text-slate-600 font-medium">Recipe Image</p>
                </div>
            </div>
        ''')
    
    def _create_header_section(self):
        """Create recipe header with title and basic info."""
        
        with ui.row().classes('items-start gap-4 mb-4'):
            # Recipe number badge
            ui.html(f'''
                <div class="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-600 text-white rounded-full flex items-center justify-center text-lg font-bold shadow-lg">
                    {self.index}
                </div>
            ''')
            
            # Title and description
            with ui.column().classes('flex-1 min-w-0'):
                ui.html(f'''
                    <h3 class="text-xl font-bold text-slate-900 mb-2 line-clamp-2" role="heading" aria-level="3">
                        {self.recipe.get("name", "Untitled Recipe")}
                    </h3>
                ''')
                
                if self.recipe.get("description"):
                    ui.html(f'''
                        <p class="text-sm text-slate-600 italic line-clamp-2 leading-relaxed">
                            {self.recipe.get("description", "")}
                        </p>
                    ''')
    
    def _create_tags_section(self):
        """Create recipe tags and metadata badges."""
        
        with ui.row().classes('gap-2 flex-wrap mb-6'):
            # Cuisine tag
            if self.recipe.get("cuisine_inspiration"):
                ui.html(f'''
                    <span class="bg-slate-100 text-slate-700 rounded-full px-3 py-1.5 text-xs font-medium border border-slate-200 transition-all duration-200 hover:bg-slate-200">
                        🌍 {self.recipe.get("cuisine_inspiration")}
                    </span>
                ''')
            
            # Difficulty badge
            if self.recipe.get("difficulty"):
                difficulty_config = {
                    "Easy": {"color": "bg-green-100 text-green-700 border-green-200", "emoji": "👶"},
                    "Medium": {"color": "bg-yellow-100 text-yellow-700 border-yellow-200", "emoji": "👨‍🍳"}, 
                    "Advanced": {"color": "bg-red-100 text-red-700 border-red-200", "emoji": "🧑‍🍳"}
                }
                
                config = difficulty_config.get(self.recipe.get("difficulty"), difficulty_config["Medium"])
                
                ui.html(f'''
                    <span class="{config["color"]} rounded-full px-3 py-1.5 text-xs font-medium border transition-all duration-200 hover:scale-105">
                        {config["emoji"]} {self.recipe.get("difficulty")}
                    </span>
                ''')
            
            # Time badges
            for time_type, emoji in [("prep_time", "⏱️"), ("cook_time", "🔥")]:
                if self.recipe.get(time_type):
                    ui.html(f'''
                        <span class="bg-blue-100 text-blue-700 border-blue-200 rounded-full px-3 py-1.5 text-xs font-medium border transition-all duration-200 hover:scale-105">
                            {emoji} {self.recipe.get(time_type)}
                        </span>
                    ''')
    
    def _create_content_section(self):
        """Create full content with ingredients and instructions."""
        
        with ui.row().classes('gap-8 w-full'):
            # Ingredients column
            with ui.column().classes('flex-1'):
                ui.html(f'''
                    <div class="flex items-center gap-3 mb-4">
                        <div class="text-2xl" aria-hidden="true">🛒</div>
                        <h4 class="text-lg font-semibold text-slate-900" role="heading" aria-level="4">Ingredients</h4>
                    </div>
                ''')
                
                self._create_ingredients_list()
            
            # Instructions column
            with ui.column().classes('flex-1'):
                ui.html(f'''
                    <div class="flex items-center gap-3 mb-4">
                        <div class="text-2xl" aria-hidden="true">👨‍🍳</div>
                        <h4 class="text-lg font-semibold text-slate-900" role="heading" aria-level="4">Instructions</h4>
                    </div>
                ''')
                
                self._create_instructions_list()
    
    def _create_compact_content(self):
        """Create compact content preview with expand option."""
        
        ingredients_count = len(self.recipe.get("ingredients", []))
        instructions_count = len(self.recipe.get("instructions", []))
        
        with ui.row().classes('gap-4 text-sm text-slate-600 mb-4'):
            ui.html(f'''
                <span class="flex items-center gap-2">
                    <span class="text-emerald-600">📝</span>
                    {ingredients_count} ingredients • {instructions_count} steps
                </span>
            ''')
        
        # Expand button
        expand_btn = Button(
            text="Show Full Recipe ▼",
            variant="ghost",
            size="sm",
            on_click=self._toggle_full_content
        )
        expand_btn.create()
    
    def _toggle_full_content(self):
        """Toggle between compact and full content view."""
        # This would require state management in a real implementation
        pass
    
    def _create_ingredients_list(self):
        """Create styled ingredients list."""
        
        with ui.column().classes('gap-3') as ingredients:
            ingredients.props('role="list" aria-label="Recipe ingredients"')
            
            for ingredient in self.recipe.get("ingredients", []):
                with ui.row().classes('items-start gap-3') as item:
                    item.props('role="listitem"')
                    
                    # Bullet point
                    ui.html('<div class="w-2 h-2 bg-emerald-400 rounded-full flex-shrink-0 mt-2.5"></div>')
                    
                    # Ingredient content
                    if isinstance(ingredient, dict):
                        quantity = ingredient.get("quantity", "")
                        unit = ingredient.get("unit", "")
                        item_name = ingredient.get("item", "")
                        display_text = f"{quantity} {unit} {item_name}".strip()
                        
                        with ui.column().classes('flex-1'):
                            ui.html(f'<span class="text-sm text-slate-900 leading-relaxed font-medium">{display_text}</span>')
                            
                            if ingredient.get("notes"):
                                ui.html(f'<span class="text-xs text-slate-500 italic mt-1">💡 {ingredient.get("notes")}</span>')
                    else:
                        display_text = str(ingredient) if ingredient else ""
                        if display_text:
                            ui.html(f'<span class="text-sm text-slate-900 leading-relaxed font-medium">{display_text}</span>')
    
    def _create_instructions_list(self):
        """Create styled instructions list."""
        
        with ui.column().classes('gap-4') as instructions:
            instructions.props('role="list" aria-label="Recipe instructions"')
            
            for j, step in enumerate(self.recipe.get("instructions", []), 1):
                if step and step.strip():
                    with ui.row().classes('items-start gap-4') as item:
                        item.props('role="listitem"')
                        
                        # Step number
                        ui.html(f'''
                            <div class="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-emerald-500 to-teal-600 text-white rounded-full flex items-center justify-center text-sm font-bold shadow-sm">
                                {j}
                            </div>
                        ''')
                        
                        # Step text
                        ui.html(f'<p class="text-sm text-slate-900 leading-relaxed flex-1 pt-1">{step}</p>')
    
    def _create_rating_section(self):
        """Create interactive rating section."""
        
        with ui.column().classes('mt-8 pt-6 border-t border-slate-200'):
            with ui.row().classes('items-center justify-between'):
                ui.html('<span class="text-sm text-slate-600 font-medium">Rate this recipe:</span>')
                
                with ui.row().classes('gap-1'):
                    for star in range(1, 6):
                        star_btn = IconButton(
                            icon="⭐",
                            variant="ghost",
                            size="sm",
                            tooltip=f'Rate {star} star{"s" if star != 1 else ""}',
                            on_click=lambda r=star: self._handle_rating(r)
                        )
                        star_btn.create().classes("hover:scale-125 transition-transform duration-200 text-lg opacity-60 hover:opacity-100")
    
    def _handle_rating(self, rating: int):
        """Handle star rating click."""
        if self.on_rate:
            recipe_name = self.recipe.get("name", "Untitled Recipe")
            self.on_rate(self.index - 1, recipe_name, rating)


class MealPlanCard(Card):
    """Specialized card for displaying saved meal plans."""
    
    def __init__(
        self,
        meal_plan: Dict[str, Any], 
        theme: str = "light",
        **kwargs
    ):
        super().__init__(variant="interactive", theme=theme, **kwargs)
        self.meal_plan = meal_plan
    
    def create(self) -> ui.card:
        """Create meal plan card with summary content."""
        
        card = super().create()
        
        with card:
            self._create_meal_plan_content()
        
        return card
    
    def _create_meal_plan_content(self):
        """Create meal plan card content."""
        
        with ui.row().classes('items-start justify-between w-full'):
            with ui.column().classes('flex-1'):
                # Meal plan header
                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.html('''
                        <div class="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center text-2xl text-white shadow-lg">
                            📋
                        </div>
                    ''')
                    
                    with ui.column():
                        ui.html(f'<h3 class="text-xl font-bold text-slate-900 mb-1">{self.meal_plan.get("name", "Untitled Plan")}</h3>')
                        
                        # Format timestamp
                        if hasattr(self.meal_plan, 'created_at'):
                            timestamp = self.meal_plan.created_at.strftime("%B %d, %Y at %I:%M %p")
                            ui.html(f'<p class="text-sm text-slate-500">{timestamp}</p>')
                
                # Stats badges
                with ui.row().classes('gap-3 mb-4'):
                    ui.html(f'''
                        <span class="bg-emerald-100 text-emerald-700 border border-emerald-200 rounded-full px-4 py-2 text-sm font-medium">
                            🍽️ {self.meal_plan.get("recipe_count", 0)} recipes
                        </span>
                    ''')
                    
                    ui.html(f'''
                        <span class="bg-blue-100 text-blue-700 border border-blue-200 rounded-full px-4 py-2 text-sm font-medium">
                            👥 {self.meal_plan.get("serving_size", 0)} servings
                        </span>
                    ''')
                
                # Preferences preview
                self._create_preferences_preview()
            
            # Arrow indicator
            ui.html('<div class="text-slate-400 text-2xl">→</div>')
    
    def _create_preferences_preview(self):
        """Create preview of food preferences."""
        
        liked_foods = getattr(self.meal_plan, 'liked_foods_snapshot', '')
        disliked_foods = getattr(self.meal_plan, 'disliked_foods_snapshot', '')
        
        if liked_foods or disliked_foods:
            with ui.column().classes('gap-2'):
                if liked_foods:
                    preview = liked_foods[:60] + '...' if len(liked_foods) > 60 else liked_foods
                    ui.html(f'''
                        <p class="text-sm text-emerald-700 flex items-start gap-2">
                            <span class="text-base flex-shrink-0">💚</span>
                            <span><strong>Liked:</strong> {preview}</span>
                        </p>
                    ''')
                
                if disliked_foods:
                    preview = disliked_foods[:60] + '...' if len(disliked_foods) > 60 else disliked_foods
                    ui.html(f'''
                        <p class="text-sm text-red-700 flex items-start gap-2">
                            <span class="text-base flex-shrink-0">🚫</span>
                            <span><strong>Avoided:</strong> {preview}</span>
                        </p>
                    ''')