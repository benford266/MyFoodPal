from nicegui import app

def get_current_user():
    """Get the current user from session storage"""
    return app.storage.user.get('current_user', None)

def set_current_user(user):
    """Set the current user in session storage"""
    if user:
        # Store user data as a dictionary to avoid SQLAlchemy session issues
        user_data = {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'liked_foods': user.liked_foods,
            'disliked_foods': user.disliked_foods,
            'must_use_ingredients': getattr(user, 'must_use_ingredients', ''),
            'created_at': user.created_at.isoformat(),
            'is_active': user.is_active
        }
        app.storage.user['current_user'] = user_data
    else:
        app.storage.user['current_user'] = None

def clear_current_user():
    """Clear the current user from session storage"""
    app.storage.user['current_user'] = None