from functools import wraps
from flask import abort, current_app
from flask_login import current_user


def roles_required(*roles):
    """Izinkan akses hanya untuk user dengan salah satu role yang disebutkan."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            if not current_user.has_role(*roles):
                abort(403)
            return view_func(*args, **kwargs)
        return wrapper
    return decorator
