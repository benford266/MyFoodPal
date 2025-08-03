from nicegui import ui, app
from typing import Dict, Optional
import os

class ThemeManager:
    _instance: Optional['ThemeManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.is_dark = self.get_system_theme()
            self.initialized = True
    
    def get_system_theme(self) -> bool:
        """Detect system theme preference from environment or default"""
        return os.getenv('FOODPAL_DARK_MODE', 'false').lower() == 'true'
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self.is_dark = not self.is_dark
        self.apply_theme()
        # Trigger a UI refresh
        ui.notify(f'Switched to {"dark" if self.is_dark else "light"} mode', type='info')
    
    def apply_theme(self):
        """Apply comprehensive theme to the UI"""
        # Add modern CSS custom properties and animations
        theme_css = f'''
        <style>
        :root {{
            color-scheme: {"dark" if self.is_dark else "light"};
            --transition-smooth: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            --transition-bounce: all 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
            --shadow-elevation-1: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
            --shadow-elevation-2: 0 3px 6px rgba(0, 0, 0, 0.16), 0 3px 6px rgba(0, 0, 0, 0.23);
            --shadow-elevation-3: 0 10px 20px rgba(0, 0, 0, 0.19), 0 6px 6px rgba(0, 0, 0, 0.23);
            --border-radius-sm: 0.5rem;
            --border-radius-md: 1rem;
            --border-radius-lg: 1.5rem;
            --border-radius-xl: 2rem;
        }}
        
        /* Smooth transitions for all elements */
        * {{
            transition: var(--transition-smooth);
        }}
        
        /* Modern glass morphism effects */
        .glass-card {{
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }}
        
        /* Hover effects */
        .hover-lift:hover {{
            transform: translateY(-4px);
            box-shadow: var(--shadow-elevation-3);
        }}
        
        /* Loading animations */
        @keyframes shimmer {{
            0% {{ background-position: -200px 0; }}
            100% {{ background-position: calc(200px + 100%) 0; }}
        }}
        
        .loading-shimmer {{
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200px 100%;
            animation: shimmer 1.5s infinite;
        }}
        
        /* Micro-interactions */
        .button-interactive {{
            transition: var(--transition-bounce);
        }}
        
        .button-interactive:active {{
            transform: scale(0.95);
        }}
        
        /* Progressive disclosure animations */
        .slide-down {{
            animation: slideDown 0.3s ease-out;
        }}
        
        @keyframes slideDown {{
            from {{
                opacity: 0;
                transform: translateY(-10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        </style>
        '''
        ui.add_head_html(theme_css)

def get_theme_classes(force_dark: bool = None) -> Dict[str, str]:
    """Get theme-appropriate CSS classes with modern design system and enhanced tokens"""
    theme_manager = ThemeManager()
    is_dark = force_dark if force_dark is not None else theme_manager.is_dark
    
    if is_dark:
        return {
            # Backgrounds with glass morphism
            'bg_primary': 'bg-gradient-to-br from-gray-900 via-slate-900 to-gray-900',
            'bg_secondary': 'bg-slate-800/60 backdrop-blur-xl glass-card',
            'bg_accent': 'bg-slate-700/80',
            'bg_surface': 'bg-slate-800/40 backdrop-blur-sm',
            
            # Typography
            'text_primary': 'text-slate-50',
            'text_secondary': 'text-slate-400',
            'text_accent': 'text-slate-300',
            'text_muted': 'text-slate-500',
            
            # Borders and dividers
            'border': 'border-slate-700/50',
            'border_accent': 'border-slate-600/30',
            'divider': 'border-slate-700/30',
            
            # Interactive elements
            'button_primary': 'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg hover:shadow-emerald-500/20 button-interactive hover-lift',
            'button_secondary': 'bg-slate-700/80 hover:bg-slate-600/80 border border-slate-600/50 text-slate-100 button-interactive hover-lift',
            'button_ghost': 'bg-transparent hover:bg-slate-800/50 text-slate-300 hover:text-slate-100 button-interactive',
            
            # Cards and containers
            'card': 'bg-slate-800/50 backdrop-blur-xl border-slate-700/40 shadow-2xl hover-lift',
            'card_elevated': 'bg-slate-800/60 backdrop-blur-xl border-slate-700/50 shadow-2xl hover:shadow-emerald-500/10',
            'card_interactive': 'bg-slate-800/40 backdrop-blur-xl border-slate-700/40 shadow-xl hover:bg-slate-800/60 hover:border-slate-600/50 cursor-pointer hover-lift',
            
            # Form elements
            'input_bg': 'bg-slate-800/60 border-slate-600/50 text-slate-100 placeholder-slate-400 focus:border-emerald-400/60 focus:ring-2 focus:ring-emerald-400/20',
            'textarea_bg': 'bg-slate-800/60 border-slate-600/50 text-slate-100 placeholder-slate-400 focus:border-emerald-400/60',
            
            # Status colors
            'success_bg': 'bg-gradient-to-r from-emerald-900/40 to-teal-900/40 border-emerald-500/40',
            'success_text': 'text-emerald-300',
            'error_bg': 'bg-gradient-to-r from-red-900/40 to-rose-900/40 border-red-500/40',
            'error_text': 'text-red-300',
            'warning_bg': 'bg-gradient-to-r from-amber-900/40 to-orange-900/40 border-amber-500/40',
            'warning_text': 'text-amber-300',
            
            # Special effects
            'gradient_text': 'bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent',
            'chip_bg': 'bg-slate-700/80 text-slate-200 border-slate-600/50 hover:bg-slate-600/80',
            'badge_bg': 'bg-emerald-600/20 text-emerald-300 border-emerald-500/30',
            
            # Navigation
            'nav_bg': 'bg-slate-900/80 backdrop-blur-xl border-b border-slate-800/50',
            'nav_item': 'text-slate-300 hover:text-emerald-400 hover:bg-slate-800/50',
            'nav_active': 'text-emerald-400 bg-emerald-900/20 border-emerald-500/30'
        }
    else:
        return {
            # Backgrounds with glass morphism  
            'bg_primary': 'bg-gradient-to-br from-slate-50 via-white to-blue-50/30',
            'bg_secondary': 'bg-white/80 backdrop-blur-xl glass-card',
            'bg_accent': 'bg-slate-100/80',
            'bg_surface': 'bg-white/60 backdrop-blur-sm',
            
            # Typography
            'text_primary': 'text-slate-900',
            'text_secondary': 'text-slate-600',
            'text_accent': 'text-slate-700',
            'text_muted': 'text-slate-500',
            
            # Borders and dividers
            'border': 'border-slate-200/80',
            'border_accent': 'border-slate-300/60',
            'divider': 'border-slate-200/50',
            
            # Interactive elements
            'button_primary': 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white shadow-lg hover:shadow-emerald-500/25 button-interactive hover-lift',
            'button_secondary': 'bg-white hover:bg-slate-50 border border-slate-300 text-slate-900 shadow-sm hover:shadow-md button-interactive hover-lift',
            'button_ghost': 'bg-transparent hover:bg-slate-100/50 text-slate-600 hover:text-slate-900 button-interactive',
            
            # Cards and containers
            'card': 'bg-white/80 backdrop-blur-xl border-slate-200/60 shadow-lg hover-lift',
            'card_elevated': 'bg-white/90 backdrop-blur-xl border-slate-200/70 shadow-xl hover:shadow-emerald-500/10',
            'card_interactive': 'bg-white/70 backdrop-blur-xl border-slate-200/50 shadow-md hover:bg-white/90 hover:border-slate-300/60 hover:shadow-xl cursor-pointer hover-lift',
            
            # Form elements
            'input_bg': 'bg-white/90 border-slate-300/80 text-slate-900 placeholder-slate-500 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/20',
            'textarea_bg': 'bg-white/90 border-slate-300/80 text-slate-900 placeholder-slate-500 focus:border-emerald-400',
            
            # Status colors
            'success_bg': 'bg-gradient-to-r from-emerald-50 to-teal-50 border-emerald-200',
            'success_text': 'text-emerald-700',
            'error_bg': 'bg-gradient-to-r from-red-50 to-rose-50 border-red-200',
            'error_text': 'text-red-700', 
            'warning_bg': 'bg-gradient-to-r from-amber-50 to-orange-50 border-amber-200',
            'warning_text': 'text-amber-700',
            
            # Special effects
            'gradient_text': 'bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 bg-clip-text text-transparent',
            'chip_bg': 'bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200',
            'badge_bg': 'bg-emerald-100 text-emerald-700 border-emerald-200',
            
            # Navigation
            'nav_bg': 'bg-white/90 backdrop-blur-xl border-b border-slate-200/60 shadow-sm',
            'nav_item': 'text-slate-600 hover:text-emerald-600 hover:bg-emerald-50/50',
            'nav_active': 'text-emerald-600 bg-emerald-50 border-emerald-200'
        }

def get_theme_manager() -> ThemeManager:
    """Get the singleton theme manager instance"""
    return ThemeManager()