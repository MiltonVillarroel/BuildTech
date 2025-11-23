# app/run.py
"""
BuildTech - Sistema de Gestión Integral para Edificios Multifamiliares
Versión Unificada con SQLite
"""

import sys
import os
import eventlet
eventlet.monkey_patch()

# Agregar el directorio app al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO
from database import db

# Importar blueprints
from controllers.auth_controller import auth_bp
from controllers.mantenimiento_controller import mantenimiento_bp
from controllers.comunicacion_controller import comunicacion_bp
from controllers.finanzas_controller import finanzas_bp
from controllers.reservas_controller import reservas_bp

# Importar eventos de Socket.IO
from socket_events import register_socket_events

# Importar modelos para cargar usuario
from models.user_model import User

def create_app():
    app = Flask(__name__)
    
    # Configuración
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///buildtech.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'buildtech-secret-key-2025'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    
    # Inicializar extensiones
    db.init_app(app)
    
    # Configurar Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(int(user_id))
    
    # Inicializar Socket.IO
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(mantenimiento_bp)
    app.register_blueprint(comunicacion_bp)
    app.register_blueprint(finanzas_bp)
    app.register_blueprint(reservas_bp)
    
    # Registrar eventos de Socket.IO
    register_socket_events(socketio)
    
    # Crear directorios necesarios
    os.makedirs('static/uploads/evidencias', exist_ok=True)
    
    # Crear tablas
    with app.app_context():
        db.create_all()
        
        # Inicializar áreas comunes si no existen
        from models.reservas_model import inicializar_areas_comunes
        inicializar_areas_comunes()
        
        print("\n" + "="*70)
        print("✓ Base de datos SQLite creada correctamente.")
        print("✓ Todas las tablas fueron creadas exitosamente.")
        print("✓ Áreas comunes inicializadas.")
        print("="*70)
        print("\n🏢 BUILDTECH - Sistema de Gestión Integral")
        print("="*70)
        print("\n📋 RUTAS PRINCIPALES:")
        print("   🔐 Login:           http://127.0.0.1:7000/")
        print("   🏠 Home:            http://127.0.0.1:7000/home")
        print("\n⚙️ MANTENIMIENTO:")
        print("   📋 Tickets:         http://127.0.0.1:7000/mantenimiento")
        print("   ➕ Crear:           http://127.0.0.1:7000/mantenimiento/crear")
        print("\n💬 COMUNICACIÓN:")
        print("   💬 Chat:            http://127.0.0.1:7000/comunicacion/chat")
        print("   📢 Avisos:          http://127.0.0.1:7000/comunicacion/avisos")
        print("   📝 Quejas:          http://127.0.0.1:7000/comunicacion/quejas")
        print("\n💰 FINANZAS:")
        print("   📊 Resumen:         http://127.0.0.1:7000/financiera/")
        print("   💳 Cargos Dpto:     http://127.0.0.1:7000/cargos_mensuales/dpto/1/")
        print("\n📅 RESERVAS:")
        print("   🎫 Reservar:        http://127.0.0.1:7000/reservas/")
        print("   🔧 Admin:           http://127.0.0.1:7000/reservas_admin/")
        print("="*70 + "\n")
    
    return app, socketio

if __name__ == "__main__":
    app, socketio = create_app()
    port = int(os.environ.get("PORT", 7000))
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)
