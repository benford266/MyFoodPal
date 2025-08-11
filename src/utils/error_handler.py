"""
Enhanced error handling system for FoodPal UI
Provides consistent error boundaries and user-friendly error messages
"""

from nicegui import ui
from typing import Dict, Any, Callable, Optional, Type, Union
from functools import wraps
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FoodPalException(Exception):
    """Base exception for FoodPal application"""
    def __init__(self, message: str, code: str = "GENERAL_ERROR", details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.now()

class UIException(FoodPalException):
    """UI-specific exceptions"""
    pass

class DatabaseException(FoodPalException):
    """Database-related exceptions"""
    pass

class APIException(FoodPalException):
    """API-related exceptions"""
    pass

class ValidationException(FoodPalException):
    """Input validation exceptions"""
    pass

class ErrorHandler:
    """Centralized error handling for UI components"""
    
    @staticmethod
    def handle_ui_error(
        error: Exception, 
        context: str = "UI Operation", 
        user_message: Optional[str] = None,
        theme: Optional[Dict[str, str]] = None
    ):
        """Handle UI errors with user-friendly messages"""
        
        # Log the error
        logger.error(f"Error in {context}: {str(error)}", exc_info=True)
        
        # Determine user message
        if user_message:
            display_message = user_message
        elif isinstance(error, ValidationException):
            display_message = f"Input validation failed: {error.message}"
        elif isinstance(error, DatabaseException):
            display_message = "Database operation failed. Please try again."
        elif isinstance(error, APIException):
            display_message = "Service temporarily unavailable. Please try again later."
        elif isinstance(error, UIException):
            display_message = error.message
        else:
            display_message = "An unexpected error occurred. Please try again."
        
        # Show user notification
        ui.notify(display_message, type='negative', timeout=5000)
        
        # Create error details for debugging (in development)
        if theme and hasattr(error, '__dict__'):
            ErrorHandler._create_error_debug_info(error, context, theme)
    
    @staticmethod
    def _create_error_debug_info(error: Exception, context: str, theme: Dict[str, str]):
        """Create debug information for development (can be disabled in production)"""
        import os
        if os.getenv('FOODPAL_DEBUG', 'false').lower() == 'true':
            with ui.dialog() as debug_dialog:
                with ui.card().classes('w-96 max-w-full'):
                    ui.html(f'<h3 class="text-lg font-bold {theme["error_text"]} mb-4">Debug Info: {context}</h3>')
                    ui.html(f'<p class="text-sm mb-2"><strong>Error Type:</strong> {type(error).__name__}</p>')
                    ui.html(f'<p class="text-sm mb-2"><strong>Message:</strong> {str(error)}</p>')
                    
                    if hasattr(error, 'code'):
                        ui.html(f'<p class="text-sm mb-2"><strong>Code:</strong> {error.code}</p>')
                    
                    # Stack trace (collapsed)
                    with ui.expansion('Stack Trace', icon='bug_report'):
                        ui.html(f'<pre class="text-xs overflow-auto max-h-40">{traceback.format_exc()}</pre>')
                    
                    ui.button('Close', on_click=debug_dialog.close).classes(f'{theme["button_secondary"]} mt-4')

def safe_ui_operation(
    user_message: str = None,
    context: str = "UI Operation",
    fallback_action: Callable = None
):
    """Decorator for safe UI operations with error handling"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get theme from args if available
                theme = None
                for arg in args:
                    if isinstance(arg, dict) and 'text_primary' in arg:
                        theme = arg
                        break
                
                ErrorHandler.handle_ui_error(e, context, user_message, theme)
                
                # Execute fallback action if provided
                if fallback_action:
                    try:
                        return fallback_action(*args, **kwargs)
                    except Exception as fallback_error:
                        logger.error(f"Fallback action failed: {fallback_error}")
                        
        return wrapper
    return decorator

def safe_async_ui_operation(
    user_message: str = None,
    context: str = "Async UI Operation",
    fallback_action: Callable = None
):
    """Decorator for safe async UI operations with error handling"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Get theme from args if available
                theme = None
                for arg in args:
                    if isinstance(arg, dict) and 'text_primary' in arg:
                        theme = arg
                        break
                
                ErrorHandler.handle_ui_error(e, context, user_message, theme)
                
                # Execute fallback action if provided
                if fallback_action:
                    try:
                        if callable(fallback_action):
                            result = fallback_action(*args, **kwargs)
                            if hasattr(result, '__await__'):
                                return await result
                            return result
                    except Exception as fallback_error:
                        logger.error(f"Async fallback action failed: {fallback_error}")
                        
        return wrapper
    return decorator

def validate_input(
    value: Any,
    validation_rules: Dict[str, Any],
    field_name: str = "Input"
) -> Any:
    """Validate input with comprehensive rules"""
    
    # Required check
    if validation_rules.get('required', False) and not value:
        raise ValidationException(f"{field_name} is required", "REQUIRED_FIELD")
    
    # Type check
    expected_type = validation_rules.get('type')
    if expected_type and value is not None and not isinstance(value, expected_type):
        raise ValidationException(f"{field_name} must be of type {expected_type.__name__}", "INVALID_TYPE")
    
    # String validations
    if isinstance(value, str) and value:
        min_length = validation_rules.get('min_length')
        max_length = validation_rules.get('max_length')
        
        if min_length and len(value) < min_length:
            raise ValidationException(f"{field_name} must be at least {min_length} characters", "MIN_LENGTH")
        
        if max_length and len(value) > max_length:
            raise ValidationException(f"{field_name} must not exceed {max_length} characters", "MAX_LENGTH")
        
        # Pattern validation
        pattern = validation_rules.get('pattern')
        if pattern:
            import re
            if not re.match(pattern, value):
                raise ValidationException(f"{field_name} format is invalid", "INVALID_FORMAT")
    
    # Numeric validations
    if isinstance(value, (int, float)) and value is not None:
        min_value = validation_rules.get('min_value')
        max_value = validation_rules.get('max_value')
        
        if min_value is not None and value < min_value:
            raise ValidationException(f"{field_name} must be at least {min_value}", "MIN_VALUE")
        
        if max_value is not None and value > max_value:
            raise ValidationException(f"{field_name} must not exceed {max_value}", "MAX_VALUE")
    
    return value

class UIErrorBoundary:
    """Error boundary component for UI sections"""
    
    def __init__(self, theme: Dict[str, str], fallback_content: str = None):
        self.theme = theme
        self.fallback_content = fallback_content or "Something went wrong. Please refresh the page."
        self.error_occurred = False
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error_occurred = True
            self._render_error_fallback(exc_val)
            return True  # Suppress the exception
        return False
    
    def _render_error_fallback(self, error: Exception):
        """Render fallback UI when error occurs"""
        with ui.card().classes(f'{self.theme["error_bg"]} rounded-xl p-6 border {self.theme["border"]} text-center'):
            ui.html('<div class="text-4xl mb-4">😞</div>')
            ui.html(f'<h3 class="text-lg font-bold {self.theme["error_text"]} mb-2">Oops! Something went wrong</h3>')
            ui.html(f'<p class="text-sm {self.theme["text_secondary"]} mb-4">{self.fallback_content}</p>')
            
            with ui.row().classes('gap-2 justify-center'):
                ui.button(
                    'Refresh Page',
                    on_click=lambda: ui.navigate.to(ui.navigate.to, new_tab=False)
                ).classes(f'{self.theme["button_primary"]} px-4 py-2 rounded-lg')
                
                ui.button(
                    'Go Home',
                    on_click=lambda: ui.navigate.to('/')
                ).classes(f'{self.theme["button_ghost"]} px-4 py-2 rounded-lg')

def create_error_boundary(theme: Dict[str, str], content_func: Callable, fallback_message: str = None):
    """Create an error boundary around content"""
    try:
        with UIErrorBoundary(theme, fallback_message):
            return content_func()
    except Exception as e:
        logger.error(f"Error boundary caught exception: {e}", exc_info=True)
        # Fallback is handled by the context manager
        return None

# Common validation rules
VALIDATION_RULES = {
    'email': {
        'type': str,
        'required': True,
        'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    },
    'password': {
        'type': str,
        'required': True,
        'min_length': 8,
        'max_length': 128
    },
    'name': {
        'type': str,
        'required': True,
        'min_length': 1,
        'max_length': 100
    },
    'recipe_count': {
        'type': int,
        'required': True,
        'min_value': 1,
        'max_value': 20
    },
    'serving_size': {
        'type': int,
        'required': True,
        'min_value': 1,
        'max_value': 50
    }
}