from nicegui import ui
from typing import Dict, List, Callable, Optional
from ..utils.theme import get_theme_classes, get_theme_manager

class ModernNavigation:
    def __init__(self, current_user: Dict, theme: Dict[str, str]):
        self.current_user = current_user
        self.theme = theme
        self.theme_manager = get_theme_manager()
        
    def create_header(self, current_page: str = "home") -> ui.row:
        """Create modern header with navigation and theme toggle"""
        with ui.row().classes(f'{self.theme["nav_bg"]} w-full px-6 py-4 items-center justify-between sticky top-0 z-50 border-b {self.theme["border"]}') as header:
            # Logo and brand
            with ui.row().classes('items-center gap-4'):
                ui.html(f'''
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center text-xl">
                            🍽️
                        </div>
                        <h1 class="text-2xl font-bold {self.theme["gradient_text"]}">MyFoodPal</h1>
                    </div>
                ''')
            
            # Navigation tabs
            with ui.row().classes('flex-1 justify-center'):
                self._create_nav_tabs(current_page)
            
            # User actions
            with ui.row().classes('items-center gap-3'):
                self._create_user_menu()
        
        return header
    
    def _create_nav_tabs(self, current_page: str):
        """Create modern navigation tabs"""
        nav_items = [
            {"key": "home", "label": "Discover", "icon": "🏠", "path": "/"},
            {"key": "kitchen", "label": "My Kitchen", "icon": "🍳", "path": "/kitchen"},
            {"key": "plans", "label": "Meal Plans", "icon": "📋", "path": "/history"},
            {"key": "recipes", "label": "Recipe History", "icon": "📖", "path": "/recipe-history"}
        ]
        
        with ui.row().classes('bg-white/5 backdrop-blur-sm rounded-xl p-1 gap-1'):
            for item in nav_items:
                is_active = current_page == item["key"]
                
                # Active/inactive styling
                if is_active:
                    button_classes = f'{self.theme["nav_active"]} px-6 py-3 rounded-lg font-medium transition-all duration-300'
                else:
                    button_classes = f'{self.theme["nav_item"]} px-6 py-3 rounded-lg font-medium transition-all duration-300 hover:scale-105'
                
                with ui.button(on_click=lambda path=item["path"]: ui.navigate.to(path)).classes(button_classes):
                    with ui.row().classes('items-center gap-2'):
                        ui.html(f'<span class="text-base">{item["icon"]}</span>')
                        ui.html(f'<span class="text-sm">{item["label"]}</span>')
    
    def _create_user_menu(self):
        """Create user menu with theme toggle and profile options"""
        # Theme toggle button
        theme_icon = "🌙" if not self.theme_manager.is_dark else "☀️"
        theme_tooltip = f"Switch to {'dark' if not self.theme_manager.is_dark else 'light'} mode"
        
        ui.button(
            theme_icon,
            on_click=self._toggle_theme
        ).classes(f'{self.theme["button_ghost"]} w-10 h-10 rounded-xl text-lg').tooltip(theme_tooltip)
        
        # User profile dropdown
        with ui.button().classes(f'{self.theme["button_ghost"]} px-4 py-2 rounded-xl') as user_btn:
            with ui.row().classes('items-center gap-3'):
                # User avatar
                ui.html(f'''
                    <div class="w-8 h-8 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
                        {self.current_user.get("name", "U")[0].upper()}
                    </div>
                ''')
                ui.html(f'<span class="text-sm font-medium {self.theme["text_primary"]}">{self.current_user.get("name", "User")}</span>')
                ui.html('<span class="text-xs opacity-60">▼</span>')
        
        # Dropdown menu
        with ui.menu().props('auto-close') as menu:
            with ui.column().classes('gap-1 p-2 min-w-48'):
                # Profile section
                with ui.row().classes('items-center gap-3 p-3 border-b border-gray-200'):
                    ui.html(f'''
                        <div class="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-full flex items-center justify-center text-white font-bold">
                            {self.current_user.get("name", "U")[0].upper()}
                        </div>
                    ''')
                    with ui.column():
                        ui.html(f'<span class="font-medium {self.theme["text_primary"]}">{self.current_user.get("name", "User")}</span>')
                        ui.html(f'<span class="text-xs {self.theme["text_muted"]}">{self.current_user.get("email", "")}</span>')
                
                # Menu items
                menu_items = [
                    {"label": "👤 Profile Settings", "action": lambda: ui.notify("Profile settings coming soon!", type="info")},
                    {"label": "🍽️ Dietary Preferences", "action": lambda: ui.navigate.to("/")},
                    {"label": "📊 Usage Statistics", "action": lambda: ui.notify("Statistics coming soon!", type="info")},
                    {"label": "❓ Help & Support", "action": lambda: ui.notify("Help documentation coming soon!", type="info")},
                ]
                
                for item in menu_items:
                    ui.button(
                        item["label"],
                        on_click=item["action"]
                    ).classes(f'{self.theme["button_ghost"]} w-full justify-start px-3 py-2 text-sm rounded-lg')
                
                # Separator
                ui.separator()
                
                # Logout
                ui.button(
                    "🚪 Sign Out",
                    on_click=self._logout
                ).classes('w-full justify-start px-3 py-2 text-sm rounded-lg text-red-600 hover:bg-red-50')
        
        user_btn.on('click', menu.open)
    
    def _toggle_theme(self):
        """Toggle between light and dark themes"""
        self.theme_manager.toggle_theme()
        # Refresh the page to apply new theme
        ui.navigate.to(ui.page.request.url.path, new_tab=False)
    
    def _logout(self):
        """Handle user logout"""
        from ..utils.session import clear_current_user
        clear_current_user()
        ui.notify("Signed out successfully", type="positive")
        ui.navigate.to('/login')

def create_floating_action_button(theme: Dict[str, str], on_click: Callable) -> ui.button:
    """Create a floating action button for quick recipe generation"""
    return ui.button(
        "➕",
        on_click=on_click
    ).classes(f'''
        fixed bottom-6 right-6 w-14 h-14 rounded-full shadow-lg z-40
        bg-gradient-to-r from-emerald-500 to-teal-600 text-white text-2xl
        hover:from-emerald-600 hover:to-teal-700 hover:scale-110
        transition-all duration-300 hover:shadow-emerald-500/25
    ''').tooltip("Generate New Recipes")

def create_bottom_navigation(current_page: str, theme: Dict[str, str]) -> ui.row:
    """Create mobile bottom navigation (for responsive design)"""
    nav_items = [
        {"key": "home", "label": "Home", "icon": "🏠", "path": "/"},
        {"key": "kitchen", "label": "Kitchen", "icon": "🍳", "path": "/kitchen"},
        {"key": "plans", "label": "Plans", "icon": "📋", "path": "/history"},
        {"key": "recipes", "label": "Recipes", "icon": "📖", "path": "/recipe-history"}
    ]
    
    with ui.row().classes(f'''
        {theme["nav_bg"]} fixed bottom-0 left-0 right-0 z-40 px-4 py-2 
        border-t {theme["border"]} justify-around items-center
        md:hidden
    ''') as bottom_nav:
        for item in nav_items:
            is_active = current_page == item["key"]
            
            with ui.button(on_click=lambda path=item["path"]: ui.navigate.to(path)).classes(
                f'flex-1 py-3 bg-transparent border-none transition-all duration-200 {"scale-110" if is_active else ""}'
            ):
                with ui.column().classes('items-center gap-1'):
                    ui.html(f'<span class="text-lg {"opacity-100" if is_active else "opacity-60"}">{item["icon"]}</span>')
                    ui.html(f'<span class="text-xs {theme["nav_active" if is_active else "nav_item"]} font-medium">{item["label"]}</span>')
    
    return bottom_nav

class TabContainer:
    """Modern tab container for organizing content"""
    
    def __init__(self, theme: Dict[str, str]):
        self.theme = theme
        self.tabs = []
        self.active_tab = 0
    
    def add_tab(self, label: str, icon: str, content_builder: Callable):
        """Add a tab with label, icon, and content builder function"""
        self.tabs.append({
            "label": label,
            "icon": icon,
            "content_builder": content_builder
        })
    
    def render(self) -> ui.column:
        """Render the tab container"""
        with ui.column().classes('w-full') as container:
            # Tab headers
            with ui.row().classes(f'{self.theme["card"]} rounded-t-xl p-1 gap-1 border-b {self.theme["border"]}'):
                for i, tab in enumerate(self.tabs):
                    is_active = i == self.active_tab
                    
                    button_classes = (
                        f'{self.theme["nav_active"]} px-6 py-3 rounded-lg font-medium transition-all duration-300'
                        if is_active else
                        f'{self.theme["nav_item"]} px-6 py-3 rounded-lg font-medium transition-all duration-300 hover:scale-105'
                    )
                    
                    ui.button(
                        f'{tab["icon"]} {tab["label"]}',
                        on_click=lambda idx=i: self._switch_tab(idx)
                    ).classes(button_classes)
            
            # Tab content
            self.content_container = ui.column().classes('flex-1 p-6')
            self._render_active_content()
        
        return container
    
    def _switch_tab(self, tab_index: int):
        """Switch to a different tab"""
        self.active_tab = tab_index
        self._render_active_content()
    
    def _render_active_content(self):
        """Render the content of the active tab"""
        self.content_container.clear()
        with self.content_container:
            if self.tabs and 0 <= self.active_tab < len(self.tabs):
                self.tabs[self.active_tab]["content_builder"]()