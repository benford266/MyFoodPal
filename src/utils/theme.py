from nicegui import ui

class ThemeManager:
    def __init__(self):
        self.is_dark = self.get_system_theme()
    
    def get_system_theme(self) -> bool:
        """Detect system theme preference"""
        # For now, default to light mode. In production, could use browser API
        return False
    
    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.apply_theme()
    
    def apply_theme(self):
        """Apply theme to the UI"""
        if self.is_dark:
            ui.add_head_html('<style>:root { color-scheme: dark; }</style>')
        else:
            ui.add_head_html('<style>:root { color-scheme: light; }</style>')

def get_theme_classes():
    """Get theme-appropriate CSS classes with modern design system"""
    # For now, default to light theme
    # TODO: Implement proper theme management
    is_dark = False
    
    if is_dark:
        return {
            'bg_primary': 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900',
            'bg_secondary': 'bg-slate-800/50 backdrop-blur-xl',
            'bg_accent': 'bg-slate-700/80',
            'text_primary': 'text-slate-100',
            'text_secondary': 'text-slate-400',
            'text_accent': 'text-slate-300',
            'border': 'border-slate-600/50',
            'border_accent': 'border-slate-500/30',
            'button_primary': 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 shadow-lg hover:shadow-emerald-500/25',
            'button_secondary': 'bg-slate-700 hover:bg-slate-600 border border-slate-600 text-slate-100',
            'card': 'bg-slate-800/40 backdrop-blur-xl border-slate-700/50 shadow-xl',
            'card_hover': 'hover:bg-slate-800/60 hover:border-slate-600/50 hover:shadow-2xl',
            'input_bg': 'bg-slate-800/50 border-slate-600/50 text-slate-100 focus:border-emerald-400/50 focus:ring-emerald-400/20',
            'success_bg': 'bg-gradient-to-r from-emerald-900/30 to-teal-900/30 border-emerald-500/30',
            'error_bg': 'bg-gradient-to-r from-red-900/30 to-rose-900/30 border-red-500/30',
            'gradient_text': 'bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent',
            'chip_bg': 'bg-slate-700/80 text-slate-200 border-slate-600/50'
        }
    else:
        return {
            'bg_primary': 'bg-gradient-to-br from-slate-50 via-white to-slate-100',
            'bg_secondary': 'bg-white/80 backdrop-blur-xl',
            'bg_accent': 'bg-slate-100/80',
            'text_primary': 'text-slate-900',
            'text_secondary': 'text-slate-600',
            'text_accent': 'text-slate-700',
            'border': 'border-slate-200/80',
            'border_accent': 'border-slate-300/50',
            'button_primary': 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 shadow-lg hover:shadow-emerald-500/25',
            'button_secondary': 'bg-white hover:bg-slate-50 border border-slate-300 text-slate-900',
            'card': 'bg-white/70 backdrop-blur-xl border-slate-200/50 shadow-lg',
            'card_hover': 'hover:bg-white/90 hover:border-slate-300/50 hover:shadow-xl',
            'input_bg': 'bg-white/80 border-slate-300/80 text-slate-900 focus:border-emerald-400 focus:ring-emerald-400/20',
            'success_bg': 'bg-gradient-to-r from-emerald-50 to-teal-50 border-emerald-200',
            'error_bg': 'bg-gradient-to-r from-red-50 to-rose-50 border-red-200',
            'gradient_text': 'bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 bg-clip-text text-transparent',
            'chip_bg': 'bg-slate-100 text-slate-700 border-slate-200'
        }