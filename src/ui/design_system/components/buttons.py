"""
Button Components

Comprehensive button system with consistent styling, accessibility, and interaction patterns.
"""

from nicegui import ui
from typing import Optional, Callable, Dict, Any, Literal
from ..tokens.colors import get_color_token, SEMANTIC_COLORS
from ..tokens.spacing import TOUCH_TARGETS
from ..tokens.animations import get_transition

ButtonVariant = Literal["primary", "secondary", "ghost", "danger", "success", "warning"]
ButtonSize = Literal["sm", "md", "lg", "xl"]

class Button:
    """
    Modern, accessible button component with consistent styling and behavior.
    
    Features:
    - Multiple variants (primary, secondary, ghost, danger, etc.)
    - Responsive sizing with proper touch targets
    - Loading states and disabled states
    - Full keyboard and screen reader accessibility
    - Smooth micro-interactions
    """
    
    # Button variant styles
    VARIANTS: Dict[ButtonVariant, Dict[str, str]] = {
        "primary": {
            "light": "bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white shadow-lg hover:shadow-emerald-500/25",
            "dark": "bg-gradient-to-r from-emerald-400 to-teal-500 hover:from-emerald-300 hover:to-teal-400 text-slate-900 shadow-lg hover:shadow-emerald-400/25"
        },
        "secondary": {
            "light": "bg-white hover:bg-slate-50 border-2 border-slate-300 hover:border-slate-400 text-slate-900 shadow-sm hover:shadow-md",
            "dark": "bg-slate-800 hover:bg-slate-700 border-2 border-slate-600 hover:border-slate-500 text-slate-100 shadow-sm hover:shadow-lg"
        },
        "ghost": {
            "light": "bg-transparent hover:bg-slate-100 text-slate-600 hover:text-slate-900",
            "dark": "bg-transparent hover:bg-slate-800 text-slate-300 hover:text-slate-100"
        },
        "danger": {
            "light": "bg-red-500 hover:bg-red-600 text-white shadow-lg hover:shadow-red-500/25",
            "dark": "bg-red-500 hover:bg-red-400 text-white shadow-lg hover:shadow-red-400/25"
        },
        "success": {
            "light": "bg-emerald-500 hover:bg-emerald-600 text-white shadow-lg hover:shadow-emerald-500/25",
            "dark": "bg-emerald-500 hover:bg-emerald-400 text-white shadow-lg hover:shadow-emerald-400/25"
        },
        "warning": {
            "light": "bg-amber-500 hover:bg-amber-600 text-white shadow-lg hover:shadow-amber-500/25",
            "dark": "bg-amber-500 hover:bg-amber-400 text-slate-900 shadow-lg hover:shadow-amber-400/25"
        }
    }
    
    # Button size configurations
    SIZES: Dict[ButtonSize, Dict[str, str]] = {
        "sm": {
            "padding": "px-3 py-1.5",
            "text": "text-sm",
            "min_size": TOUCH_TARGETS["minimum"],
            "icon_size": "w-4 h-4"
        },
        "md": {
            "padding": "px-4 py-2.5", 
            "text": "text-base",
            "min_size": TOUCH_TARGETS["recommended"],
            "icon_size": "w-5 h-5"
        },
        "lg": {
            "padding": "px-6 py-3.5",
            "text": "text-lg",
            "min_size": TOUCH_TARGETS["comfortable"],
            "icon_size": "w-6 h-6"
        },
        "xl": {
            "padding": "px-8 py-4.5",
            "text": "text-xl",
            "min_size": "min-h-[64px] min-w-[64px]",
            "icon_size": "w-8 h-8"
        }
    }
    
    def __init__(
        self,
        text: str,
        variant: ButtonVariant = "primary",
        size: ButtonSize = "md", 
        icon: Optional[str] = None,
        icon_position: Literal["left", "right"] = "left",
        disabled: bool = False,
        loading: bool = False,
        full_width: bool = False,
        on_click: Optional[Callable] = None,
        theme: str = "light",
        additional_classes: str = "",
        **props
    ):
        self.text = text
        self.variant = variant
        self.size = size
        self.icon = icon
        self.icon_position = icon_position
        self.disabled = disabled
        self.loading = loading
        self.full_width = full_width
        self.on_click = on_click
        self.theme = theme
        self.additional_classes = additional_classes
        self.props = props
        
        self.button_element = None
        
    def create(self) -> ui.button:
        """Create the button UI element with all styling and accessibility features."""
        
        # Build CSS classes
        variant_classes = self.VARIANTS[self.variant][self.theme]
        size_config = self.SIZES[self.size]
        
        base_classes = [
            # Base button styles
            "inline-flex items-center justify-center gap-2 rounded-xl font-medium",
            "transition-all duration-200 ease-out",
            "focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:ring-offset-2",
            "active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed",
            "select-none touch-manipulation",
            
            # Variant and size classes
            variant_classes,
            size_config["padding"],
            size_config["text"],
            size_config["min_size"],
            
            # Conditional classes
            "w-full" if self.full_width else "",
            "cursor-not-allowed opacity-50" if self.disabled or self.loading else "",
            self.additional_classes
        ]
        
        # Create button element
        self.button_element = ui.button(
            on_click=self._handle_click
        ).classes(" ".join(filter(None, base_classes)))
        
        # Add content
        with self.button_element:
            self._create_button_content()
        
        # Add accessibility attributes
        self._add_accessibility_attributes()
        
        # Add any additional props
        for key, value in self.props.items():
            self.button_element.props(f"{key}='{value}'")
            
        return self.button_element
    
    def _create_button_content(self):
        """Create the internal button content (text, icons, loading spinner)."""
        
        if self.loading:
            # Loading state with spinner
            with ui.row().classes("items-center gap-2"):
                ui.html(f'''
                    <svg class="animate-spin {self.SIZES[self.size]["icon_size"]} text-current" 
                         fill="none" viewBox="0 0 24 24" aria-hidden="true">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                ''')
                ui.html('<span class="sr-only">Loading...</span>')
                if self.text:
                    ui.html(f'<span>{self.text}</span>')
        else:
            # Normal state with optional icon
            with ui.row().classes("items-center gap-2"):
                # Left icon
                if self.icon and self.icon_position == "left":
                    self._create_icon()
                
                # Button text
                if self.text:
                    ui.html(f'<span>{self.text}</span>')
                
                # Right icon  
                if self.icon and self.icon_position == "right":
                    self._create_icon()
    
    def _create_icon(self):
        """Create button icon (emoji or Material Icon)."""
        icon_size = self.SIZES[self.size]["icon_size"]
        
        if self.icon.startswith(('material-icons', 'material-icons-outlined')):
            # Material Design icon
            icon_class, icon_name = self.icon.split(':') if ':' in self.icon else (self.icon, '')
            ui.html(f'<span class="{icon_class} {icon_size}" aria-hidden="true">{icon_name}</span>')
        else:
            # Emoji or other text icon
            ui.html(f'<span class="text-current {icon_size} flex items-center justify-center" aria-hidden="true">{self.icon}</span>')
    
    def _handle_click(self):
        """Handle button click with loading state and callback."""
        if self.disabled or self.loading:
            return
            
        if self.on_click:
            self.on_click()
    
    def _add_accessibility_attributes(self):
        """Add WCAG-compliant accessibility attributes."""
        if self.button_element:
            # Basic accessibility
            self.button_element.props(f'role="button"')
            self.button_element.props(f'type="button"')
            
            # Disabled state
            if self.disabled:
                self.button_element.props('disabled="true"')
                self.button_element.props('aria-disabled="true"')
            
            # Loading state
            if self.loading:
                self.button_element.props('aria-busy="true"')
                self.button_element.props('aria-live="polite"')
    
    def set_loading(self, loading: bool):
        """Update button loading state."""
        self.loading = loading
        if self.button_element:
            # Re-create content with new loading state
            self.button_element.clear()
            with self.button_element:
                self._create_button_content()
    
    def set_disabled(self, disabled: bool):
        """Update button disabled state."""
        self.disabled = disabled
        self._add_accessibility_attributes()


class IconButton(Button):
    """Icon-only button variant for compact interfaces."""
    
    def __init__(
        self,
        icon: str,
        variant: ButtonVariant = "ghost",
        size: ButtonSize = "md",
        tooltip: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            text="",
            variant=variant,
            size=size,
            icon=icon,
            **kwargs
        )
        self.tooltip = tooltip
    
    def create(self) -> ui.button:
        """Create icon button with proper accessibility."""
        button = super().create()
        
        # Make icon buttons square
        button.classes("aspect-square")
        
        # Add tooltip for accessibility
        if self.tooltip:
            button.tooltip(self.tooltip)
            button.props(f'aria-label="{self.tooltip}"')
        
        return button


class FloatingActionButton(Button):
    """
    Floating Action Button (FAB) for primary actions.
    
    Features:
    - Fixed positioning with z-index management
    - Smooth entrance animations
    - Mobile-optimized placement
    - Extended FAB variant with text label
    """
    
    def __init__(
        self,
        icon: str,
        text: Optional[str] = None,
        position: Literal["bottom-right", "bottom-left", "bottom-center"] = "bottom-right",
        extended: bool = False,
        **kwargs
    ):
        super().__init__(
            text=text if extended else "",
            variant="primary",
            size="lg",
            icon=icon,
            **kwargs
        )
        self.position = position
        self.extended = extended
    
    def create(self) -> ui.button:
        """Create floating action button with positioning."""
        
        # Position classes
        position_classes = {
            "bottom-right": "fixed bottom-6 right-6 md:bottom-8 md:right-8",
            "bottom-left": "fixed bottom-6 left-6 md:bottom-8 md:left-8", 
            "bottom-center": "fixed bottom-6 left-1/2 transform -translate-x-1/2 md:bottom-8"
        }
        
        # FAB-specific classes
        fab_classes = [
            position_classes[self.position],
            "z-50 shadow-2xl hover:shadow-3xl",
            "rounded-full" if not self.extended else "rounded-2xl",
            "animate-[slideInUp_300ms_ease-out]",
            "h-14 w-14" if not self.extended else "h-14"
        ]
        
        self.additional_classes = " ".join(fab_classes)
        
        button = super().create()
        
        # Add FAB-specific accessibility
        if not self.text:
            button.props('aria-label="Primary action"')
        
        return button

def create_button_group(
    buttons: list,
    orientation: Literal["horizontal", "vertical"] = "horizontal",
    spacing: str = "gap-2",
    theme: str = "light"
) -> ui.row:
    """
    Create a group of related buttons with consistent spacing.
    
    Args:
        buttons: List of Button instances
        orientation: Layout direction
        spacing: Gap between buttons
        theme: Theme for styling
        
    Returns:
        UI container with button group
    """
    container_class = "flex gap-2"
    if orientation == "vertical":
        container_class += " flex-col"
    else:
        container_class += " flex-row flex-wrap"
    
    with ui.row().classes(f"{container_class} {spacing}") as group:
        for button in buttons:
            if hasattr(button, 'create'):
                button.create()
            else:
                # Handle raw button elements
                group.add(button)
    
    return group