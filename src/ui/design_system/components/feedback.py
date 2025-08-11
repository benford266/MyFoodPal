"""
Feedback Components

Loading states, error handling, empty states, and progress indicators for better user experience.
"""

from nicegui import ui
from typing import Optional, Callable, Dict, Any, List, Literal
from ..tokens.animations import ANIMATION_CLASSES, get_transition

class LoadingState:
    """
    Comprehensive loading state components with various display options.
    
    Features:
    - Multiple loading patterns (spinner, skeleton, shimmer)
    - Progressive loading with meaningful messages
    - Staggered animations for list loading
    - Accessibility support with screen reader announcements
    """
    
    @staticmethod
    def spinner(
        size: Literal["sm", "md", "lg", "xl"] = "md",
        message: Optional[str] = None,
        theme: str = "light"
    ) -> ui.column:
        """Create animated spinner with optional message."""
        
        size_config = {
            "sm": {"spinner": "w-6 h-6", "text": "text-sm"},
            "md": {"spinner": "w-8 h-8", "text": "text-base"},
            "lg": {"spinner": "w-12 h-12", "text": "text-lg"},
            "xl": {"spinner": "w-16 h-16", "text": "text-xl"}
        }
        
        config = size_config[size]
        text_color = "text-slate-600" if theme == "light" else "text-slate-300"
        
        with ui.column().classes('items-center gap-4') as container:
            # Animated spinner
            ui.html(f'''
                <div class="{config["spinner"]} animate-spin">
                    <svg class="w-full h-full text-emerald-500" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                </div>
            ''')
            
            # Loading message
            if message:
                ui.html(f'<p class="{config["text"]} {text_color} font-medium text-center" role="status" aria-live="polite">{message}</p>')
        
        return container
    
    @staticmethod
    def skeleton_card(theme: str = "light") -> ui.card:
        """Create skeleton loading card."""
        
        skeleton_color = "bg-slate-200" if theme == "light" else "bg-slate-700"
        shimmer_class = ANIMATION_CLASSES["loading_shimmer"]
        
        with ui.card().classes(f'p-6 w-full {"bg-white border border-slate-200" if theme == "light" else "bg-slate-800 border border-slate-700"}') as skeleton:
            # Image skeleton
            ui.html(f'''
                <div class="{skeleton_color} {shimmer_class} h-48 w-full rounded-lg mb-4"></div>
            ''')
            
            # Header skeleton
            with ui.row().classes('items-center gap-4 mb-4'):
                ui.html(f'<div class="{skeleton_color} {shimmer_class} w-12 h-12 rounded-full"></div>')
                with ui.column().classes('flex-1 gap-2'):
                    ui.html(f'<div class="{skeleton_color} {shimmer_class} h-6 w-3/4 rounded"></div>')
                    ui.html(f'<div class="{skeleton_color} {shimmer_class} h-4 w-1/2 rounded"></div>')
            
            # Tags skeleton
            with ui.row().classes('gap-2 mb-6'):
                for i in range(3):
                    width = ["w-20", "w-16", "w-24"][i]
                    ui.html(f'<div class="{skeleton_color} {shimmer_class} h-6 {width} rounded-full"></div>')
            
            # Content skeleton
            with ui.row().classes('gap-8'):
                for _ in range(2):
                    with ui.column().classes('flex-1 gap-2'):
                        ui.html(f'<div class="{skeleton_color} {shimmer_class} h-5 w-32 rounded mb-4"></div>')
                        for _ in range(4):
                            ui.html(f'<div class="{skeleton_color} {shimmer_class} h-4 w-full rounded mb-2"></div>')
        
        return skeleton
    
    @staticmethod
    def skeleton_list(count: int = 3, theme: str = "light") -> ui.column:
        """Create skeleton loading list."""
        
        with ui.column().classes('gap-6 w-full') as container:
            for i in range(count):
                # Add staggered animation delay
                delay = i * 100  # 100ms delay between items
                LoadingState.skeleton_card(theme).style(f'animation-delay: {delay}ms;')
        
        return container
    
    @staticmethod
    def progress_bar(
        progress: float,
        message: Optional[str] = None,
        show_percentage: bool = True,
        theme: str = "light"
    ) -> ui.column:
        """Create progress bar with optional message."""
        
        progress_clamped = max(0, min(100, progress))
        bg_color = "bg-slate-200" if theme == "light" else "bg-slate-700"
        text_color = "text-slate-600" if theme == "light" else "text-slate-300"
        
        with ui.column().classes('w-full gap-3') as container:
            # Progress message
            if message:
                ui.html(f'<p class="text-lg font-semibold {text_color} text-center" role="status" aria-live="polite">{message}</p>')
            
            # Progress bar
            ui.html(f'''
                <div class="{bg_color} rounded-full h-3 overflow-hidden shadow-inner">
                    <div class="bg-gradient-to-r from-emerald-500 to-teal-600 h-full rounded-full transition-all duration-500 ease-out shadow-sm" 
                         style="width: {progress_clamped}%" 
                         role="progressbar" 
                         aria-valuenow="{progress_clamped}" 
                         aria-valuemin="0" 
                         aria-valuemax="100">
                    </div>
                </div>
            ''')
            
            # Percentage display
            if show_percentage:
                ui.html(f'<p class="text-sm {text_color} font-semibold text-center">{int(progress_clamped)}% Complete</p>')
        
        return container


class ErrorState:
    """
    User-friendly error states with recovery options.
    
    Features:
    - Contextual error messages
    - Recovery action buttons
    - Different severity levels
    - Accessibility support
    """
    
    ERROR_TYPES = {
        "network": {
            "icon": "🌐",
            "title": "Connection Problem",
            "default_message": "Unable to connect to our servers. Please check your internet connection.",
            "recovery_text": "Retry Connection"
        },
        "generation": {
            "icon": "🤖",
            "title": "Recipe Generation Failed", 
            "default_message": "We couldn't generate your recipes right now. Please try again.",
            "recovery_text": "Try Again"
        },
        "auth": {
            "icon": "🔐",
            "title": "Authentication Required",
            "default_message": "Please sign in to access this feature.",
            "recovery_text": "Sign In"
        },
        "not_found": {
            "icon": "🔍",
            "title": "Content Not Found",
            "default_message": "The requested content could not be found.",
            "recovery_text": "Go Back"
        },
        "generic": {
            "icon": "⚠️",
            "title": "Something Went Wrong",
            "default_message": "An unexpected error occurred. Please try again.",
            "recovery_text": "Retry"
        }
    }
    
    @staticmethod
    def create(
        error_type: Literal["network", "generation", "auth", "not_found", "generic"] = "generic",
        title: Optional[str] = None,
        message: Optional[str] = None,
        recovery_callback: Optional[Callable] = None,
        theme: str = "light"
    ) -> ui.column:
        """Create error state with recovery options."""
        
        error_config = ErrorState.ERROR_TYPES[error_type]
        final_title = title or error_config["title"]
        final_message = message or error_config["default_message"]
        
        bg_color = "bg-red-50 border-red-200" if theme == "light" else "bg-red-900/20 border-red-800/30"
        text_primary = "text-red-800" if theme == "light" else "text-red-200"
        text_secondary = "text-red-600" if theme == "light" else "text-red-300"
        
        with ui.column().classes(f'items-center text-center p-12 rounded-2xl border {bg_color} max-w-md mx-auto') as container:
            # Error icon
            ui.html(f'''
                <div class="w-20 h-20 bg-red-100 dark:bg-red-900/40 rounded-full flex items-center justify-center text-4xl mb-6 shadow-lg">
                    {error_config["icon"]}
                </div>
            ''')
            
            # Error content
            ui.html(f'<h3 class="text-2xl font-bold {text_primary} mb-3" role="alert">{final_title}</h3>')
            ui.html(f'<p class="text-lg {text_secondary} mb-8 leading-relaxed">{final_message}</p>')
            
            # Recovery actions
            with ui.row().classes('gap-4 justify-center flex-wrap'):
                if recovery_callback:
                    from .buttons import Button
                    retry_btn = Button(
                        text=error_config["recovery_text"],
                        variant="primary",
                        icon="🔄",
                        on_click=recovery_callback,
                        theme=theme
                    )
                    retry_btn.create()
                
                # Always provide a back button
                back_btn = Button(
                    text="Go Back",
                    variant="secondary", 
                    icon="←",
                    on_click=lambda: ui.navigate.back(),
                    theme=theme
                )
                back_btn.create()
        
        return container


class EmptyState:
    """
    Engaging empty states that guide user actions.
    
    Features:
    - Contextual illustrations and messages
    - Clear call-to-action buttons
    - Onboarding guidance for new users
    - Multiple preset configurations
    """
    
    EMPTY_STATES = {
        "no_recipes": {
            "icon": "🍽️",
            "title": "No Recipes Yet",
            "message": "Create your first personalized meal plan to get started with delicious recipes.",
            "action_text": "Generate Recipes",
            "gradient": "from-emerald-100 to-teal-100"
        },
        "no_meal_plans": {
            "icon": "📋",
            "title": "Your Recipe Collection Awaits",
            "message": "Generate your first meal plan and we'll save it here for easy access.",
            "action_text": "Create First Plan",
            "gradient": "from-blue-100 to-indigo-100"
        },
        "no_search_results": {
            "icon": "🔍", 
            "title": "No Results Found",
            "message": "Try adjusting your search filters or terms to find what you're looking for.",
            "action_text": "Clear Filters",
            "gradient": "from-amber-100 to-orange-100"
        },
        "no_inventory": {
            "icon": "📦",
            "title": "Kitchen Inventory Empty",
            "message": "Add ingredients to your kitchen inventory to get personalized recipe suggestions.",
            "action_text": "Add Ingredients",
            "gradient": "from-purple-100 to-pink-100"
        }
    }
    
    @staticmethod
    def create(
        state_type: Literal["no_recipes", "no_meal_plans", "no_search_results", "no_inventory"],
        title: Optional[str] = None,
        message: Optional[str] = None,
        action_text: Optional[str] = None,
        action_callback: Optional[Callable] = None,
        theme: str = "light"
    ) -> ui.column:
        """Create engaging empty state with clear next steps."""
        
        state_config = EmptyState.EMPTY_STATES[state_type]
        final_title = title or state_config["title"]
        final_message = message or state_config["message"]
        final_action_text = action_text or state_config["action_text"]
        
        text_primary = "text-slate-900" if theme == "light" else "text-slate-100"
        text_secondary = "text-slate-600" if theme == "light" else "text-slate-400"
        
        with ui.column().classes('items-center text-center p-16 max-w-2xl mx-auto') as container:
            # Illustration
            ui.html(f'''
                <div class="w-32 h-32 bg-gradient-to-br {state_config["gradient"]} rounded-full flex items-center justify-center text-6xl mb-8 shadow-lg">
                    {state_config["icon"]}
                </div>
            ''')
            
            # Content
            ui.html(f'<h2 class="text-3xl font-bold {text_primary} mb-4">{final_title}</h2>')
            ui.html(f'<p class="text-lg {text_secondary} mb-8 leading-relaxed max-w-lg">{final_message}</p>')
            
            # Action button
            if action_callback:
                from .buttons import Button
                action_btn = Button(
                    text=final_action_text,
                    variant="primary",
                    size="lg",
                    icon="✨",
                    on_click=action_callback,
                    theme=theme
                )
                action_btn.create()
        
        return container


class ProgressIndicator:
    """
    Multi-step progress indicators for complex workflows.
    
    Features:
    - Step-by-step progress visualization
    - Current step highlighting
    - Estimated time remaining
    - Accessibility support
    """
    
    @staticmethod
    def create_stepper(
        steps: List[Dict[str, Any]],
        current_step: int,
        theme: str = "light"
    ) -> ui.column:
        """Create step-by-step progress indicator."""
        
        primary_color = "text-emerald-600 bg-emerald-100 border-emerald-300" if theme == "light" else "text-emerald-400 bg-emerald-900/30 border-emerald-500/50"
        completed_color = "text-emerald-700 bg-emerald-200 border-emerald-400" if theme == "light" else "text-emerald-300 bg-emerald-800/40 border-emerald-400/60"
        inactive_color = "text-slate-500 bg-slate-100 border-slate-200" if theme == "light" else "text-slate-400 bg-slate-800 border-slate-600"
        
        with ui.column().classes('w-full') as container:
            for i, step in enumerate(steps):
                is_current = i == current_step
                is_completed = i < current_step
                
                # Determine step styling
                if is_completed:
                    step_classes = completed_color
                    icon = "✓"
                elif is_current:
                    step_classes = primary_color
                    icon = str(i + 1)
                else:
                    step_classes = inactive_color
                    icon = str(i + 1)
                
                with ui.row().classes('items-center gap-4 mb-4'):
                    # Step number/checkmark
                    ui.html(f'''
                        <div class="w-10 h-10 rounded-full border-2 {step_classes} flex items-center justify-center font-bold text-sm">
                            {icon}
                        </div>
                    ''')
                    
                    # Step content
                    with ui.column().classes('flex-1'):
                        step_title_class = "text-slate-900 font-semibold" if theme == "light" else "text-slate-100 font-semibold"
                        step_desc_class = "text-slate-600 text-sm" if theme == "light" else "text-slate-400 text-sm"
                        
                        ui.html(f'<h4 class="{step_title_class}">{step.get("title", f"Step {i + 1}")}</h4>')
                        if step.get("description"):
                            ui.html(f'<p class="{step_desc_class}">{step["description"]}</p>')
                
                # Progress line (except for last step)
                if i < len(steps) - 1:
                    line_color = completed_color.split()[2] if is_completed else inactive_color.split()[2]  # Extract border color
                    ui.html(f'<div class="w-0.5 h-8 {line_color.replace("border-", "bg-")} ml-5 mb-2"></div>')
        
        return container
    
    @staticmethod
    def create_circular(
        progress: float,
        size: Literal["sm", "md", "lg"] = "md",
        show_percentage: bool = True,
        label: Optional[str] = None,
        theme: str = "light"
    ) -> ui.column:
        """Create circular progress indicator."""
        
        size_config = {
            "sm": {"diameter": "w-16 h-16", "stroke": "4", "text": "text-xs"},
            "md": {"diameter": "w-24 h-24", "stroke": "6", "text": "text-sm"},
            "lg": {"diameter": "w-32 h-32", "stroke": "8", "text": "text-base"}
        }
        
        config = size_config[size]
        progress_clamped = max(0, min(100, progress))
        circumference = 2 * 3.14159 * 45  # radius of 45
        stroke_dasharray = circumference
        stroke_dashoffset = circumference - (progress_clamped / 100) * circumference
        
        text_color = "text-slate-900" if theme == "light" else "text-slate-100"
        
        with ui.column().classes('items-center gap-3') as container:
            # Circular progress
            ui.html(f'''
                <div class="{config["diameter"]} relative">
                    <svg class="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                        <!-- Background circle -->
                        <circle cx="50" cy="50" r="45" 
                                fill="none" 
                                stroke="{"#e2e8f0" if theme == "light" else "#475569"}" 
                                stroke-width="{config["stroke"]}" />
                        <!-- Progress circle -->
                        <circle cx="50" cy="50" r="45" 
                                fill="none" 
                                stroke="url(#gradient-progress)" 
                                stroke-width="{config["stroke"]}"
                                stroke-linecap="round"
                                stroke-dasharray="{stroke_dasharray}"
                                stroke-dashoffset="{stroke_dashoffset}"
                                style="transition: stroke-dashoffset 0.5s ease-in-out;" />
                        <!-- Gradient definition -->
                        <defs>
                            <linearGradient id="gradient-progress" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" style="stop-color:#10b981;stop-opacity:1" />
                                <stop offset="100%" style="stop-color:#14b8a6;stop-opacity:1" />
                            </linearGradient>
                        </defs>
                    </svg>
                    {"" if not show_percentage else f'''
                    <div class="absolute inset-0 flex items-center justify-center">
                        <span class="{config["text"]} font-bold {text_color}">{int(progress_clamped)}%</span>
                    </div>
                    '''}
                </div>
            ''')
            
            # Label
            if label:
                ui.html(f'<p class="text-sm {text_color} font-medium text-center">{label}</p>')
        
        return container