from nicegui import ui
from typing import Dict, List, Callable, Optional, Any
import asyncio
from datetime import datetime, timedelta

class ModernSearchBar:
    """Modern search bar with real-time filtering and suggestions"""
    
    def __init__(self, theme: Dict[str, str], on_search: Callable[[str], None]):
        self.theme = theme
        self.on_search = on_search
        self.search_input = None
        self.suggestions_container = None
        self.search_timer = None
        
    def create_search_bar(self, placeholder: str = "Search recipes, ingredients, or cuisines...") -> ui.column:
        """Create the search bar with suggestions dropdown"""
        with ui.column().classes('w-full relative') as container:
            # Search input with icon
            with ui.row().classes(f'{self.theme["input_bg"]} rounded-xl border-2 {self.theme["border"]} p-4 items-center gap-3 focus-within:border-emerald-400 transition-colors duration-200'):
                ui.html('<span class="text-xl opacity-60">🔍</span>')
                
                self.search_input = ui.input(
                    placeholder=placeholder
                ).classes('flex-1 bg-transparent border-none outline-none').props('outlined=false')
                
                # Clear button (show when there's text)
                clear_btn = ui.button(
                    '✕',
                    on_click=self._clear_search
                ).classes('w-6 h-6 rounded-full bg-gray-200 hover:bg-gray-300 text-xs opacity-0 transition-opacity').style('min-width: 24px;')
                
                # Voice search button (future feature)
                ui.button(
                    '🎤',
                    on_click=lambda: ui.notify('Voice search coming soon!', type='info')
                ).classes(f'{self.theme["button_ghost"]} w-8 h-8 rounded-lg text-lg').tooltip('Voice Search (Coming Soon)')
            
            # Suggestions dropdown
            self.suggestions_container = ui.column().classes('absolute top-full left-0 right-0 z-50 mt-2 hidden')
            
            # Bind search events
            self.search_input.on('input', self._on_input_change)
            self.search_input.on('focus', self._on_focus)
            self.search_input.on('blur', self._on_blur)
            
            # Update clear button visibility
            def update_clear_button():
                if self.search_input.value:
                    clear_btn.classes(remove='opacity-0')
                else:
                    clear_btn.classes(add='opacity-0')
            
            self.search_input.on('input', lambda: update_clear_button())
        
        return container
    
    def _on_input_change(self, event):
        """Handle search input changes with debouncing"""
        if self.search_timer:
            self.search_timer.cancel()
        
        search_term = event.sender.value
        
        # Debounce search for 300ms
        self.search_timer = asyncio.create_task(self._debounced_search(search_term))
    
    async def _debounced_search(self, search_term: str):
        """Debounced search execution"""
        await asyncio.sleep(0.3)  # 300ms delay
        
        if search_term.strip():
            self._show_suggestions(search_term)
            self.on_search(search_term)
        else:
            self._hide_suggestions()
            self.on_search("")
    
    def _on_focus(self, event):
        """Show suggestions when focused"""
        if self.search_input.value.strip():
            self._show_suggestions(self.search_input.value)
    
    def _on_blur(self, event):
        """Hide suggestions when unfocused (with delay for click handling)"""
        # Small delay to allow clicking on suggestions
        asyncio.create_task(self._delayed_hide_suggestions())
    
    async def _delayed_hide_suggestions(self):
        """Hide suggestions after a short delay"""
        await asyncio.sleep(0.2)
        self._hide_suggestions()
    
    def _show_suggestions(self, search_term: str):
        """Show search suggestions"""
        self.suggestions_container.classes(remove='hidden')
        self._update_suggestions(search_term)
    
    def _hide_suggestions(self):
        """Hide search suggestions"""
        self.suggestions_container.classes(add='hidden')
    
    def _clear_search(self):
        """Clear the search input"""
        self.search_input.value = ""
        self._hide_suggestions()
        self.on_search("")
    
    def _update_suggestions(self, search_term: str):
        """Update suggestion content based on search term"""
        self.suggestions_container.clear()
        
        with self.suggestions_container:
            with ui.card().classes(f'{self.theme["card"]} rounded-xl shadow-lg border {self.theme["border"]} p-4'):
                # Sample suggestions (in production, these would come from a database)
                suggestions = self._get_suggestions(search_term.lower())
                
                if suggestions:
                    for category, items in suggestions.items():
                        if items:
                            ui.html(f'<h4 class="text-sm font-semibold {self.theme["text_primary"]} mb-2 opacity-75">{category}</h4>')
                            
                            for item in items[:3]:  # Limit to 3 items per category
                                with ui.button(
                                    on_click=lambda text=item: self._select_suggestion(text)
                                ).classes(f'{self.theme["button_ghost"]} w-full justify-start p-3 rounded-lg mb-1'):
                                    with ui.row().classes('items-center gap-3'):
                                        icon = self._get_suggestion_icon(category)
                                        ui.html(f'<span class="text-lg">{icon}</span>')
                                        ui.html(f'<span class="text-sm">{item}</span>')
                else:
                    ui.html(f'<p class="text-center {self.theme["text_muted"]} py-4">No suggestions found for "{search_term}"</p>')
    
    def _get_suggestions(self, search_term: str) -> Dict[str, List[str]]:
        """Get suggestions based on search term (mock data)"""
        # In production, this would query the database
        all_suggestions = {
            "Cuisines": ["Italian", "Mexican", "Asian", "Mediterranean", "Indian", "Thai", "Chinese", "Japanese"],
            "Ingredients": ["Chicken", "Beef", "Salmon", "Pasta", "Rice", "Tomatoes", "Garlic", "Onions", "Cheese"],
            "Cooking Methods": ["Grilled", "Baked", "Fried", "Roasted", "Steamed", "Sautéed", "Braised"],
            "Dietary": ["Vegetarian", "Vegan", "Gluten-Free", "Keto", "Low-Carb", "High-Protein"]
        }
        
        # Filter suggestions based on search term
        filtered_suggestions = {}
        for category, items in all_suggestions.items():
            matching_items = [item for item in items if search_term in item.lower()]
            if matching_items:
                filtered_suggestions[category] = matching_items
        
        return filtered_suggestions
    
    def _get_suggestion_icon(self, category: str) -> str:
        """Get icon for suggestion category"""
        icons = {
            "Cuisines": "🌍",
            "Ingredients": "🥬",
            "Cooking Methods": "🔥",
            "Dietary": "🥗"
        }
        return icons.get(category, "🔍")
    
    def _select_suggestion(self, suggestion: str):
        """Handle suggestion selection"""
        self.search_input.value = suggestion
        self._hide_suggestions()
        self.on_search(suggestion)

class AdvancedFilterPanel:
    """Advanced filtering panel with multiple filter options"""
    
    def __init__(self, theme: Dict[str, str], on_filter_change: Callable[[Dict], None]):
        self.theme = theme
        self.on_filter_change = on_filter_change
        self.filters = {
            "cuisine": [],
            "dietary": [],
            "cooking_time": None,
            "difficulty": None,
            "rating": None
        }
        
    def create_filter_panel(self) -> ui.column:
        """Create the advanced filter panel"""
        with ui.column().classes('w-full') as container:
            # Filter header
            with ui.row().classes('items-center justify-between mb-6'):
                ui.html(f'<h3 class="text-lg font-bold {self.theme["text_primary"]} flex items-center gap-2"><span class="text-xl">🎛️</span> Advanced Filters</h3>')
                ui.button(
                    'Clear All',
                    on_click=self._clear_all_filters
                ).classes(f'{self.theme["button_ghost"]} text-sm px-4 py-2 rounded-lg')
            
            # Cuisine filters
            self._create_cuisine_filters()
            
            # Dietary filters
            self._create_dietary_filters()
            
            # Time and difficulty filters
            with ui.row().classes('gap-6 w-full'):
                self._create_time_filter()
                self._create_difficulty_filter()
            
            # Rating filter
            self._create_rating_filter()
        
        return container
    
    def _create_cuisine_filters(self):
        """Create cuisine filter checkboxes"""
        with ui.column().classes('mb-6'):
            ui.html(f'<h4 class="text-sm font-semibold {self.theme["text_primary"]} mb-3 flex items-center gap-2"><span>🌍</span> Cuisine Type</h4>')
            
            cuisines = ["Italian", "Mexican", "Asian", "Mediterranean", "Indian", "American"]
            
            with ui.row().classes('gap-3 flex-wrap'):
                for cuisine in cuisines:
                    checkbox = ui.checkbox(cuisine).classes('text-sm')
                    checkbox.on('update:model-value', lambda value, c=cuisine: self._update_cuisine_filter(c, value))
    
    def _create_dietary_filters(self):
        """Create dietary restriction filters"""
        with ui.column().classes('mb-6'):
            ui.html(f'<h4 class="text-sm font-semibold {self.theme["text_primary"]} mb-3 flex items-center gap-2"><span>🥗</span> Dietary Options</h4>')
            
            dietary_options = ["Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Keto", "Low-Carb"]
            
            with ui.row().classes('gap-3 flex-wrap'):
                for option in dietary_options:
                    checkbox = ui.checkbox(option).classes('text-sm')
                    checkbox.on('update:model-value', lambda value, opt=option: self._update_dietary_filter(opt, value))
    
    def _create_time_filter(self):
        """Create cooking time filter"""
        with ui.column().classes('flex-1'):
            ui.html(f'<h4 class="text-sm font-semibold {self.theme["text_primary"]} mb-3 flex items-center gap-2"><span>⏱️</span> Cooking Time</h4>')
            
            time_options = [
                ("quick", "Under 30 mins"),
                ("medium", "30-60 mins"),
                ("long", "Over 1 hour")
            ]
            
            with ui.column().classes('gap-2'):
                for value, label in time_options:
                    radio = ui.radio([value], value=None).classes('text-sm').props(f'label="{label}"')
                    radio.on('update:model-value', lambda val: self._update_time_filter(val))
    
    def _create_difficulty_filter(self):
        """Create difficulty filter"""
        with ui.column().classes('flex-1'):
            ui.html(f'<h4 class="text-sm font-semibold {self.theme["text_primary"]} mb-3 flex items-center gap-2"><span>👨‍🍳</span> Difficulty</h4>')
            
            difficulty_options = [
                ("easy", "Easy"),
                ("medium", "Medium"),
                ("hard", "Advanced")
            ]
            
            with ui.column().classes('gap-2'):
                for value, label in difficulty_options:
                    radio = ui.radio([value], value=None).classes('text-sm').props(f'label="{label}"')
                    radio.on('update:model-value', lambda val: self._update_difficulty_filter(val))
    
    def _create_rating_filter(self):
        """Create rating filter"""
        with ui.column().classes('mb-6'):
            ui.html(f'<h4 class="text-sm font-semibold {self.theme["text_primary"]} mb-3 flex items-center gap-2"><span>⭐</span> Minimum Rating</h4>')
            
            with ui.row().classes('gap-2'):
                for i in range(1, 6):
                    star_btn = ui.button(
                        '⭐' * i,
                        on_click=lambda rating=i: self._update_rating_filter(rating)
                    ).classes(f'{self.theme["button_ghost"]} px-3 py-2 rounded-lg text-sm')
    
    def _update_cuisine_filter(self, cuisine: str, checked: bool):
        """Update cuisine filter"""
        if checked and cuisine not in self.filters["cuisine"]:
            self.filters["cuisine"].append(cuisine)
        elif not checked and cuisine in self.filters["cuisine"]:
            self.filters["cuisine"].remove(cuisine)
        self._emit_filter_change()
    
    def _update_dietary_filter(self, dietary: str, checked: bool):
        """Update dietary filter"""
        if checked and dietary not in self.filters["dietary"]:
            self.filters["dietary"].append(dietary)
        elif not checked and dietary in self.filters["dietary"]:
            self.filters["dietary"].remove(dietary)
        self._emit_filter_change()
    
    def _update_time_filter(self, time_range: str):
        """Update time filter"""
        self.filters["cooking_time"] = time_range
        self._emit_filter_change()
    
    def _update_difficulty_filter(self, difficulty: str):
        """Update difficulty filter"""
        self.filters["difficulty"] = difficulty
        self._emit_filter_change()
    
    def _update_rating_filter(self, rating: int):
        """Update rating filter"""
        self.filters["rating"] = rating
        self._emit_filter_change()
    
    def _clear_all_filters(self):
        """Clear all filters"""
        self.filters = {
            "cuisine": [],
            "dietary": [],
            "cooking_time": None,
            "difficulty": None,
            "rating": None
        }
        self._emit_filter_change()
        ui.notify('All filters cleared', type='info')
    
    def _emit_filter_change(self):
        """Emit filter change event"""
        self.on_filter_change(self.filters.copy())

class QuickFilters:
    """Quick filter buttons for common filtering scenarios"""
    
    def __init__(self, theme: Dict[str, str], on_quick_filter: Callable[[str], None]):
        self.theme = theme
        self.on_quick_filter = on_quick_filter
        
    def create_quick_filters(self) -> ui.row:
        """Create quick filter buttons"""
        with ui.row().classes('gap-3 flex-wrap') as container:
            quick_filters = [
                {"label": "🔥 Trending", "value": "trending"},
                {"label": "⚡ Quick (< 30min)", "value": "quick"},
                {"label": "🥗 Healthy", "value": "healthy"},
                {"label": "🌱 Vegetarian", "value": "vegetarian"},
                {"label": "🍖 High Protein", "value": "protein"},
                {"label": "🌍 International", "value": "international"}
            ]
            
            for filter_option in quick_filters:
                ui.button(
                    filter_option["label"],
                    on_click=lambda val=filter_option["value"]: self.on_quick_filter(val)
                ).classes(f'{self.theme["chip_bg"]} rounded-full px-4 py-2 text-sm font-medium border {self.theme["border"]} transition-all duration-200 hover:scale-105')
        
        return container