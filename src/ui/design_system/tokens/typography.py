"""
Typography System

Comprehensive typography scale and text style tokens for consistent text hierarchy.
"""

from typing import Dict, Union

# Typography scale based on modular scale (1.25 ratio - Major Third)
TYPOGRAPHY_SCALE: Dict[str, Dict[str, str]] = {
    # Display text (hero sections, large headings)
    "display-large": {
        "size": "text-5xl lg:text-7xl",     # 48px -> 72px
        "weight": "font-black",
        "line_height": "leading-none",
        "letter_spacing": "tracking-tight"
    },
    
    "display-medium": {
        "size": "text-4xl lg:text-6xl",    # 36px -> 60px
        "weight": "font-bold", 
        "line_height": "leading-tight",
        "letter_spacing": "tracking-tight"
    },
    
    "display-small": {
        "size": "text-3xl lg:text-5xl",    # 30px -> 48px
        "weight": "font-bold",
        "line_height": "leading-tight", 
        "letter_spacing": "tracking-normal"
    },
    
    # Headings (section titles, card titles)
    "heading-1": {
        "size": "text-3xl lg:text-4xl",    # 30px -> 36px
        "weight": "font-bold",
        "line_height": "leading-tight",
        "letter_spacing": "tracking-normal"
    },
    
    "heading-2": {
        "size": "text-2xl lg:text-3xl",    # 24px -> 30px
        "weight": "font-semibold",
        "line_height": "leading-tight", 
        "letter_spacing": "tracking-normal"
    },
    
    "heading-3": {
        "size": "text-xl lg:text-2xl",     # 20px -> 24px
        "weight": "font-semibold",
        "line_height": "leading-snug",
        "letter_spacing": "tracking-normal"
    },
    
    "heading-4": {
        "size": "text-lg lg:text-xl",      # 18px -> 20px
        "weight": "font-semibold",
        "line_height": "leading-snug",
        "letter_spacing": "tracking-normal"
    },
    
    # Body text (paragraphs, descriptions)
    "body-large": {
        "size": "text-lg",                 # 18px
        "weight": "font-normal",
        "line_height": "leading-relaxed",
        "letter_spacing": "tracking-normal"
    },
    
    "body-medium": {
        "size": "text-base",               # 16px
        "weight": "font-normal", 
        "line_height": "leading-relaxed",
        "letter_spacing": "tracking-normal"
    },
    
    "body-small": {
        "size": "text-sm",                 # 14px
        "weight": "font-normal",
        "line_height": "leading-relaxed",
        "letter_spacing": "tracking-normal"
    },
    
    # UI text (buttons, labels, captions)
    "label-large": {
        "size": "text-base",               # 16px
        "weight": "font-medium",
        "line_height": "leading-normal",
        "letter_spacing": "tracking-normal"
    },
    
    "label-medium": {
        "size": "text-sm",                 # 14px
        "weight": "font-medium", 
        "line_height": "leading-normal",
        "letter_spacing": "tracking-normal"
    },
    
    "label-small": {
        "size": "text-xs",                 # 12px
        "weight": "font-medium",
        "line_height": "leading-normal",
        "letter_spacing": "tracking-wide"
    },
    
    # Caption text (metadata, timestamps)
    "caption": {
        "size": "text-xs",                 # 12px
        "weight": "font-normal",
        "line_height": "leading-normal",
        "letter_spacing": "tracking-normal"
    }
}

# Font weight tokens
FONT_WEIGHTS: Dict[str, str] = {
    "light": "font-light",        # 300
    "normal": "font-normal",      # 400
    "medium": "font-medium",      # 500
    "semibold": "font-semibold",  # 600
    "bold": "font-bold",          # 700
    "extrabold": "font-extrabold", # 800
    "black": "font-black"         # 900
}

def get_typography_classes(variant: str) -> str:
    """
    Get combined typography classes for a text variant.
    
    Args:
        variant: Typography variant name (e.g., 'heading-1', 'body-medium')
        
    Returns:
        Combined CSS classes string
        
    Example:
        >>> get_typography_classes('heading-1')
        'text-3xl lg:text-4xl font-bold leading-tight tracking-normal'
    """
    style = TYPOGRAPHY_SCALE.get(variant, TYPOGRAPHY_SCALE["body-medium"])
    
    return f"{style['size']} {style['weight']} {style['line_height']} {style['letter_spacing']}"

def create_text_element(text: str, variant: str, color_class: str = "", additional_classes: str = "") -> str:
    """
    Create a text element with proper typography and semantic markup.
    
    Args:
        text: Text content
        variant: Typography variant
        color_class: Color class (e.g., 'text-slate-900')
        additional_classes: Additional CSS classes
        
    Returns:
        HTML string for text element
        
    Example:
        >>> create_text_element('Welcome!', 'heading-1', 'text-slate-900', 'mb-4')
        '<h1 class="text-3xl lg:text-4xl font-bold leading-tight tracking-normal text-slate-900 mb-4">Welcome!</h1>'
    """
    typography_classes = get_typography_classes(variant)
    all_classes = f"{typography_classes} {color_class} {additional_classes}".strip()
    
    # Map variants to semantic HTML elements
    element_mapping = {
        "display-large": "h1",
        "display-medium": "h1", 
        "display-small": "h1",
        "heading-1": "h1",
        "heading-2": "h2",
        "heading-3": "h3",
        "heading-4": "h4",
        "body-large": "p",
        "body-medium": "p",
        "body-small": "p",
        "label-large": "span",
        "label-medium": "span",
        "label-small": "span",
        "caption": "small"
    }
    
    element = element_mapping.get(variant, "p")
    
    return f'<{element} class="{all_classes}">{text}</{element}>'

# Mobile typography adjustments
MOBILE_TYPOGRAPHY_OVERRIDES: Dict[str, str] = {
    "display-large": "text-4xl",
    "display-medium": "text-3xl", 
    "display-small": "text-2xl",
    "heading-1": "text-2xl",
    "heading-2": "text-xl",
    "heading-3": "text-lg"
}

def get_mobile_typography_classes(variant: str) -> str:
    """
    Get mobile-optimized typography classes.
    
    Args:
        variant: Typography variant name
        
    Returns:
        Mobile-specific CSS classes string
    """
    desktop_classes = get_typography_classes(variant)
    mobile_size = MOBILE_TYPOGRAPHY_OVERRIDES.get(variant)
    
    if mobile_size:
        # Replace the size class with mobile-specific size
        parts = desktop_classes.split()
        # Remove desktop size classes and add mobile size
        filtered_parts = [p for p in parts if not p.startswith('text-')]
        filtered_parts.insert(0, mobile_size)
        return " ".join(filtered_parts)
    
    return desktop_classes