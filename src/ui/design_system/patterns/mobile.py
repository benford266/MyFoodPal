"""
Mobile Design Patterns

Mobile-first responsive patterns, touch interactions, and gesture handling for optimal mobile experience.
"""

from nicegui import ui
from typing import Optional, Callable, Dict, Any, List, Literal
from ..tokens.spacing import TOUCH_TARGETS
from ..tokens.animations import get_transition

class MobileOptimizations:
    """
    Mobile-specific optimizations and responsive patterns.
    
    Features:
    - Touch-friendly sizing and spacing
    - Mobile-first responsive breakpoints
    - Progressive enhancement for larger screens
    - Performance optimizations for mobile devices
    """
    
    # Mobile-first breakpoints
    BREAKPOINTS = {
        "mobile": "max-width: 640px",
        "tablet": "min-width: 641px and max-width: 1024px", 
        "desktop": "min-width: 1025px"
    }
    
    # Touch target recommendations  
    TOUCH_STANDARDS = {
        "minimum": 44,      # Apple/WCAG minimum
        "recommended": 48,  # Material Design recommendation
        "comfortable": 56   # Comfortable for most users
    }
    
    @staticmethod
    def create_mobile_header(
        title: str,
        back_button: bool = True,
        actions: Optional[List[Dict[str, Any]]] = None,
        theme: str = "light"
    ) -> ui.row:
        """Create mobile-optimized header with proper touch targets."""
        
        bg_color = "bg-white/95 backdrop-blur-xl border-slate-200/60" if theme == "light" else "bg-slate-900/95 backdrop-blur-xl border-slate-800/60"
        text_color = "text-slate-900" if theme == "light" else "text-slate-100"
        
        with ui.row().classes(f'{bg_color} border-b sticky top-0 z-40 px-4 py-3 items-center justify-between w-full') as header:
            # Left side - back button
            if back_button:
                from ..components.buttons import IconButton
                back_btn = IconButton(
                    icon="←",
                    variant="ghost",
                    size="md",
                    tooltip="Go back",
                    on_click=lambda: ui.navigate.back(),
                    theme=theme
                )
                back_btn.create()
            else:
                ui.html('<div class="w-12"></div>')  # Spacer
            
            # Center - title
            ui.html(f'<h1 class="text-lg font-bold {text_color} text-center flex-1 truncate px-4">{title}</h1>')
            
            # Right side - actions
            if actions:
                with ui.row().classes('gap-2'):
                    for action in actions:
                        from ..components.buttons import IconButton
                        action_btn = IconButton(
                            icon=action.get("icon", "⋮"),
                            variant="ghost",
                            size="md", 
                            tooltip=action.get("tooltip", ""),
                            on_click=action.get("callback"),
                            theme=theme
                        )
                        action_btn.create()
            else:
                ui.html('<div class="w-12"></div>')  # Spacer for balance
        
        return header
    
    @staticmethod
    def create_mobile_card_list(
        items: List[Dict[str, Any]],
        card_creator: Callable,
        theme: str = "light"
    ) -> ui.column:
        """Create mobile-optimized card list with proper spacing."""
        
        with ui.column().classes('gap-4 p-4 w-full') as container:
            for i, item in enumerate(items):
                # Create card with mobile optimizations
                card = card_creator(item, theme)
                
                # Add swipe gestures for mobile
                card.classes('touch-manipulation active:scale-[0.98] transition-transform duration-100')
                
                # Add staggered entrance animation
                card.style(f'animation-delay: {i * 50}ms;').classes('animate-[slideInUp_300ms_ease-out_both]')
        
        return container
    
    @staticmethod
    def create_bottom_sheet(
        content_creator: Callable,
        title: Optional[str] = None,
        max_height: str = "80vh",
        theme: str = "light"
    ) -> ui.column:
        """Create mobile bottom sheet modal."""
        
        bg_color = "bg-white" if theme == "light" else "bg-slate-900"
        handle_color = "bg-slate-300" if theme == "light" else "bg-slate-600"
        
        # Overlay
        overlay = ui.html(f'''
            <div class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 animate-[fadeIn_300ms_ease-out]" 
                 id="bottom-sheet-overlay"
                 onclick="this.parentElement.remove()">
            </div>
        ''')
        
        # Bottom sheet
        with ui.column().classes(f'''
            fixed bottom-0 left-0 right-0 {bg_color} rounded-t-3xl shadow-2xl z-50
            animate-[slideInUp_300ms_ease-out] max-h-[{max_height}] overflow-hidden
        ''') as sheet:
            
            # Handle
            ui.html(f'''
                <div class="w-12 h-1 {handle_color} rounded-full mx-auto mt-3 mb-1"></div>
            ''')
            
            # Header
            if title:
                with ui.row().classes('items-center justify-between p-6 pb-0'):
                    ui.html(f'<h2 class="text-xl font-bold {"text-slate-900" if theme == "light" else "text-slate-100"}">{title}</h2>')
                    
                    from ..components.buttons import IconButton
                    close_btn = IconButton(
                        icon="×",
                        variant="ghost",
                        size="md",
                        tooltip="Close",
                        on_click="document.getElementById('bottom-sheet-overlay').click()",
                        theme=theme
                    )
                    close_btn.create()
            
            # Content
            with ui.column().classes('flex-1 overflow-y-auto p-6'):
                content_creator()
        
        return sheet
    
    @staticmethod
    def create_mobile_tabs(
        tabs: List[Dict[str, Any]],
        active_tab: int = 0,
        theme: str = "light"
    ) -> ui.row:
        """Create mobile-optimized tab navigation."""
        
        bg_color = "bg-white border-slate-200" if theme == "light" else "bg-slate-900 border-slate-700"
        
        with ui.row().classes(f'{bg_color} border-b overflow-x-auto no-scrollbar sticky top-0 z-30') as tab_container:
            for i, tab in enumerate(tabs):
                is_active = i == active_tab
                
                # Tab styling
                active_classes = "text-emerald-600 border-emerald-600 bg-emerald-50/50" if theme == "light" else "text-emerald-400 border-emerald-400 bg-emerald-900/20"
                inactive_classes = "text-slate-600 border-transparent hover:text-slate-800" if theme == "light" else "text-slate-400 border-transparent hover:text-slate-200"
                
                tab_classes = active_classes if is_active else inactive_classes
                
                with ui.button(on_click=lambda idx=i: tab.get("callback", lambda: None)(idx)).classes(f'''
                    px-6 py-4 border-b-2 font-medium text-sm whitespace-nowrap transition-all duration-200
                    {tab_classes} {TOUCH_TARGETS["comfortable"]}
                '''):
                    if tab.get("icon"):
                        ui.html(f'<span class="mr-2">{tab["icon"]}</span>')
                    ui.html(f'<span>{tab.get("title", "Tab")}</span>')
                    
                    if tab.get("badge"):
                        ui.html(f'<span class="ml-2 bg-red-500 text-white text-xs rounded-full px-2 py-0.5">{tab["badge"]}</span>')
        
        return tab_container


class TouchInteractions:
    """
    Touch-optimized interaction patterns for mobile devices.
    
    Features:
    - Swipe gestures (left, right, up, down)
    - Pull-to-refresh functionality
    - Long press interactions
    - Touch feedback and haptics
    """
    
    @staticmethod
    def add_swipe_gestures(
        element: ui.element,
        on_swipe_left: Optional[Callable] = None,
        on_swipe_right: Optional[Callable] = None,
        on_swipe_up: Optional[Callable] = None,
        on_swipe_down: Optional[Callable] = None,
        threshold: int = 50
    ):
        """Add swipe gesture detection to an element."""
        
        # JavaScript for touch handling
        swipe_js = f'''
        (function() {{
            let startX = 0, startY = 0, endX = 0, endY = 0;
            const threshold = {threshold};
            
            element.addEventListener('touchstart', function(e) {{
                startX = e.touches[0].clientX;
                startY = e.touches[0].clientY;
            }}, {{ passive: true }});
            
            element.addEventListener('touchend', function(e) {{
                endX = e.changedTouches[0].clientX;
                endY = e.changedTouches[0].clientY;
                
                const deltaX = endX - startX;
                const deltaY = endY - startY;
                
                if (Math.abs(deltaX) > Math.abs(deltaY)) {{
                    // Horizontal swipe
                    if (Math.abs(deltaX) > threshold) {{
                        if (deltaX > 0) {{
                            // Swipe right
                            {'onSwipeRight && onSwipeRight();' if on_swipe_right else ''}
                        }} else {{
                            // Swipe left
                            {'onSwipeLeft && onSwipeLeft();' if on_swipe_left else ''}
                        }}
                    }}
                }} else {{
                    // Vertical swipe
                    if (Math.abs(deltaY) > threshold) {{
                        if (deltaY > 0) {{
                            // Swipe down
                            {'onSwipeDown && onSwipeDown();' if on_swipe_down else ''}
                        }} else {{
                            // Swipe up
                            {'onSwipeUp && onSwipeUp();' if on_swipe_up else ''}
                        }}
                    }}
                }}
            }}, {{ passive: true }});
        }})();
        '''
        
        element.add_script(swipe_js)
        
        # Add callbacks to global scope
        if on_swipe_left:
            ui.add_script(f'window.onSwipeLeft = {on_swipe_left.__name__};')
        if on_swipe_right:
            ui.add_script(f'window.onSwipeRight = {on_swipe_right.__name__};')
        if on_swipe_up:
            ui.add_script(f'window.onSwipeUp = {on_swipe_up.__name__};')
        if on_swipe_down:
            ui.add_script(f'window.onSwipeDown = {on_swipe_down.__name__};')
    
    @staticmethod
    def add_pull_to_refresh(
        container: ui.element,
        refresh_callback: Callable,
        threshold: int = 100
    ):
        """Add pull-to-refresh functionality to a scrollable container."""
        
        pull_refresh_js = f'''
        (function() {{
            let startY = 0;
            let currentY = 0;
            let pulling = false;
            const threshold = {threshold};
            
            // Create refresh indicator
            const indicator = document.createElement('div');
            indicator.className = 'fixed top-0 left-1/2 transform -translate-x-1/2 -translate-y-full transition-transform duration-300 bg-emerald-500 text-white px-4 py-2 rounded-b-lg shadow-lg z-50';
            indicator.innerHTML = '↓ Pull to refresh';
            document.body.appendChild(indicator);
            
            container.addEventListener('touchstart', function(e) {{
                if (container.scrollTop === 0) {{
                    startY = e.touches[0].clientY;
                    pulling = true;
                }}
            }}, {{ passive: true }});
            
            container.addEventListener('touchmove', function(e) {{
                if (pulling && container.scrollTop === 0) {{
                    currentY = e.touches[0].clientY;
                    const pullDistance = currentY - startY;
                    
                    if (pullDistance > 0) {{
                        const progress = Math.min(pullDistance / threshold, 1);
                        indicator.style.transform = `translateX(-50%) translateY(${{progress * 100 - 100}}%)`;
                        
                        if (pullDistance > threshold) {{
                            indicator.innerHTML = '↑ Release to refresh';
                            indicator.className = indicator.className.replace('bg-emerald-500', 'bg-teal-500');
                        }} else {{
                            indicator.innerHTML = '↓ Pull to refresh';
                            indicator.className = indicator.className.replace('bg-teal-500', 'bg-emerald-500');
                        }}
                    }}
                }}
            }}, {{ passive: true }});
            
            container.addEventListener('touchend', function(e) {{
                if (pulling) {{
                    const pullDistance = currentY - startY;
                    
                    if (pullDistance > threshold) {{
                        // Trigger refresh
                        indicator.innerHTML = '⟳ Refreshing...';
                        indicator.style.transform = 'translateX(-50%) translateY(0%)';
                        
                        // Call refresh callback
                        {refresh_callback.__name__ if hasattr(refresh_callback, '__name__') else 'refreshCallback'}();
                        
                        // Hide indicator after refresh
                        setTimeout(() => {{
                            indicator.style.transform = 'translateX(-50%) translateY(-100%)';
                        }}, 2000);
                    }} else {{
                        // Reset indicator
                        indicator.style.transform = 'translateX(-50%) translateY(-100%)';
                    }}
                    
                    pulling = false;
                }}
            }}, {{ passive: true }});
        }})();
        '''
        
        container.add_script(pull_refresh_js)
        
        # Add refresh callback to global scope
        ui.add_script(f'''
        window.{refresh_callback.__name__ if hasattr(refresh_callback, '__name__') else 'refreshCallback'} = function() {{
            // Call the Python callback
            pyodide.runPython(`{refresh_callback.__name__ if hasattr(refresh_callback, '__name__') else 'refresh_callback'}()`);
        }};
        ''')
    
    @staticmethod
    def add_long_press(
        element: ui.element,
        callback: Callable,
        duration: int = 500
    ):
        """Add long press interaction to an element."""
        
        long_press_js = f'''
        (function() {{
            let pressTimer = null;
            
            element.addEventListener('touchstart', function(e) {{
                pressTimer = setTimeout(function() {{
                    // Add haptic feedback if available
                    if (navigator.vibrate) {{
                        navigator.vibrate(50);
                    }}
                    
                    // Visual feedback
                    element.style.transform = 'scale(0.95)';
                    element.style.transition = 'transform 0.1s ease-out';
                    
                    // Call callback
                    {callback.__name__ if hasattr(callback, '__name__') else 'longPressCallback'}();
                }}, {duration});
            }}, {{ passive: true }});
            
            element.addEventListener('touchend', function(e) {{
                clearTimeout(pressTimer);
                element.style.transform = 'scale(1)';
            }}, {{ passive: true }});
            
            element.addEventListener('touchmove', function(e) {{
                clearTimeout(pressTimer);
                element.style.transform = 'scale(1)';
            }}, {{ passive: true }});
        }})();
        '''
        
        element.add_script(long_press_js)
        
        # Add callback to global scope
        ui.add_script(f'window.{callback.__name__ if hasattr(callback, "__name__") else "longPressCallback"} = function() {{ /* callback logic */ }};')


class GestureHandlers:
    """
    Advanced gesture handling for complex interactions.
    
    Features:
    - Pinch-to-zoom for images
    - Double-tap interactions
    - Multi-finger gestures
    - Gesture conflict resolution
    """
    
    @staticmethod
    def add_pinch_zoom(
        image_element: ui.element,
        min_scale: float = 0.5,
        max_scale: float = 3.0
    ):
        """Add pinch-to-zoom functionality to an image."""
        
        pinch_zoom_js = f'''
        (function() {{
            let scale = 1;
            let lastDistance = 0;
            const minScale = {min_scale};
            const maxScale = {max_scale};
            
            image_element.addEventListener('touchstart', function(e) {{
                if (e.touches.length === 2) {{
                    e.preventDefault();
                    lastDistance = getDistance(e.touches[0], e.touches[1]);
                }}
            }}, {{ passive: false }});
            
            image_element.addEventListener('touchmove', function(e) {{
                if (e.touches.length === 2) {{
                    e.preventDefault();
                    
                    const currentDistance = getDistance(e.touches[0], e.touches[1]);
                    const scaleChange = currentDistance / lastDistance;
                    scale = Math.min(Math.max(scale * scaleChange, minScale), maxScale);
                    
                    image_element.style.transform = `scale(${{scale}})`;
                    image_element.style.transition = 'none';
                    
                    lastDistance = currentDistance;
                }}
            }}, {{ passive: false }});
            
            image_element.addEventListener('touchend', function(e) {{
                image_element.style.transition = 'transform 0.3s ease-out';
                
                // Reset if scale is too small
                if (scale < 1) {{
                    scale = 1;
                    image_element.style.transform = 'scale(1)';
                }}
            }}, {{ passive: true }});
            
            function getDistance(touch1, touch2) {{
                const dx = touch1.clientX - touch2.clientX;
                const dy = touch1.clientY - touch2.clientY;
                return Math.sqrt(dx * dx + dy * dy);
            }}
        }})();
        '''
        
        image_element.add_script(pinch_zoom_js)
    
    @staticmethod
    def add_double_tap(
        element: ui.element,
        callback: Callable,
        delay: int = 300
    ):
        """Add double-tap interaction to an element."""
        
        double_tap_js = f'''
        (function() {{
            let lastTap = 0;
            let tapTimeout = null;
            
            element.addEventListener('touchend', function(e) {{
                const currentTime = new Date().getTime();
                const tapLength = currentTime - lastTap;
                
                clearTimeout(tapTimeout);
                
                if (tapLength < {delay} && tapLength > 0) {{
                    // Double tap detected
                    e.preventDefault();
                    
                    // Visual feedback
                    element.style.transform = 'scale(1.05)';
                    element.style.transition = 'transform 0.1s ease-out';
                    
                    setTimeout(() => {{
                        element.style.transform = 'scale(1)';
                    }}, 100);
                    
                    // Call callback
                    {callback.__name__ if hasattr(callback, '__name__') else 'doubleTapCallback'}();
                }} else {{
                    tapTimeout = setTimeout(function() {{
                        // Single tap
                    }}, {delay});
                }}
                
                lastTap = currentTime;
            }}, {{ passive: false }});
        }})();
        '''
        
        element.add_script(double_tap_js)
        
        # Add callback to global scope
        ui.add_script(f'window.{callback.__name__ if hasattr(callback, "__name__") else "doubleTapCallback"} = function() {{ /* callback logic */ }};')


# Utility functions for mobile optimization
def is_mobile_device() -> bool:
    """Detect if the user is on a mobile device."""
    # This would typically check user agent or screen size
    # For now, return a default value
    return True

def get_safe_area_insets() -> Dict[str, str]:
    """Get safe area insets for devices with notches/home indicators."""
    return {
        "top": "env(safe-area-inset-top, 0px)",
        "right": "env(safe-area-inset-right, 0px)", 
        "bottom": "env(safe-area-inset-bottom, 0px)",
        "left": "env(safe-area-inset-left, 0px)"
    }

def add_viewport_meta() -> str:
    """Generate viewport meta tag for mobile optimization."""
    return '''
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="theme-color" content="#10b981">
    '''