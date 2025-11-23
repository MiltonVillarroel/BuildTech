from database import db
from datetime import datetime

class Aviso(db.Model):
    __tablename__ = 'avisos'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)  # 'urgente', 'importante', 'informativo'
    autor = db.Column(db.String(100), nullable=False)  # Nombre del admin
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)  # Para archivar avisos sin borrarlos
    
    def __init__(self, titulo, contenido, categoria, autor):
        self.titulo = titulo
        self.contenido = contenido
        self.categoria = categoria
        self.autor = autor
        self.activo = True

    def save(self):
        db.session.add(self)
        db.session.commit()

    def archivar(self):
        """Marca el aviso como inactivo en lugar de eliminarlo"""
        self.activo = False
        db.session.commit()

    def reactivar(self):
        """Reactiva un aviso archivado"""
        self.activo = True
        db.session.commit()

    @staticmethod
    def get_all_activos():
        """Obtiene todos los avisos activos ordenados por fecha descendente"""
        return Aviso.query.filter_by(activo=True).order_by(Aviso.timestamp.desc()).all()
    
    @staticmethod
    def get_all():
        """Obtiene todos los avisos (incluidos archivados)"""
        return Aviso.query.order_by(Aviso.timestamp.desc()).all()
    
    @staticmethod
    def get_by_id(aviso_id):
        return Aviso.query.get(aviso_id)
    
    @staticmethod
    def get_by_categoria(categoria):
        """Obtiene avisos activos por categoría"""
        return Aviso.query.filter_by(activo=True, categoria=categoria).order_by(Aviso.timestamp.desc()).all()

    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'contenido': self.contenido,
            'categoria': self.categoria,
            'autor': self.autor,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'activo': self.activo
        }


class Queja(db.Model):
    __tablename__ = 'quejas'

    id = db.Column(db.Integer, primary_key=True)
    contenido = db.Column(db.Text, nullable=False)
    anonima = db.Column(db.Boolean, default=False)
    autor = db.Column(db.String(100), nullable=True)  # Null si es anónima
    categoria = db.Column(db.String(50), nullable=False)  # 'mantenimiento', 'seguridad', 'limpieza', 'vecinos', 'otro'
    estado = db.Column(db.String(50), default='pendiente')  # 'pendiente', 'en_revision', 'resuelta', 'archivada'
    respuesta = db.Column(db.Text, nullable=True)  # Respuesta del admin
    respondida_por = db.Column(db.String(100), nullable=True)  # Nombre del admin que respondió
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_respuesta = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, contenido, categoria, anonima=False, autor=None):
        self.contenido = contenido
        self.categoria = categoria
        self.anonima = anonima
        self.autor = autor if not anonima else None
        self.estado = 'pendiente'

    def save(self):
        db.session.add(self)
        db.session.commit()

    def responder(self, respuesta, admin_nombre):
        """Registra la respuesta del administrador"""
        self.respuesta = respuesta
        self.respondida_por = admin_nombre
        self.fecha_respuesta = datetime.utcnow()
        self.estado = 'resuelta'
        db.session.commit()

    def cambiar_estado(self, nuevo_estado):
        """Cambia el estado de la queja"""
        estados_validos = ['pendiente', 'en_revision', 'resuelta', 'archivada']
        if nuevo_estado in estados_validos:
            self.estado = nuevo_estado
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_all():
        return Queja.query.order_by(Queja.timestamp.desc()).all()
    
    @staticmethod
    def get_pendientes():
        """Obtiene quejas pendientes y en revisión"""
        return Queja.query.filter(
            Queja.estado.in_(['pendiente', 'en_revision'])
        ).order_by(Queja.timestamp.desc()).all()
    
    @staticmethod
    def get_by_estado(estado):
        return Queja.query.filter_by(estado=estado).order_by(Queja.timestamp.desc()).all()
    
    @staticmethod
    def get_by_categoria(categoria):
        return Queja.query.filter_by(categoria=categoria).order_by(Queja.timestamp.desc()).all()
    
    @staticmethod
    def get_by_id(queja_id):
        return Queja.query.get(queja_id)

    def to_dict(self):
        return {
            'id': self.id,
            'contenido': self.contenido,
            'anonima': self.anonima,
            'autor': self.autor if not self.anonima else 'Anónimo',
            'categoria': self.categoria,
            'estado': self.estado,
            'respuesta': self.respuesta,
            'respondida_por': self.respondida_por,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'fecha_respuesta': self.fecha_respuesta.strftime('%Y-%m-%d %H:%M:%S') if self.fecha_respuesta else None
        }