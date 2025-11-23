# app/models/user_model.py
from database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Información personal
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    ci = db.Column(db.String(20), unique=True, nullable=True)
    telefono = db.Column(db.String(15), nullable=True)
    
    # Rol y permisos
    role = db.Column(db.String(50), nullable=False, default='residente')
    # Roles: 'admin', 'residente', 'personal'
    
    # Departamento (si es residente)
    departamento = db.Column(db.Integer, nullable=True)
    
    # Control de contraseña
    must_change_password = db.Column(db.Boolean, default=False)
    
    # Estado
    estado = db.Column(db.String(20), default='activo')
    # Estados: 'activo', 'provisional', 'inactivo'
    
    fecha_creacion = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, username, email, password, first_name, last_name, 
                 role='residente', departamento=None, ci=None, telefono=None):
        self.username = username
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.departamento = departamento
        self.ci = ci
        self.telefono = telefono

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def update(self):
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    @staticmethod
    def get_all():
        return User.query.all()
    
    @staticmethod
    def get_by_id(user_id):
        return User.query.get(user_id)
    
    @staticmethod
    def get_by_email(email):
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def get_by_username(username):
        return User.query.filter_by(username=username).first()
    
    def has_role(self, role):
        return self.role == role
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"