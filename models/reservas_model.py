# app/models/reservas_model.py - VERSIÓN MEJORADA
"""
Modelos de Reservas Mejorados - Optimizado para uso móvil
Nuevas funcionalidades:
- Notificaciones automáticas
- Sistema de rating
- Historial de reservas
- Estadísticas de uso
"""

from database import db
from datetime import datetime, date, time, timedelta
from decimal import Decimal


class AreaComun(db.Model):
    """
    Áreas comunes disponibles para reserva
    """
    __tablename__ = 'areas_comunes'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    descripcion = db.Column(db.Text, nullable=True)
    
    # Capacidad y características
    capacidad = db.Column(db.Integer, default=0)
    
    # Disponibilidad
    disponible = db.Column(db.Boolean, default=True)
    
    # Costo por hora
    costo_hora = db.Column(db.Numeric(10, 2), default=0.00)
    
    # Horario de operación
    hora_apertura = db.Column(db.Time, default=time(8, 0))
    hora_cierre = db.Column(db.Time, default=time(22, 0))
    
    # Tiempo mínimo y máximo de reserva (en horas)
    tiempo_minimo = db.Column(db.Integer, default=1)
    tiempo_maximo = db.Column(db.Integer, default=8)
    
    # NUEVO: Características adicionales
    requiere_deposito = db.Column(db.Boolean, default=False)
    monto_deposito = db.Column(db.Numeric(10, 2), default=0.00)
    
    # NUEVO: Equipamiento disponible
    equipamiento = db.Column(db.Text, nullable=True)  # JSON string
    
    # NUEVO: Reglas específicas
    reglas = db.Column(db.Text, nullable=True)
    
    # NUEVO: Rating promedio
    rating_promedio = db.Column(db.Numeric(3, 2), default=0.00)
    total_ratings = db.Column(db.Integer, default=0)
    
    # NUEVO: Popularidad
    total_reservas = db.Column(db.Integer, default=0)
    
    # Metadatos
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_modificacion = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Relación con reservas
    reservas = db.relationship('Reserva', backref='area', lazy=True, cascade='all, delete-orphan')
    ratings = db.relationship('AreaRating', backref='area', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, nombre, descripcion=None, capacidad=0, costo_hora=0, 
                 hora_apertura=None, hora_cierre=None):
        self.nombre = nombre
        self.descripcion = descripcion
        self.capacidad = capacidad
        self.costo_hora = Decimal(str(costo_hora))
        self.hora_apertura = hora_apertura or time(8, 0)
        self.hora_cierre = hora_cierre or time(22, 0)
        self.disponible = True
    
    def actualizar_rating(self):
        """Actualiza el rating promedio del área"""
        if self.total_ratings > 0:
            suma = sum(r.rating for r in self.ratings)
            self.rating_promedio = Decimal(str(suma / self.total_ratings))
        db.session.commit()
    
    def incrementar_contador_reservas(self):
        """Incrementa el contador de reservas"""
        self.total_reservas += 1
        db.session.commit()
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    @staticmethod
    def get_by_id(area_id):
        return AreaComun.query.get(area_id)
    
    @staticmethod
    def get_all():
        return AreaComun.query.all()
    
    @staticmethod
    def get_disponibles():
        """Obtiene solo áreas disponibles ordenadas por popularidad"""
        return AreaComun.query.filter_by(disponible=True)\
            .order_by(AreaComun.total_reservas.desc()).all()
    
    @staticmethod
    def get_mas_populares(limit=5):
        """Obtiene las áreas más populares"""
        return AreaComun.query.filter_by(disponible=True)\
            .order_by(AreaComun.total_reservas.desc())\
            .limit(limit).all()
    
    def esta_disponible_en(self, fecha, hora_inicio, hora_fin):
        """Verifica si el área está disponible en un horario específico"""
        if not self.disponible:
            return False
        
        if hora_inicio < self.hora_apertura or hora_fin > self.hora_cierre:
            return False
        
        from sqlalchemy import and_, or_
        conflictos = Reserva.query.filter(
            and_(
                Reserva.area_id == self.id,
                Reserva.fecha == fecha,
                Reserva.estado.in_(['pendiente', 'confirmada']),
                or_(
                    and_(
                        Reserva.hora_inicio <= hora_inicio,
                        Reserva.hora_fin > hora_inicio
                    ),
                    and_(
                        Reserva.hora_inicio < hora_fin,
                        Reserva.hora_fin >= hora_fin
                    ),
                    and_(
                        Reserva.hora_inicio >= hora_inicio,
                        Reserva.hora_fin <= hora_fin
                    )
                )
            )
        ).first()
        
        return conflictos is None
    
    def to_dict(self):
        """Serializa el área para API"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'capacidad': self.capacidad,
            'costo_hora': float(self.costo_hora),
            'disponible': self.disponible,
            'rating_promedio': float(self.rating_promedio) if self.rating_promedio else 0,
            'total_reservas': self.total_reservas,
        }


class Reserva(db.Model):
    """
    Reservas de áreas comunes - Mejorado
    """
    __tablename__ = 'reservas'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relación con área común
    area_id = db.Column(db.Integer, db.ForeignKey('areas_comunes.id'), nullable=False)
    
    # Departamento que reserva
    departamento = db.Column(db.Integer, nullable=False, index=True)
    
    # Información del usuario que reserva
    usuario = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    
    # Fecha y horario de la reserva
    fecha = db.Column(db.Date, nullable=False, index=True)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    
    # Motivo de la reserva
    motivo = db.Column(db.String(200), nullable=True)
    
    # Cantidad de personas
    num_personas = db.Column(db.Integer, default=1)
    
    # Costo total
    costo_total = db.Column(db.Numeric(10, 2), default=0.00)
    
    # Estado de la reserva
    estado = db.Column(db.String(20), default='pendiente')
    # Estados: 'pendiente', 'confirmada', 'cancelada', 'completada', 'no_show'
    
    # NUEVO: Recordatorios enviados
    recordatorio_24h_enviado = db.Column(db.Boolean, default=False)
    recordatorio_1h_enviado = db.Column(db.Boolean, default=False)
    
    # NUEVO: Check-in/Check-out
    check_in = db.Column(db.DateTime, nullable=True)
    check_out = db.Column(db.DateTime, nullable=True)
    
    # NUEVO: Notas del usuario
    notas_usuario = db.Column(db.Text, nullable=True)
    
    # NUEVO: Evaluación completada
    evaluada = db.Column(db.Boolean, default=False)
    
    # Metadatos
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_modificacion = db.Column(db.DateTime, onupdate=datetime.utcnow)
    fecha_cancelacion = db.Column(db.DateTime, nullable=True)
    motivo_cancelacion = db.Column(db.Text, nullable=True)
    
    # Observaciones administrativas
    observaciones = db.Column(db.Text, nullable=True)
    
    # Relación con rating
    rating = db.relationship('AreaRating', backref='reserva', uselist=False, 
                            cascade='all, delete-orphan')
    
    def __init__(self, area_id, departamento, usuario, fecha, hora_inicio, hora_fin,
                 motivo=None, num_personas=1, telefono=None, email=None):
        self.area_id = area_id
        self.departamento = departamento
        self.usuario = usuario
        self.fecha = fecha
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.motivo = motivo
        self.num_personas = num_personas
        self.telefono = telefono
        self.email = email
        self.estado = 'pendiente'
        
        self.calcular_costo()
    
    def calcular_costo(self):
        """Calcula el costo total de la reserva"""
        area = AreaComun.get_by_id(self.area_id)
        if area:
            hora_inicio_dt = datetime.combine(date.today(), self.hora_inicio)
            hora_fin_dt = datetime.combine(date.today(), self.hora_fin)
            horas = (hora_fin_dt - hora_inicio_dt).total_seconds() / 3600
            
            self.costo_total = float(area.costo_hora) * horas
            
            # Agregar depósito si es requerido
            if area.requiere_deposito:
                self.costo_total += float(area.monto_deposito)
    
    @property
    def duracion_horas(self):
        """Calcula la duración en horas"""
        hora_inicio_dt = datetime.combine(date.today(), self.hora_inicio)
        hora_fin_dt = datetime.combine(date.today(), self.hora_fin)
        return (hora_fin_dt - hora_inicio_dt).total_seconds() / 3600
    
    @property
    def puede_cancelar(self):
        """Verifica si la reserva puede ser cancelada (24hrs antes)"""
        if self.estado not in ['pendiente', 'confirmada']:
            return False
        
        fecha_hora_reserva = datetime.combine(self.fecha, self.hora_inicio)
        diferencia = fecha_hora_reserva - datetime.now()
        return diferencia.total_seconds() > 86400  # 24 horas
    
    @property
    def puede_check_in(self):
        """Verifica si puede hacer check-in (15 min antes)"""
        if self.estado != 'confirmada' or self.check_in:
            return False
        
        fecha_hora_reserva = datetime.combine(self.fecha, self.hora_inicio)
        diferencia = fecha_hora_reserva - datetime.now()
        return -900 <= diferencia.total_seconds() <= 900  # ±15 minutos
    
    @property
    def puede_check_out(self):
        """Verifica si puede hacer check-out"""
        if not self.check_in or self.check_out:
            return False
        
        fecha_hora_fin = datetime.combine(self.fecha, self.hora_fin)
        return datetime.now() >= fecha_hora_fin
    
    def confirmar(self):
        """Confirma la reserva"""
        self.estado = 'confirmada'
        
        # Incrementar contador del área
        area = AreaComun.get_by_id(self.area_id)
        if area:
            area.incrementar_contador_reservas()
        
        db.session.commit()
    
    def cancelar(self, motivo=None):
        """Cancela la reserva"""
        self.estado = 'cancelada'
        self.fecha_cancelacion = datetime.utcnow()
        if motivo:
            self.motivo_cancelacion = motivo
        db.session.commit()
    
    def completar(self):
        """Marca la reserva como completada"""
        self.estado = 'completada'
        db.session.commit()
    
    def hacer_check_in(self):
        """Registra el check-in"""
        if self.puede_check_in:
            self.check_in = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    def hacer_check_out(self):
        """Registra el check-out"""
        if self.puede_check_out:
            self.check_out = datetime.utcnow()
            self.completar()
            return True
        return False
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    @staticmethod
    def get_by_id(reserva_id):
        return Reserva.query.get(reserva_id)
    
    @staticmethod
    def get_all():
        return Reserva.query.order_by(Reserva.fecha.desc(), Reserva.hora_inicio.desc()).all()
    
    @staticmethod
    def get_by_departamento(departamento):
        """Obtiene todas las reservas de un departamento"""
        return Reserva.query.filter_by(
            departamento=departamento
        ).order_by(Reserva.fecha.desc()).all()
    
    @staticmethod
    def get_proximas_by_departamento(departamento):
        """Obtiene las próximas reservas de un departamento"""
        hoy = date.today()
        return Reserva.query.filter(
            Reserva.departamento == departamento,
            Reserva.fecha >= hoy,
            Reserva.estado.in_(['pendiente', 'confirmada'])
        ).order_by(Reserva.fecha, Reserva.hora_inicio).all()
    
    @staticmethod
    def get_historial_by_departamento(departamento, limit=10):
        """Obtiene el historial de reservas de un departamento"""
        return Reserva.query.filter_by(
            departamento=departamento
        ).order_by(Reserva.fecha.desc())\
        .limit(limit).all()
    
    @staticmethod
    def get_pendientes_evaluacion(departamento):
        """Obtiene reservas completadas pendientes de evaluación"""
        return Reserva.query.filter(
            Reserva.departamento == departamento,
            Reserva.estado == 'completada',
            Reserva.evaluada == False
        ).all()
    
    @staticmethod
    def get_by_area(area_id):
        """Obtiene todas las reservas de un área"""
        return Reserva.query.filter_by(area_id=area_id).order_by(Reserva.fecha.desc()).all()
    
    @staticmethod
    def get_by_fecha(fecha):
        """Obtiene todas las reservas de una fecha específica"""
        return Reserva.query.filter_by(fecha=fecha).all()
    
    @staticmethod
    def get_pendientes():
        """Obtiene todas las reservas pendientes"""
        return Reserva.query.filter_by(estado='pendiente').all()
    
    @staticmethod
    def get_proximas_horas(horas=24):
        """Obtiene reservas en las próximas X horas"""
        limite = datetime.now() + timedelta(hours=horas)
        return Reserva.query.filter(
            Reserva.estado.in_(['pendiente', 'confirmada']),
            Reserva.fecha == date.today()
        ).all()
    
    @staticmethod
    def get_fechas_ocupadas(area_id, mes=None, anio=None):
        """
        Obtiene las fechas que tienen al menos una reserva confirmada
        para un área específica
        """
        query = Reserva.query.filter(
            Reserva.area_id == area_id,
            Reserva.estado.in_(['pendiente', 'confirmada'])
        )
        
        if mes and anio:
            from sqlalchemy import extract
            query = query.filter(
                extract('month', Reserva.fecha) == mes,
                extract('year', Reserva.fecha) == anio
            )
        
        reservas = query.all()
        fechas = set(r.fecha for r in reservas)
        return sorted(list(fechas))
    
    @staticmethod
    def get_horarios_disponibles(area_id, fecha):
        """
        Retorna los horarios disponibles para una fecha específica
        """
        area = AreaComun.get_by_id(area_id)
        if not area or not area.disponible:
            return []
        
        # Obtener reservas del día
        reservas_dia = Reserva.query.filter(
            Reserva.area_id == area_id,
            Reserva.fecha == fecha,
            Reserva.estado.in_(['pendiente', 'confirmada'])
        ).order_by(Reserva.hora_inicio).all()
        
        # Generar horarios disponibles (bloques de 1 hora)
        horarios_disponibles = []
        hora_actual = area.hora_apertura
        
        while hora_actual < area.hora_cierre:
            hora_fin = (datetime.combine(date.today(), hora_actual) + timedelta(hours=1)).time()
            
            # Verificar si hay conflicto con alguna reserva
            conflicto = False
            for reserva in reservas_dia:
                if not (hora_fin <= reserva.hora_inicio or hora_actual >= reserva.hora_fin):
                    conflicto = True
                    break
            
            if not conflicto:
                horarios_disponibles.append({
                    'hora_inicio': hora_actual.strftime('%H:%M'),
                    'hora_fin': hora_fin.strftime('%H:%M')
                })
            
            hora_actual = hora_fin
        
        return horarios_disponibles
    
    def to_dict(self):
        """Serializa la reserva para API"""
        return {
            'id': self.id,
            'area': self.area.nombre if self.area else None,
            'departamento': self.departamento,
            'fecha': self.fecha.isoformat(),
            'hora_inicio': self.hora_inicio.strftime('%H:%M'),
            'hora_fin': self.hora_fin.strftime('%H:%M'),
            'estado': self.estado,
            'costo_total': float(self.costo_total),
            'num_personas': self.num_personas,
        }


class AreaRating(db.Model):
    """
    NUEVO: Sistema de calificación de áreas
    """
    __tablename__ = 'area_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relaciones
    area_id = db.Column(db.Integer, db.ForeignKey('areas_comunes.id'), nullable=False)
    reserva_id = db.Column(db.Integer, db.ForeignKey('reservas.id'), nullable=False)
    departamento = db.Column(db.Integer, nullable=False)
    
    # Calificación (1-5 estrellas)
    rating = db.Column(db.Integer, nullable=False)
    
    # Comentario opcional
    comentario = db.Column(db.Text, nullable=True)
    
    # Aspectos específicos (1-5)
    limpieza = db.Column(db.Integer, nullable=True)
    equipamiento = db.Column(db.Integer, nullable=True)
    ubicacion = db.Column(db.Integer, nullable=True)
    
    # Metadatos
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, area_id, reserva_id, departamento, rating, comentario=None,
                 limpieza=None, equipamiento=None, ubicacion=None):
        self.area_id = area_id
        self.reserva_id = reserva_id
        self.departamento = departamento
        self.rating = rating
        self.comentario = comentario
        self.limpieza = limpieza
        self.equipamiento = equipamiento
        self.ubicacion = ubicacion
    
    def save(self):
        db.session.add(self)
        db.session.commit()
        
        # Actualizar contador del área
        area = AreaComun.get_by_id(self.area_id)
        if area:
            area.total_ratings += 1
            area.actualizar_rating()
        
        # Marcar reserva como evaluada
        reserva = Reserva.get_by_id(self.reserva_id)
        if reserva:
            reserva.evaluada = True
            db.session.commit()
    
    @staticmethod
    def get_by_area(area_id):
        """Obtiene todos los ratings de un área"""
        return AreaRating.query.filter_by(area_id=area_id)\
            .order_by(AreaRating.fecha_creacion.desc()).all()
    
    @staticmethod
    def get_promedio_area(area_id):
        """Calcula el promedio de un área"""
        ratings = AreaRating.query.filter_by(area_id=area_id).all()
        if not ratings:
            return 0
        return sum(r.rating for r in ratings) / len(ratings)


# Función helper para inicializar áreas comunes por defecto
def inicializar_areas_comunes():
    """Crea áreas comunes predeterminadas si no existen"""
    areas_default = [
        {
            'nombre': 'Salón de Fiestas',
            'descripcion': 'Amplio salón para eventos y celebraciones con capacidad para 50 personas',
            'capacidad': 50,
            'costo_hora': 100.00,
            'requiere_deposito': True,
            'monto_deposito': 200.00,
            'equipamiento': 'Sillas, mesas, sistema de sonido, pantalla',
            'reglas': 'No fumar, respetar horario de cierre, dejar limpio'
        },
        {
            'nombre': 'Salón de Reuniones',
            'descripcion': 'Sala equipada para reuniones y presentaciones',
            'capacidad': 20,
            'costo_hora': 50.00,
            'equipamiento': 'Proyector, pizarra, WiFi, aire acondicionado'
        },
        {
            'nombre': 'Piscina',
            'descripcion': 'Piscina climatizada con área de descanso',
            'capacidad': 30,
            'costo_hora': 75.00,
            'hora_apertura': time(9, 0),
            'hora_cierre': time(20, 0),
            'reglas': 'Uso obligatorio de gorro, duchas antes de entrar, no correr'
        },
        {
            'nombre': 'Área de Parrillas',
            'descripcion': 'Zona de parrillas al aire libre con mesas',
            'capacidad': 25,
            'costo_hora': 40.00,
            'equipamiento': 'Parrilla, mesas, sillas, lavaplatos'
        },
        {
            'nombre': 'Cancha Deportiva',
            'descripcion': 'Cancha multiuso para deportes (fútbol, vóley, básquet)',
            'capacidad': 20,
            'costo_hora': 30.00,
            'equipamiento': 'Arcos, red de vóley, pelotas'
        }
    ]
    
    for area_data in areas_default:
        existe = AreaComun.query.filter_by(nombre=area_data['nombre']).first()
        if not existe:
            # Extraer campos específicos
            equipamiento = area_data.pop('equipamiento', None)
            reglas = area_data.pop('reglas', None)
            requiere_deposito = area_data.pop('requiere_deposito', False)
            monto_deposito = area_data.pop('monto_deposito', 0)
            
            area = AreaComun(**area_data)
            area.equipamiento = equipamiento
            area.reglas = reglas
            area.requiere_deposito = requiere_deposito
            area.monto_deposito = monto_deposito
            
            area.save()
            print(f"✅ Área creada: {area_data['nombre']}")