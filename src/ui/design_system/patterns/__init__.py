"""
Design Patterns

Common layout patterns and compound components for the FoodPal application.
"""

from .layouts import ResponsiveGrid, CardLayout, SectionLayout
from .mobile import MobileOptimizations, TouchInteractions, GestureHandlers

__all__ = [
    'ResponsiveGrid',
    'CardLayout', 
    'SectionLayout',
    'MobileOptimizations',
    'TouchInteractions',
    'GestureHandlers'
]