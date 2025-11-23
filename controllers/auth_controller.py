# app/controllers/auth_controller.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models.user_model import User
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

# Control de intentos fallidos
def get_intentos_fallidos():
    return session.get('login_intentos', 0)

def set_intentos_fallidos(intentos):
    session['login_intentos'] = intentos

def get_ultimo_intento():
    ts = session.get('ultimo_intento')
    return datetime.fromisoformat(ts) if ts else None

def set_ultimo_intento():
    session['ultimo_intento'] = datetime.now().isoformat()

def esta_bloqueado():
    intentos = get_intentos_fallidos()
    if intentos < 3:
        return False
    ultimo = get_ultimo_intento()
    if ultimo and (datetime.now() - ultimo) < timedelta(minutes=5):
        return True
    set_intentos_fallidos(0)
    return False

@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.home'))
    
    if request.method == 'POST':
        if esta_bloqueado():
            flash('Demasiados intentos fallidos. Espera 5 minutos.', 'danger')
            return render_template('auth/login.html')
        
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.get_by_username(username)
        
        if not user or not user.check_password(password):
            intentos = get_intentos_fallidos() + 1
            set_intentos_fallidos(intentos)
            set_ultimo_intento()
            flash('Usuario o contraseña incorrectos.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Login exitoso
        session['login_intentos'] = 0
        login_user(user)
        
        if user.must_change_password:
            flash('Debes cambiar tu contraseña temporal.', 'warning')
            return redirect(url_for('auth.cambiar_password'))
        
        flash(f'Bienvenido, {user.first_name}!', 'success')
        return redirect(url_for('auth.home'))
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Solo admins pueden registrar usuarios desde aquí
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role', 'residente')
        
        # Validar que no exista
        if User.get_by_username(username):
            flash('El usuario ya existe.', 'danger')
            return redirect(url_for('auth.register'))
        
        if User.get_by_email(email):
            flash('El correo ya está registrado.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Crear usuario
        new_user = User(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role
        )
        new_user.save()
        
        flash('Usuario registrado exitosamente.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/home')
@login_required
def home():
    return render_template('home.html', user=current_user)

@auth_bp.route('/cambiar_password', methods=['GET', 'POST'])
@login_required
def cambiar_password():
    if request.method == 'POST':
        nueva = request.form.get('nueva_password')
        
        if len(nueva) < 8:
            flash('La contraseña debe tener mínimo 8 caracteres.', 'danger')
            return redirect(url_for('auth.cambiar_password'))
        
        current_user.set_password(nueva)
        current_user.must_change_password = False
        current_user.update()
        
        flash('Contraseña actualizada correctamente.', 'success')
        return redirect(url_for('auth.home'))
    
    return render_template('auth/cambiar_password.html')