"""
Animation System

Comprehensive animation tokens and utilities for smooth, delightful interactions.
"""

from typing import Dict, Optional

# Animation duration tokens (following Material Design guidelines)
ANIMATION_DURATIONS: Dict[str, str] = {
    "instant": "0ms",
    "fast": "150ms",        # Quick transitions (hover, focus)
    "normal": "250ms",      # Standard transitions 
    "slow": "350ms",        # Complex transitions
    "slower": "500ms",      # Entrance/exit animations
    "slowest": "700ms",     # Page transitions
}

# Easing functions for natural motion
EASING_FUNCTIONS: Dict[str, str] = {
    "linear": "linear",
    "ease": "ease",
    "ease_in": "ease-in",
    "ease_out": "ease-out", 
    "ease_in_out": "ease-in-out",
    
    # Custom cubic-bezier functions
    "smooth": "cubic-bezier(0.4, 0, 0.2, 1)",           # Material Design standard
    "bounce": "cubic-bezier(0.68, -0.55, 0.265, 1.55)", # Playful bounce
    "elastic": "cubic-bezier(0.175, 0.885, 0.32, 1.275)", # Elastic effect
    "sharp": "cubic-bezier(0.4, 0, 0.6, 1)",            # Sharp entrance
    "gentle": "cubic-bezier(0, 0, 0.2, 1)",             # Gentle entrance/exit
}

# Pre-defined transition tokens
TRANSITION_TOKENS: Dict[str, str] = {
    # Common property transitions
    "all": f"all {ANIMATION_DURATIONS['normal']} {EASING_FUNCTIONS['smooth']}",
    "colors": f"color {ANIMATION_DURATIONS['fast']} {EASING_FUNCTIONS['smooth']}, background-color {ANIMATION_DURATIONS['fast']} {EASING_FUNCTIONS['smooth']}, border-color {ANIMATION_DURATIONS['fast']} {EASING_FUNCTIONS['smooth']}",
    "transform": f"transform {ANIMATION_DURATIONS['normal']} {EASING_FUNCTIONS['smooth']}",
    "opacity": f"opacity {ANIMATION_DURATIONS['fast']} {EASING_FUNCTIONS['smooth']}",
    "shadow": f"box-shadow {ANIMATION_DURATIONS['normal']} {EASING_FUNCTIONS['smooth']}",
    
    # Interactive element transitions
    "button": f"all {ANIMATION_DURATIONS['fast']} {EASING_FUNCTIONS['smooth']}",
    "card": f"transform {ANIMATION_DURATIONS['normal']} {EASING_FUNCTIONS['smooth']}, box-shadow {ANIMATION_DURATIONS['normal']} {EASING_FUNCTIONS['smooth']}",
    "modal": f"all {ANIMATION_DURATIONS['slower']} {EASING_FUNCTIONS['gentle']}",
    "dropdown": f"all {ANIMATION_DURATIONS['normal']} {EASING_FUNCTIONS['sharp']}",
    
    # Loading and feedback
    "loading": f"all {ANIMATION_DURATIONS['slow']} {EASING_FUNCTIONS['ease_in_out']}",
    "pulse": f"opacity {ANIMATION_DURATIONS['slower']} {EASING_FUNCTIONS['ease_in_out']}",
}

# Keyframe animations
KEYFRAMES: Dict[str, str] = {
    # Loading animations
    "shimmer": """
        @keyframes shimmer {
            0% { background-position: -200px 0; }
            100% { background-position: calc(200px + 100%) 0; }
        }
    """,
    
    "pulse": """
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    """,
    
    "spin": """
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
    """,
    
    # Entrance animations
    "fade_in": """
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    """,
    
    "slide_in_up": """
        @keyframes slideInUp {
            from { 
                opacity: 0;
                transform: translateY(20px);
            }
            to { 
                opacity: 1;
                transform: translateY(0);
            }
        }
    """,
    
    "slide_in_down": """
        @keyframes slideInDown {
            from { 
                opacity: 0;
                transform: translateY(-20px);
            }
            to { 
                opacity: 1;
                transform: translateY(0);
            }
        }
    """,
    
    "scale_in": """
        @keyframes scaleIn {
            from { 
                opacity: 0;
                transform: scale(0.95);
            }
            to { 
                opacity: 1;
                transform: scale(1);
            }
        }
    """,
    
    # Interactive animations
    "bounce_once": """
        @keyframes bounceOnce {
            0%, 20%, 60%, 100% { transform: translateY(0); }
            40% { transform: translateY(-10px); }
            80% { transform: translateY(-5px); }
        }
    """,
    
    "shake": """
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-2px); }
            20%, 40%, 60%, 80% { transform: translateX(2px); }
        }
    """,
    
    # Progress animations
    "progress_indeterminate": """
        @keyframes progressIndeterminate {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(300%); }
        }
    """,
}

# Animation utility classes
ANIMATION_CLASSES: Dict[str, str] = {
    # Loading states
    "loading_shimmer": f"animate-pulse bg-gradient-to-r from-slate-200 via-slate-300 to-slate-200 bg-[length:200px_100%]",
    "loading_pulse": "animate-pulse",
    "loading_spin": "animate-spin",
    
    # Entrance animations
    "fade_in": f"animate-[fadeIn_{ANIMATION_DURATIONS['normal']}_ease-out]",
    "slide_up": f"animate-[slideInUp_{ANIMATION_DURATIONS['normal']}_ease-out]", 
    "slide_down": f"animate-[slideInDown_{ANIMATION_DURATIONS['normal']}_ease-out]",
    "scale_in": f"animate-[scaleIn_{ANIMATION_DURATIONS['normal']}_ease-out]",
    
    # Interactive feedback
    "bounce_once": f"animate-[bounceOnce_{ANIMATION_DURATIONS['slow']}_ease-out]",
    "shake": f"animate-[shake_{ANIMATION_DURATIONS['normal']}_ease-in-out]",
    
    # Hover effects
    "hover_lift": "hover:-translate-y-1 hover:shadow-lg transition-all duration-200",
    "hover_scale": "hover:scale-105 transition-transform duration-200",
    "hover_glow": "hover:shadow-emerald-500/25 transition-shadow duration-300",
}

# Reduced motion preferences (accessibility)
REDUCED_MOTION_CSS: str = """
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
"""

def get_transition(property: str = "all", duration: str = "normal", easing: str = "smooth") -> str:
    """
    Generate a custom transition CSS property.
    
    Args:
        property: CSS property to transition
        duration: Duration token name
        easing: Easing function token name
        
    Returns:
        CSS transition property string
        
    Example:
        >>> get_transition("transform", "fast", "bounce")
        "transform 150ms cubic-bezier(0.68, -0.55, 0.265, 1.55)"
    """
    duration_value = ANIMATION_DURATIONS.get(duration, ANIMATION_DURATIONS["normal"])
    easing_value = EASING_FUNCTIONS.get(easing, EASING_FUNCTIONS["smooth"])
    
    return f"{property} {duration_value} {easing_value}"

def create_animation_css(
    name: str, 
    duration: str = "normal", 
    easing: str = "ease_out",
    delay: str = "0ms",
    iteration_count: str = "1",
    fill_mode: str = "forwards"
) -> str:
    """
    Generate CSS animation property.
    
    Args:
        name: Animation name (keyframe name)
        duration: Duration token name
        easing: Easing function token name
        delay: Animation delay
        iteration_count: Number of iterations
        fill_mode: Animation fill mode
        
    Returns:
        CSS animation property string
        
    Example:
        >>> create_animation_css("slideInUp", "slow", "bounce")
        "slideInUp 350ms cubic-bezier(0.68, -0.55, 0.265, 1.55) 0ms 1 forwards"
    """
    duration_value = ANIMATION_DURATIONS.get(duration, duration)
    easing_value = EASING_FUNCTIONS.get(easing, easing)
    
    return f"{name} {duration_value} {easing_value} {delay} {iteration_count} {fill_mode}"

def get_staggered_animation_delay(index: int, base_delay: int = 50) -> str:
    """
    Calculate staggered animation delay for list items.
    
    Args:
        index: Item index (0-based)
        base_delay: Base delay in milliseconds
        
    Returns:
        CSS animation delay value
        
    Example:
        >>> get_staggered_animation_delay(2, 100)
        "200ms"
    """
    delay = index * base_delay
    return f"{delay}ms"

# Performance considerations
PERFORMANCE_GUIDELINES: Dict[str, str] = {
    "gpu_accelerated": "transform: translateZ(0)", # Forces GPU acceleration
    "will_change_transform": "will-change: transform", # Hint to browser
    "will_change_opacity": "will-change: opacity",
    "contain_layout": "contain: layout", # CSS containment for better performance
}

def generate_animation_css() -> str:
    """
    Generate complete CSS for all animation tokens and keyframes.
    
    Returns:
        Complete CSS string with all animations
    """
    css_parts = [
        "/* Animation System CSS */",
        "",
        "/* CSS Custom Properties for animations */",
        ":root {",
    ]
    
    # Add duration custom properties
    for name, duration in ANIMATION_DURATIONS.items():
        css_parts.append(f"  --duration-{name.replace('_', '-')}: {duration};")
    
    css_parts.extend([
        "}",
        "",
        "/* Keyframe animations */"
    ])
    
    # Add all keyframes
    for keyframe in KEYFRAMES.values():
        css_parts.append(keyframe)
    
    css_parts.extend([
        "",
        "/* Utility classes */",
        ".transition-smooth { transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1); }",
        ".transition-bounce { transition: all 500ms cubic-bezier(0.68, -0.55, 0.265, 1.55); }",
        "",
        REDUCED_MOTION_CSS
    ])
    
    return "\n".join(css_parts)