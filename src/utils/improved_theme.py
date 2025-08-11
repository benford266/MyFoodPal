"""
Improved theme system for FoodPal
Simplified, performant, and consistent design tokens
"""

from nicegui import ui
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum
import os

class ThemeMode(Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"

@dataclass
class ColorPalette:
    """Structured color palette for consistent theming"""
    # Primary colors
    primary_50: str
    primary_100: str
    primary_200: str
    primary_300: str
    primary_400: str
    primary_500: str
    primary_600: str
    primary_700: str
    primary_800: str
    primary_900: str
    
    # Neutral colors
    neutral_50: str
    neutral_100: str
    neutral_200: str
    neutral_300: str
    neutral_400: str
    neutral_500: str
    neutral_600: str
    neutral_700: str
    neutral_800: str
    neutral_900: str
    
    # Semantic colors
    success: str
    warning: str
    error: str
    info: str

# Define color palettes
LIGHT_PALETTE = ColorPalette(
    # Emerald primary colors
    primary_50="#ecfdf5",
    primary_100="#d1fae5",
    primary_200="#a7f3d0",
    primary_300="#6ee7b7", 
    primary_400="#34d399",
    primary_500="#10b981",
    primary_600="#059669",
    primary_700="#047857",
    primary_800="#065f46",
    primary_900="#064e3b",
    
    # Light neutral colors
    neutral_50="#f9fafb",
    neutral_100="#f3f4f6",
    neutral_200="#e5e7eb",
    neutral_300="#d1d5db",
    neutral_400="#9ca3af",
    neutral_500="#6b7280",
    neutral_600="#4b5563",
    neutral_700="#374151",
    neutral_800="#1f2937",
    neutral_900="#111827",
    
    # Semantic colors
    success="#10b981",
    warning="#f59e0b", 
    error="#ef4444",
    info="#3b82f6"
)

DARK_PALETTE = ColorPalette(
    # Emerald primary colors (slightly adjusted for dark mode)
    primary_50="#064e3b",
    primary_100="#047857",
    primary_200="#065f46",
    primary_300="#059669",
    primary_400="#10b981",
    primary_500="#34d399",
    primary_600="#6ee7b7",
    primary_700="#a7f3d0", 
    primary_800="#d1fae5",
    primary_900="#ecfdf5",
    
    # Dark neutral colors
    neutral_50="#111827",
    neutral_100="#1f2937",
    neutral_200="#374151",
    neutral_300="#4b5563",
    neutral_400="#6b7280",
    neutral_500="#9ca3af",
    neutral_600="#d1d5db",
    neutral_700="#e5e7eb",
    neutral_800="#f3f4f6",
    neutral_900="#f9fafb",
    
    # Semantic colors (adjusted for dark mode)
    success="#34d399",
    warning="#fbbf24",
    error="#f87171", 
    info="#60a5fa"
)

class ImprovedThemeManager:
    """Improved theme manager with better performance and maintainability"""
    
    _instance: Optional['ImprovedThemeManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.mode = self._get_initial_mode()
            self.palette = DARK_PALETTE if self.mode == ThemeMode.DARK else LIGHT_PALETTE
            self.initialized = True
    
    def _get_initial_mode(self) -> ThemeMode:
        """Get initial theme mode from environment or default"""
        env_mode = os.getenv('FOODPAL_THEME_MODE', 'light').lower()
        if env_mode == 'dark':
            return ThemeMode.DARK
        elif env_mode == 'auto':
            return ThemeMode.AUTO
        else:
            return ThemeMode.LIGHT
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        if self.mode == ThemeMode.LIGHT:
            self.mode = ThemeMode.DARK
            self.palette = DARK_PALETTE
        else:
            self.mode = ThemeMode.LIGHT
            self.palette = LIGHT_PALETTE
        
        self.apply_theme()
        ui.notify(f'Switched to {self.mode.value} theme', type='info')
    
    def set_theme(self, mode: ThemeMode):
        """Set specific theme mode"""
        if mode != self.mode:
            self.mode = mode
            self.palette = DARK_PALETTE if mode == ThemeMode.DARK else LIGHT_PALETTE
            self.apply_theme()
    
    def apply_theme(self):
        """Apply optimized theme CSS"""
        is_dark = self.mode == ThemeMode.DARK
        
        theme_css = f'''
        <style>
        :root {{
            /* Color variables */
            --color-primary-50: {self.palette.primary_50};
            --color-primary-100: {self.palette.primary_100};
            --color-primary-200: {self.palette.primary_200};
            --color-primary-300: {self.palette.primary_300};
            --color-primary-400: {self.palette.primary_400};
            --color-primary-500: {self.palette.primary_500};
            --color-primary-600: {self.palette.primary_600};
            --color-primary-700: {self.palette.primary_700};
            --color-primary-800: {self.palette.primary_800};
            --color-primary-900: {self.palette.primary_900};
            
            --color-neutral-50: {self.palette.neutral_50};
            --color-neutral-100: {self.palette.neutral_100};
            --color-neutral-200: {self.palette.neutral_200};
            --color-neutral-300: {self.palette.neutral_300};
            --color-neutral-400: {self.palette.neutral_400};
            --color-neutral-500: {self.palette.neutral_500};
            --color-neutral-600: {self.palette.neutral_600};
            --color-neutral-700: {self.palette.neutral_700};
            --color-neutral-800: {self.palette.neutral_800};
            --color-neutral-900: {self.palette.neutral_900};
            
            --color-success: {self.palette.success};
            --color-warning: {self.palette.warning};
            --color-error: {self.palette.error};
            --color-info: {self.palette.info};
            
            /* Design tokens */
            --border-radius-sm: 0.375rem;
            --border-radius-md: 0.5rem;
            --border-radius-lg: 0.75rem;
            --border-radius-xl: 1rem;
            --border-radius-2xl: 1.5rem;
            
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            
            --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
            --transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
            --transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1);
            
            /* Layout */
            --spacing-xs: 0.25rem;
            --spacing-sm: 0.5rem;
            --spacing-md: 1rem;
            --spacing-lg: 1.5rem;
            --spacing-xl: 2rem;
            --spacing-2xl: 3rem;
            
            color-scheme: {"dark" if is_dark else "light"};
        }}
        
        /* Base styles */
        * {{
            transition: background-color var(--transition-fast), 
                       border-color var(--transition-fast),
                       color var(--transition-fast),
                       box-shadow var(--transition-fast);
        }}
        
        /* Global text color fix for light theme */
        body {{
            color: var(--color-neutral-900);
        }}
        
        /* Ensure buttons inherit proper colors */
        button, .q-btn {{
            color: inherit;
        }}
        
        /* Improved focus styles */
        .focus-visible {{
            outline: 2px solid var(--color-primary-500);
            outline-offset: 2px;
        }}
        
        /* Touch targets */
        .touch-target {{
            min-height: 44px;
            min-width: 44px;
        }}
        
        /* Loading animation */
        @keyframes shimmer {{
            0% {{ background-position: -200px 0; }}
            100% {{ background-position: calc(200px + 100%) 0; }}
        }}
        
        .loading-shimmer {{
            background: linear-gradient(90deg, 
                var(--color-neutral-200) 25%, 
                var(--color-neutral-100) 50%, 
                var(--color-neutral-200) 75%);
            background-size: 200px 100%;
            animation: shimmer 1.5s infinite;
        }}
        
        /* Button hover effects */
        .button-interactive:hover {{
            transform: translateY(-1px);
            box-shadow: var(--shadow-lg);
        }}
        
        .button-interactive:active {{
            transform: translateY(0);
        }}
        
        /* Override NiceGUI default button styles */
        .nicegui-button.q-btn {{
            color: inherit !important;
        }}
        
        /* Specific button ghost styling with high specificity */
        .q-btn.button-ghost-override {{
            color: var(--color-neutral-700) !important;
            background-color: transparent !important;
            border: 1px solid transparent !important;
        }}
        
        .q-btn.button-ghost-override:hover {{
            color: var(--color-neutral-900) !important;
            background-color: var(--color-neutral-100) !important;
            border-color: var(--color-neutral-200) !important;
        }}
        
        /* Additional button override for general text color issues */
        .q-btn .q-btn__content {{
            color: inherit !important;
        }}
        
        /* Ultra-specific overrides for stubborn text color issues */
        .q-btn.button-ghost-override .q-btn__content,
        .q-btn.button-ghost-override .q-btn__content > span,
        .q-btn.button-ghost-override span {{
            color: var(--color-neutral-700) !important;
        }}
        
        .q-btn.button-ghost-override:hover .q-btn__content,
        .q-btn.button-ghost-override:hover .q-btn__content > span,
        .q-btn.button-ghost-override:hover span {{
            color: var(--color-neutral-900) !important;
        }}
        
        /* Card hover effects */
        .card-interactive:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-xl);
        }}
        
        /* Mobile responsiveness */
        @media (max-width: 768px) {{
            .mobile-stack {{ flex-direction: column !important; }}
            .mobile-full {{ width: 100% !important; }}
            .mobile-text-sm {{ font-size: 0.875rem !important; }}
            .mobile-p-4 {{ padding: 1rem !important; }}
            .mobile-padding {{
                padding-left: var(--spacing-md);
                padding-right: var(--spacing-md);
            }}
        }}
        
        @media (min-width: 768px) {{
            .mobile-padding {{
                padding-left: var(--spacing-xl);
                padding-right: var(--spacing-xl);
            }}
        }}
        
        /* Accessibility */
        @media (prefers-reduced-motion: reduce) {{
            *, *::before, *::after {{
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }}
        }}
        
        .sr-only {{
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }}
        </style>
        '''
        
        ui.add_head_html(theme_css)

def get_improved_theme_classes(force_dark: bool = None) -> Dict[str, str]:
    """Get optimized theme classes with CSS custom properties"""
    manager = get_improved_theme_manager()
    is_dark = force_dark if force_dark is not None else (manager.mode == ThemeMode.DARK)
    
    return {
        # Backgrounds
        'bg_primary': f'bg-[{manager.palette.neutral_50}]',
        'bg_secondary': f'bg-[{manager.palette.neutral_100}]/80 backdrop-blur-sm',
        'bg_surface': f'bg-[{manager.palette.neutral_50}]/90',
        'bg_accent': f'bg-[{manager.palette.primary_50}]',
        
        # Text
        'text_primary': f'text-[{manager.palette.neutral_900}]',
        'text_secondary': f'text-[{manager.palette.neutral_600}]',
        'text_muted': f'text-[{manager.palette.neutral_400}]',
        'gradient_text': f'bg-gradient-to-r from-[{manager.palette.primary_600}] to-[{manager.palette.primary_500}] bg-clip-text text-transparent',
        
        # Borders
        'border': f'border-[{manager.palette.neutral_200}]',
        'border_accent': f'border-[{manager.palette.primary_200}]',
        'divider': f'border-[{manager.palette.neutral_200}]',
        
        # Interactive elements
        'button_primary': f'bg-gradient-to-r from-[{manager.palette.primary_600}] to-[{manager.palette.primary_500}] hover:from-[{manager.palette.primary_700}] hover:to-[{manager.palette.primary_600}] text-white shadow-lg button-interactive',
        'button_secondary': f'bg-[{manager.palette.neutral_100}] hover:bg-[{manager.palette.neutral_200}] border border-[{manager.palette.neutral_300}] text-[{manager.palette.neutral_900}] button-interactive',
        'button_ghost': f'bg-transparent hover:bg-[{manager.palette.neutral_100}] text-[{manager.palette.neutral_700}] hover:text-[{manager.palette.neutral_900}] border border-transparent hover:border-[{manager.palette.neutral_200}] button-interactive button-ghost-override',
        
        # Cards
        'card': f'bg-[{manager.palette.neutral_50}]/90 backdrop-blur-sm border border-[{manager.palette.neutral_200}] shadow-md',
        'card_elevated': f'bg-[{manager.palette.neutral_50}]/95 backdrop-blur-sm border border-[{manager.palette.neutral_200}] shadow-lg',
        'card_interactive': f'bg-[{manager.palette.neutral_50}]/90 backdrop-blur-sm border border-[{manager.palette.neutral_200}] shadow-md hover:shadow-lg cursor-pointer card-interactive',
        
        # Form elements
        'input_bg': f'bg-[{manager.palette.neutral_50}] border-[{manager.palette.neutral_300}] text-[{manager.palette.neutral_900}] placeholder-[{manager.palette.neutral_400}] focus:border-[{manager.palette.primary_500}] focus:ring-2 focus:ring-[{manager.palette.primary_500}]/20',
        'textarea_bg': f'bg-[{manager.palette.neutral_50}] border-[{manager.palette.neutral_300}] text-[{manager.palette.neutral_900}] placeholder-[{manager.palette.neutral_400}] focus:border-[{manager.palette.primary_500}]',
        
        # Status colors
        'success_bg': f'bg-[{manager.palette.success}]/10 border-[{manager.palette.success}]/20',
        'success_text': f'text-[{manager.palette.success}]',
        'error_bg': f'bg-[{manager.palette.error}]/10 border-[{manager.palette.error}]/20',
        'error_text': f'text-[{manager.palette.error}]',
        'warning_bg': f'bg-[{manager.palette.warning}]/10 border-[{manager.palette.warning}]/20',
        'warning_text': f'text-[{manager.palette.warning}]',
        'info_bg': f'bg-[{manager.palette.info}]/10 border-[{manager.palette.info}]/20',
        'info_text': f'text-[{manager.palette.info}]',
        
        # Chips and badges
        'chip_bg': f'bg-[{manager.palette.neutral_100}] text-[{manager.palette.neutral_700}] border-[{manager.palette.neutral_200}] hover:bg-[{manager.palette.neutral_200}]',
        'badge_bg': f'bg-[{manager.palette.primary_100}] text-[{manager.palette.primary_700}] border-[{manager.palette.primary_200}]',
        
        # Navigation
        'nav_bg': f'bg-[{manager.palette.neutral_50}]/90 backdrop-blur-xl border-b border-[{manager.palette.neutral_200}] shadow-sm',
        'nav_item': f'text-[{manager.palette.neutral_600}] hover:text-[{manager.palette.primary_600}] hover:bg-[{manager.palette.primary_50}]',
        'nav_active': f'text-[{manager.palette.primary_600}] bg-[{manager.palette.primary_50}] border-[{manager.palette.primary_200}]'
    }

def get_improved_theme_manager() -> ImprovedThemeManager:
    """Get the singleton improved theme manager instance"""
    return ImprovedThemeManager()

# Utility functions for theme tokens
def get_color_token(color_name: str, shade: int = 500) -> str:
    """Get CSS custom property for a color token"""
    return f'var(--color-{color_name.replace("_", "-")}-{shade})'

def get_spacing_token(size: str) -> str:
    """Get CSS custom property for spacing token"""
    return f'var(--spacing-{size})'

def get_border_radius_token(size: str) -> str:
    """Get CSS custom property for border radius token"""
    return f'var(--border-radius-{size})'

def get_shadow_token(size: str) -> str:
    """Get CSS custom property for shadow token"""
    return f'var(--shadow-{size})'