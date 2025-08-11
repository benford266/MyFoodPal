from nicegui import ui, app
from typing import Dict, List, Optional, Callable
from ..utils.session import get_current_user, set_user_onboarding_step

class OnboardingSystem:
    """Comprehensive onboarding system for new users"""
    
    def __init__(self, theme: Dict[str, str]):
        self.theme = theme
    
    def create_welcome_tour(self, current_page: str = "home") -> None:
        """Create an interactive welcome tour for first-time users"""
        current_user = get_current_user()
        if not current_user or current_user.get('has_completed_onboarding', False):
            return
        
        # Tour steps based on current page
        tour_steps = self._get_tour_steps(current_page)
        
        # Create tour overlay
        self._create_tour_overlay(tour_steps)
    
    def _get_tour_steps(self, page: str) -> List[Dict]:
        """Get tour steps for the current page"""
        steps = {
            "home": [
                {
                    "title": "Welcome to MyFoodPal! 🍽️",
                    "content": "Let's take a quick tour to help you get started with creating amazing personalized recipes.",
                    "target": None,
                    "position": "center"
                },
                {
                    "title": "Your Food Preferences",
                    "content": "Start by telling us what foods you love and what you want to avoid. The more specific you are, the better your recipes will be!",
                    "target": ".preferences-panel",
                    "position": "right"
                },
                {
                    "title": "Recipe Generation",
                    "content": "Click here to generate 5 personalized recipes with AI-generated images and a smart shopping list.",
                    "target": ".generate-button",
                    "position": "top"
                },
                {
                    "title": "Background Generation",
                    "content": "Enable this to generate recipes in the background while you explore other features.",
                    "target": ".background-mode",
                    "position": "top"
                }
            ],
            "kitchen": [
                {
                    "title": "Your Kitchen Dashboard 🍳",
                    "content": "This is your culinary command center where you can manage ingredients and find recipe suggestions.",
                    "target": None,
                    "position": "center"
                },
                {
                    "title": "Search & Discover",
                    "content": "Use these tools to search for specific recipes or filter by dietary preferences and cooking time.",
                    "target": ".search-section",
                    "position": "bottom"
                },
                {
                    "title": "Kitchen Inventory",
                    "content": "Track your ingredients and get notified when items are expiring soon.",
                    "target": ".inventory-section",
                    "position": "right"
                }
            ],
            "history": [
                {
                    "title": "Meal Plan History 📋",
                    "content": "All your generated meal plans are saved here with your preferences and ratings.",
                    "target": None,
                    "position": "center"
                },
                {
                    "title": "Background Tasks",
                    "content": "Any recipes generating in the background will appear here with progress updates.",
                    "target": ".background-tasks",
                    "position": "bottom"
                }
            ]
        }
        return steps.get(page, [])
    
    def _create_tour_overlay(self, steps: List[Dict]) -> None:
        """Create the tour overlay with step-by-step guidance"""
        if not steps:
            return
        
        current_step = {'value': 0}
        
        # Create overlay container
        overlay = ui.html(f'''
            <div id="tour-overlay" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center" style="z-index: 9999;">
                <div id="tour-card" class="{self.theme["card_elevated"]} rounded-2xl p-8 max-w-md mx-4 relative">
                    <div id="tour-content"></div>
                </div>
            </div>
        ''')
        
        def show_step(step_index: int):
            if step_index >= len(steps):
                self._complete_tour()
                return
            
            step = steps[step_index]
            
            # Update tour content
            ui.html(f'''
                <script>
                const content = document.getElementById('tour-content');
                if (content) {{
                    content.innerHTML = `
                        <div class="text-center">
                            <h3 class="text-2xl font-bold {self.theme["text_primary"]} mb-4">{step["title"]}</h3>
                            <p class="text-lg {self.theme["text_secondary"]} mb-6">{step["content"]}</p>
                            <div class="flex items-center justify-between">
                                <div class="text-sm {self.theme["text_muted"]}">
                                    Step {step_index + 1} of {len(steps)}
                                </div>
                                <div class="flex gap-2">
                                    {f'<button onclick="skipTour()" class="{self.theme["button_ghost"]} px-4 py-2 rounded-lg">Skip</button>' if step_index == 0 else ''}
                                    {f'<button onclick="previousStep()" class="{self.theme["button_secondary"]} px-4 py-2 rounded-lg">Back</button>' if step_index > 0 else ''}
                                    <button onclick="nextStep()" class="{self.theme["button_primary"]} px-6 py-2 rounded-lg">
                                        {"Got it!" if step_index == len(steps) - 1 else "Next"}
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                }}
                
                // Position tour card near target element if specified
                {self._get_positioning_js(step) if step.get("target") else ''}
                </script>
            ''')
        
        # Add tour control functions
        ui.html('''
            <script>
            window.currentTourStep = 0;
            window.tourSteps = ''' + str(len(steps)) + ''';
            
            function nextStep() {
                window.currentTourStep++;
                if (window.currentTourStep >= window.tourSteps) {
                    completeTour();
                } else {
                    showTourStep(window.currentTourStep);
                }
            }
            
            function previousStep() {
                if (window.currentTourStep > 0) {
                    window.currentTourStep--;
                    showTourStep(window.currentTourStep);
                }
            }
            
            function skipTour() {
                completeTour();
            }
            
            function completeTour() {
                const overlay = document.getElementById('tour-overlay');
                if (overlay) {
                    overlay.remove();
                }
                // Mark tour as completed
                fetch('/api/user/complete-onboarding', { method: 'POST' });
            }
            
            function showTourStep(index) {
                // This will be dynamically updated by the show_step function
            }
            
            // Start the tour
            showTourStep(0);
            </script>
        ''')
        
        # Show first step
        show_step(0)
    
    def _get_positioning_js(self, step: Dict) -> str:
        """Generate JavaScript to position tour card near target element"""
        target = step.get("target", "")
        position = step.get("position", "center")
        
        return f'''
        const target = document.querySelector('{target}');
        const card = document.getElementById('tour-card');
        if (target && card) {{
            const rect = target.getBoundingClientRect();
            const cardRect = card.getBoundingClientRect();
            
            let top, left;
            
            switch('{position}') {{
                case 'top':
                    top = rect.top - cardRect.height - 20;
                    left = rect.left + (rect.width - cardRect.width) / 2;
                    break;
                case 'bottom':
                    top = rect.bottom + 20;
                    left = rect.left + (rect.width - cardRect.width) / 2;
                    break;
                case 'left':
                    top = rect.top + (rect.height - cardRect.height) / 2;
                    left = rect.left - cardRect.width - 20;
                    break;
                case 'right':
                    top = rect.top + (rect.height - cardRect.height) / 2;
                    left = rect.right + 20;
                    break;
                default:
                    top = '50%';
                    left = '50%';
                    card.style.transform = 'translate(-50%, -50%)';
            }}
            
            if (typeof top === 'number') {{
                card.style.position = 'fixed';
                card.style.top = Math.max(20, Math.min(window.innerHeight - cardRect.height - 20, top)) + 'px';
                card.style.left = Math.max(20, Math.min(window.innerWidth - cardRect.width - 20, left)) + 'px';
            }}
            
            // Highlight target element
            target.style.outline = '3px solid #10b981';
            target.style.outlineOffset = '4px';
            target.style.position = 'relative';
            target.style.zIndex = '9998';
        }}
        '''
    
    def _complete_tour(self):
        """Mark the tour as completed"""
        current_user = get_current_user()
        if current_user:
            set_user_onboarding_step(current_user['id'], 'completed')
    
    def create_feature_spotlight(
        self, 
        feature_name: str, 
        description: str, 
        target_selector: str,
        action_text: str = "Try it now",
        action_callback: Optional[Callable] = None
    ) -> None:
        """Create a spotlight overlay for highlighting new features"""
        ui.html(f'''
            <div class="fixed inset-0 bg-black bg-opacity-60 z-40 flex items-center justify-center" style="z-index: 9998;">
                <div class="{self.theme["card_elevated"]} rounded-2xl p-8 max-w-lg mx-4 text-center">
                    <div class="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-full flex items-center justify-center text-3xl text-white mb-6 mx-auto">
                        ✨
                    </div>
                    <h3 class="text-2xl font-bold {self.theme["text_primary"]} mb-4">New Feature: {feature_name}</h3>
                    <p class="text-lg {self.theme["text_secondary"]} mb-6">{description}</p>
                    <div class="flex gap-3 justify-center">
                        <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                                class="{self.theme["button_ghost"]} px-4 py-2 rounded-lg">
                            Maybe Later
                        </button>
                        <button onclick="highlightFeature('{target_selector}'); this.parentElement.parentElement.parentElement.remove();" 
                                class="{self.theme["button_primary"]} px-6 py-2 rounded-lg">
                            {action_text}
                        </button>
                    </div>
                </div>
            </div>
            
            <script>
            function highlightFeature(selector) {{
                const element = document.querySelector(selector);
                if (element) {{
                    element.style.outline = '3px solid #10b981';
                    element.style.outlineOffset = '4px';
                    element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    
                    setTimeout(() => {{
                        element.style.outline = '';
                        element.style.outlineOffset = '';
                    }}, 3000);
                }}
            }}
            </script>
        ''')
    
    def create_quick_tips(self, page: str) -> None:
        """Create contextual quick tips for different pages"""
        tips = {
            "home": [
                "💡 Be specific with your preferences - mention cooking methods, spice levels, and cuisines you enjoy",
                "🔄 Try the background generation mode to create recipes while browsing other pages",
                "⭐ Rate your generated recipes to improve future recommendations"
            ],
            "kitchen": [
                "🔍 Use the search filters to find recipes that match your dietary restrictions",
                "📦 Keep your kitchen inventory updated to get better ingredient-based suggestions",
                "⏱️ Filter recipes by preparation time when you're in a hurry"
            ],
            "history": [
                "📋 Click on any meal plan to view detailed recipes and generate a shopping list PDF",
                "🔄 Background generation tasks will show progress updates here",
                "⭐ Your recipe ratings help improve future meal plan suggestions"
            ]
        }
        
        page_tips = tips.get(page, [])
        if not page_tips:
            return
        
        # Create collapsible tips panel
        with ui.card().classes(f'{self.theme["bg_surface"]} rounded-xl p-4 border {self.theme["border"]} mb-4'):
            tips_expanded = {'value': False}
            
            def toggle_tips():
                tips_expanded['value'] = not tips_expanded['value']
                tips_content.clear()
                
                if tips_expanded['value']:
                    with tips_content:
                        with ui.column().classes('gap-3 mt-4'):
                            for tip in page_tips:
                                with ui.row().classes('items-start gap-3'):
                                    ui.html(f'<span class="text-lg mt-0.5">{tip.split()[0]}</span>')
                                    ui.html(f'<p class="text-sm {self.theme["text_secondary"]} flex-1">{" ".join(tip.split()[1:])}</p>')
                    tips_button.text = "Hide Tips ▲"
                else:
                    tips_button.text = "Show Quick Tips ▼"
            
            with ui.row().classes('items-center justify-between w-full'):
                ui.html(f'<h4 class="text-sm font-semibold {self.theme["text_primary"]} flex items-center gap-2"><span>💡</span> Quick Tips</h4>')
                tips_button = ui.button(
                    "Show Quick Tips ▼",
                    on_click=toggle_tips
                ).classes(f'{self.theme["button_ghost"]} text-sm py-1 px-3 rounded-lg')
            
            tips_content = ui.column().classes('w-full')

def create_enhanced_empty_state(
    container,
    theme: Dict[str, str],
    state_type: str = "no_content",
    custom_config: Optional[Dict] = None
) -> None:
    """Create enhanced empty states with onboarding guidance"""
    
    empty_states = {
        "no_meal_plans": {
            "icon": "📋",
            "title": "Ready to Create Your First Meal Plan?",
            "subtitle": "Let's get you started with personalized recipes!",
            "description": "MyFoodPal creates customized meal plans based on your preferences. Each plan includes 5 recipes with shared ingredients for efficient shopping.",
            "primary_action": "Create First Meal Plan",
            "primary_callback": lambda: ui.navigate.to('/'),
            "steps": [
                "🎯 Tell us your food preferences",
                "🧠 AI generates personalized recipes", 
                "🛒 Get an optimized shopping list",
                "⭐ Rate recipes to improve recommendations"
            ]
        },
        "no_search_results": {
            "icon": "🔍",
            "title": "No Recipes Found",
            "subtitle": "Let's help you discover something delicious",
            "description": "Try adjusting your search terms or filters. You can also generate new recipes based on your preferences.",
            "primary_action": "Generate New Recipes",
            "primary_callback": lambda: ui.navigate.to('/'),
            "secondary_action": "Clear Filters",
            "tips": [
                "Try broader search terms",
                "Check your dietary filters", 
                "Generate custom recipes instead"
            ]
        },
        "no_inventory": {
            "icon": "📦",
            "title": "Your Kitchen Inventory is Empty",
            "subtitle": "Track ingredients to get better recipe suggestions",
            "description": "Add items to your kitchen inventory to get personalized recipe recommendations based on what you have available.",
            "primary_action": "Add First Ingredient",
            "tips": [
                "Add items as you shop",
                "Set expiration dates for reminders",
                "Get recipes based on available ingredients"
            ]
        }
    }
    
    config = empty_states.get(state_type, empty_states["no_meal_plans"])
    if custom_config:
        config.update(custom_config)
    
    container.clear()
    
    with container:
        with ui.card().classes(f'{theme["card_elevated"]} rounded-2xl p-8 lg:p-16 text-center border {theme["border"]}'):
            # Icon
            ui.html(f'''
                <div class="w-24 lg:w-32 h-24 lg:h-32 bg-gradient-to-br from-emerald-100 to-teal-100 rounded-full flex items-center justify-center text-5xl lg:text-6xl mb-6 lg:mb-8 mx-auto">
                    {config["icon"]}
                </div>
            ''')
            
            # Content
            ui.html(f'<h2 class="text-2xl lg:text-3xl font-bold {theme["text_primary"]} mb-2 lg:mb-4">{config["title"]}</h2>')
            ui.html(f'<h3 class="text-lg lg:text-xl {theme["gradient_text"]} font-semibold mb-4 lg:mb-6">{config["subtitle"]}</h3>')
            ui.html(f'<p class="text-base lg:text-lg {theme["text_secondary"]} mb-6 lg:mb-8 max-w-2xl mx-auto">{config["description"]}</p>')
            
            # Steps or tips
            if config.get("steps"):
                with ui.row().classes('gap-4 lg:gap-6 justify-center mb-6 lg:mb-8 flex-wrap'):
                    for i, step in enumerate(config["steps"], 1):
                        with ui.column().classes('items-center text-center max-w-40'):
                            ui.html(f'''
                                <div class="w-8 h-8 bg-gradient-to-br from-emerald-500 to-teal-600 text-white rounded-full flex items-center justify-center text-sm font-bold mb-2">
                                    {i}
                                </div>
                            ''')
                            ui.html(f'<p class="text-sm {theme["text_secondary"]}">{step}</p>')
            
            elif config.get("tips"):
                with ui.column().classes('gap-2 mb-6 lg:mb-8 text-left max-w-md mx-auto'):
                    ui.html(f'<h4 class="text-sm font-semibold {theme["text_primary"]} mb-3 text-center">💡 Helpful Tips:</h4>')
                    for tip in config["tips"]:
                        with ui.row().classes('items-start gap-2'):
                            ui.html('<div class="w-2 h-2 bg-emerald-400 rounded-full flex-shrink-0 mt-2"></div>')
                            ui.html(f'<p class="text-sm {theme["text_secondary"]} flex-1">{tip}</p>')
            
            # Action buttons
            with ui.row().classes('gap-3 lg:gap-4 justify-center flex-wrap'):
                if config.get("primary_callback"):
                    with ui.button(on_click=config["primary_callback"]).classes(f'{theme["button_primary"]} font-bold py-3 lg:py-4 px-6 lg:px-8 rounded-xl text-base lg:text-lg shadow-lg transition-all duration-300 hover:scale-105'):
                        with ui.row().classes('items-center gap-3'):
                            ui.html('<span class="text-xl">✨</span>')
                            ui.html(f'<span>{config["primary_action"]}</span>')
                
                if config.get("secondary_action") and config.get("secondary_callback"):
                    ui.button(
                        config["secondary_action"],
                        on_click=config["secondary_callback"]
                    ).classes(f'{theme["button_secondary"]} py-3 lg:py-4 px-6 lg:px-8 rounded-xl text-base lg:text-lg')