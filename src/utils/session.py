from nicegui import app
import threading
import json
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Thread-local storage for session safety
_session_lock = threading.RLock()

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get the current user from session storage with thread safety"""
    try:
        with _session_lock:
            user_data = app.storage.user.get('current_user', None)
            if user_data and isinstance(user_data, dict):
                # Validate session data integrity
                required_fields = ['id', 'email', 'name']
                if all(field in user_data for field in required_fields):
                    return user_data
                else:
                    logger.warning("Invalid user session data, clearing session")
                    clear_current_user()
            return None
    except Exception as e:
        logger.error(f"Error getting current user from session: {e}")
        return None

def set_current_user(user) -> bool:
    """Set the current user in session storage with error handling"""
    try:
        with _session_lock:
            if user:
                # Create serializable user data
                user_data = {
                    'id': int(user.id),
                    'email': str(user.email),
                    'name': str(user.name),
                    'liked_foods': str(user.liked_foods or ''),
                    'disliked_foods': str(user.disliked_foods or ''),
                    'must_use_ingredients': str(getattr(user, 'must_use_ingredients', '') or ''),
                    'created_at': user.created_at.isoformat() if user.created_at else datetime.now().isoformat(),
                    'is_active': bool(user.is_active),
                    'session_created': datetime.now().isoformat(),
                    'last_activity': datetime.now().isoformat()
                }
                
                # Validate data before storing
                try:
                    # Test serialization
                    json.dumps(user_data)
                    app.storage.user['current_user'] = user_data
                    logger.info(f"User session created for user ID: {user.id}")
                    return True
                except (TypeError, ValueError) as e:
                    logger.error(f"Failed to serialize user data: {e}")
                    return False
            else:
                app.storage.user['current_user'] = None
                return True
                
    except Exception as e:
        logger.error(f"Error setting current user in session: {e}")
        return False

def clear_current_user() -> bool:
    """Clear the current user from session storage with error handling"""
    try:
        with _session_lock:
            current_user = app.storage.user.get('current_user')
            if current_user and isinstance(current_user, dict):
                user_id = current_user.get('id', 'unknown')
                logger.info(f"Clearing session for user ID: {user_id}")
            
            app.storage.user['current_user'] = None
            
            # Also clear any other user-specific session data
            user_keys_to_clear = [key for key in app.storage.user.keys() if key.startswith('user_')]
            for key in user_keys_to_clear:
                del app.storage.user[key]
                
            return True
    except Exception as e:
        logger.error(f"Error clearing user session: {e}")
        return False

def update_user_activity() -> bool:
    """Update last activity timestamp for the current user"""
    try:
        with _session_lock:
            current_user = get_current_user()
            if current_user:
                current_user['last_activity'] = datetime.now().isoformat()
                app.storage.user['current_user'] = current_user
                return True
    except Exception as e:
        logger.error(f"Error updating user activity: {e}")
    return False

def is_session_expired(max_inactive_hours: int = 24) -> bool:
    """Check if the current session has expired"""
    try:
        current_user = get_current_user()
        if not current_user or 'last_activity' not in current_user:
            return True
        
        last_activity = datetime.fromisoformat(current_user['last_activity'])
        hours_since_activity = (datetime.now() - last_activity).total_seconds() / 3600
        
        return hours_since_activity > max_inactive_hours
    except Exception as e:
        logger.error(f"Error checking session expiration: {e}")
        return True  # Assume expired on error for security

def cleanup_expired_session():
    """Clean up expired session if necessary"""
    if is_session_expired():
        logger.info("Session expired, clearing user data")
        clear_current_user()

def set_user_onboarding_step(user_id: int, step: str):
    """Set the onboarding step for a user"""
    current_user = get_current_user()
    if current_user and current_user.get('id') == user_id:
        current_user['onboarding_step'] = step
        if step == 'completed':
            current_user['has_completed_onboarding'] = True
        app.storage.user['current_user'] = current_user

def get_user_onboarding_step(user_id: int) -> str:
    """Get the current onboarding step for a user"""
    current_user = get_current_user()
    if current_user and current_user.get('id') == user_id:
        return current_user.get('onboarding_step', 'not_started')
    return 'not_started'