from database import db
from datetime import datetime

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionar con un ticket específico (opcional)
    ticket_id = db.Column(db.Integer, db.ForeignKey('mantenimiento.id_mantenimiento'), nullable=True)
    
    def __init__(self, content, username, ticket_id=None):
        self.content = content
        self.username = username
        self.ticket_id = ticket_id

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return ChatMessage.query.order_by(ChatMessage.timestamp.asc()).all()
    
    @staticmethod
    def get_by_ticket(ticket_id):
        return ChatMessage.query.filter_by(ticket_id=ticket_id).order_by(ChatMessage.timestamp.asc()).all()
    
    @staticmethod
    def get_recent(limit=50):
        return ChatMessage.query.order_by(ChatMessage.timestamp.desc()).limit(limit).all()

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'username': self.username,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'ticket_id': self.ticket_id
        }


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)  # 'nuevo_ticket', 'ticket_actualizado', etc.
    mensaje = db.Column(db.Text, nullable=False)
    leido = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionar con el ticket
    ticket_id = db.Column(db.Integer, db.ForeignKey('mantenimiento.id_mantenimiento'), nullable=True)
    
    def __init__(self, tipo, mensaje, ticket_id=None):
        self.tipo = tipo
        self.mensaje = mensaje
        self.ticket_id = ticket_id
        self.leido = False

    def save(self):
        db.session.add(self)
        db.session.commit()

    def marcar_leido(self):
        self.leido = True
        db.session.commit()

    @staticmethod
    def get_no_leidas():
        return Notification.query.filter_by(leido=False).order_by(Notification.timestamp.desc()).all()
    
    @staticmethod
    def get_all():
        return Notification.query.order_by(Notification.timestamp.desc()).all()

    def to_dict(self):
        return {
            'id': self.id,
            'tipo': self.tipo,
            'mensaje': self.mensaje,
            'leido': self.leido,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'ticket_id': self.ticket_id
        }
