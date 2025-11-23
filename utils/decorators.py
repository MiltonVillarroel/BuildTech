from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Por favor, inicie sesión para acceder a esta página.', 'warning')
                return redirect(url_for('user.login'))
            if current_user.role != role:
                flash('No tienes permiso para acceder a esta página.', 'danger')
                return redirect(url_for('user.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator