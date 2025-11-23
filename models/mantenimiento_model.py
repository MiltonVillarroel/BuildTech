from database import db
from datetime import datetime

class Mantenimiento(db.Model):
    __tablename__ = 'mantenimiento'

    id_mantenimiento = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text, nullable=False)
    prioridad = db.Column(db.String(50), nullable=False)

    responsable = db.Column(db.String(100), nullable=True)
    fecha_ini = db.Column(db.Date, nullable=True)
    fecha_fin = db.Column(db.Date, nullable=True)
    costo = db.Column(db.Numeric(12, 2), nullable=True)

    trabajo_realizado = db.Column(db.Boolean, nullable=True, default=False)
    evidencia_url = db.Column(db.String(255), nullable=True)
    
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, descripcion, prioridad):
        self.descripcion = descripcion
        self.prioridad = prioridad
        self.responsable = None
        self.fecha_ini = None
        self.fecha_fin = None
        self.costo = None
        self.trabajo_realizado = False
        self.evidencia_url = None

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return Mantenimiento.query.order_by(Mantenimiento.fecha_creacion.desc()).all()

    @staticmethod
    def get_by_id(id):
        return Mantenimiento.query.get(id)

    def update_mantenimiento_inicio(self, responsable=None, fecha_ini=None, fecha_fin=None, costo=None, prioridad=None):
        if responsable is not None:
            self.responsable = responsable
        if fecha_ini is not None:
            self.fecha_ini = fecha_ini
        if fecha_fin is not None:
            self.fecha_fin = fecha_fin
        if costo is not None:
            self.costo = costo
        if prioridad is not None:
            self.prioridad = prioridad
        db.session.commit()

    def update_mantenimiento_fin(self, trabajo_realizado=None, evidencia_url=None):
        if trabajo_realizado is not None:
            self.trabajo_realizado = trabajo_realizado
        if evidencia_url is not None:
            self.evidencia_url = evidencia_url
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()