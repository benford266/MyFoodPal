"""
Spacing System

Consistent spacing scale and layout tokens for proper visual hierarchy.
"""

from typing import Dict

# Spacing scale based on 8px grid system (0.5rem = 8px)
SPACING_SCALE: Dict[str, str] = {
    "0": "0",           # 0px
    "1": "0.25rem",     # 4px
    "2": "0.5rem",      # 8px
    "3": "0.75rem",     # 12px
    "4": "1rem",        # 16px
    "5": "1.25rem",     # 20px
    "6": "1.5rem",      # 24px
    "8": "2rem",        # 32px
    "10": "2.5rem",     # 40px
    "12": "3rem",       # 48px
    "16": "4rem",       # 64px
    "20": "5rem",       # 80px
    "24": "6rem",       # 96px
    "32": "8rem",       # 128px
    "40": "10rem",      # 160px
    "48": "12rem",      # 192px
    "56": "14rem",      # 224px
    "64": "16rem",      # 256px
}

# Layout tokens for common spacing patterns
LAYOUT_TOKENS: Dict[str, Dict[str, str]] = {
    # Container spacing
    "container": {
        "padding_mobile": "px-4",                    # 16px horizontal padding on mobile
        "padding_tablet": "px-6",                    # 24px horizontal padding on tablet
        "padding_desktop": "px-8",                   # 32px horizontal padding on desktop
        "max_width": "max-w-7xl mx-auto",           # Centered with max width
        "section_spacing": "py-12 lg:py-16",       # Vertical section spacing
    },
    
    # Card spacing
    "card": {
        "padding_compact": "p-4",                   # 16px all around - compact cards
        "padding_default": "p-6",                   # 24px all around - default cards
        "padding_spacious": "p-8",                  # 32px all around - spacious cards
        "padding_mobile": "p-4 lg:p-6",           # Responsive card padding
        "gap_internal": "space-y-4",               # Gap between card elements
        "gap_external": "gap-4 lg:gap-6",         # Gap between cards
    },
    
    # Form spacing
    "form": {
        "field_spacing": "space-y-4",             # Gap between form fields
        "label_spacing": "mb-2",                   # Gap between label and input
        "section_spacing": "space-y-6",           # Gap between form sections
        "button_spacing": "mt-6",                  # Gap above form buttons
        "inline_spacing": "gap-4",                # Gap for inline form elements
    },
    
    # Navigation spacing
    "navigation": {
        "header_padding": "px-6 py-4",            # Header padding
        "nav_item_padding": "px-3 py-2",          # Navigation item padding
        "nav_gap": "gap-6",                       # Gap between navigation items
        "breadcrumb_gap": "gap-2",                # Gap between breadcrumb items
        "mobile_nav_padding": "p-4",             # Mobile navigation padding
    },
    
    # Content spacing
    "content": {
        "paragraph_spacing": "space-y-4",         # Gap between paragraphs
        "section_spacing": "space-y-8 lg:space-y-12", # Gap between sections
        "list_spacing": "space-y-2",             # Gap between list items
        "heading_margin": "mb-4",                 # Margin below headings
        "element_gap": "gap-3",                   # General element gap
    },
    
    # Grid and layout
    "grid": {
        "columns_mobile": "grid-cols-1",          # Single column on mobile
        "columns_tablet": "grid-cols-2",          # Two columns on tablet
        "columns_desktop": "grid-cols-3 lg:grid-cols-4", # Multi-column on desktop
        "gap_compact": "gap-4",                   # Compact grid gap
        "gap_default": "gap-6",                   # Default grid gap
        "gap_spacious": "gap-8",                  # Spacious grid gap
    }
}

# Responsive spacing utilities
RESPONSIVE_SPACING: Dict[str, Dict[str, str]] = {
    "mobile_first": {
        "small_to_medium": "space-y-4 lg:space-y-6",
        "medium_to_large": "space-y-6 lg:space-y-8",
        "large_to_xlarge": "space-y-8 lg:space-y-12",
        "padding_responsive": "p-4 lg:p-6 xl:p-8",
        "margin_responsive": "m-4 lg:m-6 xl:m-8",
    },
    
    "breakpoint_specific": {
        "mobile_only": "block lg:hidden",
        "desktop_only": "hidden lg:block", 
        "tablet_up": "hidden md:block",
        "mobile_padding": "px-4 md:px-6 lg:px-8",
        "mobile_margin": "mx-4 md:mx-6 lg:mx-8",
    }
}

def get_spacing_token(token_path: str) -> str:
    """
    Get a spacing token by its path.
    
    Args:
        token_path: Dot-separated path to token (e.g., 'card.padding_default')
        
    Returns:
        CSS class string for the spacing token
        
    Example:
        >>> get_spacing_token('card.padding_default')
        'p-6'
    """
    parts = token_path.split('.')
    
    if len(parts) == 1:
        return SPACING_SCALE.get(parts[0], "0")
    
    if len(parts) == 2:
        category, token = parts
        return LAYOUT_TOKENS.get(category, {}).get(token, "")
    
    return ""

def create_spacing_utility(
    property_type: str, 
    size: str, 
    responsive: bool = False
) -> str:
    """
    Create spacing utility classes.
    
    Args:
        property_type: Type of spacing ('margin', 'padding', 'gap')
        size: Size token (e.g., '4', '6', '8')
        responsive: Whether to include responsive variants
        
    Returns:
        CSS class string
        
    Example:
        >>> create_spacing_utility('padding', '6', True)
        'p-4 lg:p-6'
    """
    base_size = SPACING_SCALE.get(size, size)
    
    prefix_map = {
        'margin': 'm',
        'padding': 'p',
        'gap': 'gap'
    }
    
    prefix = prefix_map.get(property_type, 'p')
    base_class = f"{prefix}-{size}"
    
    if responsive:
        # Add responsive variant (smaller on mobile)
        mobile_size = str(max(1, int(size) - 2)) if size.isdigit() else size
        return f"{prefix}-{mobile_size} lg:{base_class}"
    
    return base_class

# Touch target sizing (accessibility requirement)
TOUCH_TARGETS: Dict[str, str] = {
    "minimum": "min-h-[44px] min-w-[44px]",      # WCAG minimum touch target
    "recommended": "min-h-[48px] min-w-[48px]",  # Recommended touch target
    "comfortable": "min-h-[56px] min-w-[56px]",  # Comfortable touch target
}

# Z-index scale for layering
Z_INDEX_SCALE: Dict[str, str] = {
    "dropdown": "z-10",
    "sticky": "z-20", 
    "modal_backdrop": "z-40",
    "modal": "z-50",
    "popover": "z-60",
    "tooltip": "z-70",
    "notification": "z-80"
}

def get_layout_classes(layout_type: str) -> str:
    """
    Get common layout class combinations.
    
    Args:
        layout_type: Type of layout pattern
        
    Returns:
        Combined CSS classes for the layout
        
    Example:
        >>> get_layout_classes('card_grid')
        'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'
    """
    layouts = {
        "card_grid": "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",
        "flex_center": "flex items-center justify-center",
        "flex_between": "flex items-center justify-between",
        "flex_column": "flex flex-col space-y-4",
        "container_centered": "max-w-7xl mx-auto px-4 lg:px-8",
        "section_spacing": "py-12 lg:py-16",
        "mobile_stack": "flex flex-col lg:flex-row gap-6",
    }
    
    return layouts.get(layout_type, "")