# ============================================================
# app/views/user_view.py
# ============================================================
"""
Vistas de renderizado para usuarios
"""

from flask import render_template
from flask_login import current_user

def register():
    """Renderiza la vista de registro"""
    return render_template(
        'auth/register.html',
        title="Registro",
        current_user=current_user,
    )

def login():
    """Renderiza la vista de login"""
    return render_template(
        'auth/login.html',
        title="Inicio de Sesión",
        current_user=current_user,
    )

def perfil(user):
    """Renderiza el perfil de usuario"""
    return render_template(
        "base.html",
        title="Perfil de Usuario",
        current_user=current_user,
        user=user,
    )