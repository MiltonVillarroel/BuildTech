# app/controllers/reservas_controller.py - VERSIÓN MEJORADA CON NUEVAS FUNCIONALIDADES
"""
Controlador de Reservas Mejorado - Optimizado para uso móvil
Nuevas rutas:
- Sistema de notificaciones
- Calificaciones de áreas
- Check-in/Check-out
- API endpoints para móvil
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from utils.decorators import role_required
from models.reservas_model import AreaComun, Reserva, AreaRating
from models.finanzas_model import PagoReserva
from datetime import datetime, date, time
from utils.email_utils import enviar_email_confirmacion_reserva

reservas_bp = Blueprint('reservas', __name__)


# ============================================================================
# RUTAS PRINCIPALES
# ============================================================================

@reservas_bp.route('/reservas/', methods=['GET', 'POST'])
@login_required
def reservas():
    """
    Vista principal de reservas para residentes (OPTIMIZADA PARA MÓVIL)
    """
    if request.method == 'POST':
        area_id = int(request.form.get('area_id'))
        fecha_str = request.form.get('fecha')
        hora_inicio_str = request.form.get('hora_inicio')
        hora_fin_str = request.form.get('hora_fin')
        motivo = request.form.get('motivo', '')
        num_personas = int(request.form.get('num_personas', 1))
        
        try:
            # Parsear fecha y horas
            fecha_reserva = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
            hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()
            
            # Validaciones
            if fecha_reserva < date.today():
                flash('❌ No puedes reservar fechas pasadas.', 'danger')
                return redirect(url_for('reservas.reservas'))
            
            if hora_inicio >= hora_fin:
                flash('❌ La hora de inicio debe ser anterior a la hora de fin.', 'danger')
                return redirect(url_for('reservas.reservas'))
            
            # Verificar disponibilidad
            area = AreaComun.get_by_id(area_id)
            if not area:
                flash('❌ Área no encontrada.', 'danger')
                return redirect(url_for('reservas.reservas'))
            
            # Validar capacidad
            if num_personas > area.capacidad:
                flash(f'❌ El área tiene capacidad máxima de {area.capacidad} personas.', 'danger')
                return redirect(url_for('reservas.reservas'))
            
            if not area.esta_disponible_en(fecha_reserva, hora_inicio, hora_fin):
                flash('❌ El área no está disponible en ese horario.', 'danger')
                return redirect(url_for('reservas.reservas'))
            
            # Crear reserva
            reserva = Reserva(
                area_id=area_id,
                departamento=current_user.departamento,
                usuario=current_user.get_full_name(),
                fecha=fecha_reserva,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                motivo=motivo,
                num_personas=num_personas,
                telefono=current_user.telefono,
                email=current_user.email
            )
            reserva.save()
            
            # Crear pago asociado
            pago = PagoReserva(
                reserva_id=reserva.id,
                monto=reserva.costo_total
            )
            pago.save()
            
            # Enviar email de confirmación
            try:
                enviar_email_confirmacion_reserva(reserva)
            except:
                pass  # No fallar si el email no funciona
            
            flash(f'✅ Reserva creada exitosamente. Costo: Bs. {reserva.costo_total:.2f}', 'success')
            return redirect(url_for('reservas.reservas'))
            
        except ValueError as e:
            flash(f'❌ Error en los datos ingresados: {str(e)}', 'danger')
            return redirect(url_for('reservas.reservas'))
    
    # GET
    areas = AreaComun.get_disponibles()
    
    # Obtener reservas del usuario actual
    if current_user.departamento:
        mis_reservas = Reserva.get_proximas_by_departamento(current_user.departamento)
    else:
        mis_reservas = []
    
    return render_template('reservas/reservas.html', 
                         areas=areas, 
                         mis_reservas=mis_reservas,
                         fecha_minima=date.today().isoformat())


@reservas_bp.route('/reservas_admin/')
@role_required('admin')
def reservas_admin():
    """
    Vista de administración de todas las reservas
    """
    estado_filtro = request.args.get('estado', 'todas')
    area_filtro = request.args.get('area', 'todas')
    
    reservas = Reserva.get_all()
    
    if estado_filtro != 'todas':
        reservas = [r for r in reservas if r.estado == estado_filtro]
    
    if area_filtro != 'todas':
        reservas = [r for r in reservas if r.area_id == int(area_filtro)]
    
    areas = AreaComun.get_all()
    reservas_pendientes = Reserva.get_pendientes()
    
    return render_template('reservas/reservas_admin.html',
                         reservas=reservas,
                         areas=areas,
                         reservas_pendientes=reservas_pendientes,
                         estado_filtro=estado_filtro,
                         area_filtro=area_filtro)


# ============================================================================
# GESTIÓN DE RESERVAS
# ============================================================================

@reservas_bp.route('/eliminar_reserva/<int:reserva_id>/', methods=['POST'])
@login_required
def eliminar_reserva(reserva_id):
    """
    Eliminar/cancelar una reserva
    """
    reserva = Reserva.get_by_id(reserva_id)
    
    if not reserva:
        flash('❌ Reserva no encontrada.', 'danger')
        return redirect(url_for('reservas.reservas'))
    
    # Verificar permisos
    puede_eliminar = (
        current_user.has_role('admin') or 
        current_user.departamento == reserva.departamento
    )
    
    if not puede_eliminar:
        flash('❌ No tienes permiso para cancelar esta reserva.', 'danger')
        return redirect(url_for('reservas.reservas'))
    
    # Verificar si puede cancelar (24hrs antes)
    if not reserva.puede_cancelar and not current_user.has_role('admin'):
        flash('⚠️ Solo puedes cancelar con 24 horas de anticipación.', 'warning')
        return redirect(url_for('reservas.reservas'))
    
    motivo = request.form.get('motivo', 'Cancelada por el usuario')
    reserva.cancelar(motivo)
    
    flash('✅ Reserva cancelada exitosamente.', 'success')
    
    if current_user.has_role('admin'):
        return redirect(url_for('reservas.reservas_admin'))
    else:
        return redirect(url_for('reservas.reservas'))


@reservas_bp.route('/editar_reserva/<int:reserva_id>/', methods=['GET', 'POST'])
@login_required
def editar_reserva(reserva_id):
    """
    Editar una reserva existente
    """
    reserva = Reserva.get_by_id(reserva_id)
    
    if not reserva:
        flash('❌ Reserva no encontrada.', 'danger')
        return redirect(url_for('reservas.reservas'))
    
    # Verificar permisos
    puede_editar = (
        current_user.has_role('admin') or 
        current_user.departamento == reserva.departamento
    )
    
    if not puede_editar:
        flash('❌ No tienes permiso para editar esta reserva.', 'danger')
        return redirect(url_for('reservas.reservas'))
    
    if request.method == 'POST':
        accion = request.form.get('accion')
        
        if accion == 'confirmar':
            reserva.confirmar()
            flash('✅ Reserva confirmada.', 'success')
        
        elif accion == 'cancelar':
            motivo = request.form.get('motivo', '')
            reserva.cancelar(motivo)
            flash('✅ Reserva cancelada.', 'success')
        
        elif accion == 'actualizar':
            # Actualizar datos
            fecha_str = request.form.get('fecha')
            hora_inicio_str = request.form.get('hora_inicio')
            hora_fin_str = request.form.get('hora_fin')
            motivo = request.form.get('motivo')
            num_personas = int(request.form.get('num_personas', 1))
            
            try:
                nueva_fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                nueva_hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
                nueva_hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()
                
                # Verificar disponibilidad si cambió fecha u hora
                if (nueva_fecha != reserva.fecha or 
                    nueva_hora_inicio != reserva.hora_inicio or 
                    nueva_hora_fin != reserva.hora_fin):
                    
                    area = AreaComun.get_by_id(reserva.area_id)
                    if not area.esta_disponible_en(nueva_fecha, nueva_hora_inicio, nueva_hora_fin):
                        flash('❌ El área no está disponible en el nuevo horario.', 'danger')
                        return redirect(url_for('reservas.editar_reserva', reserva_id=reserva_id))
                
                # Actualizar
                reserva.fecha = nueva_fecha
                reserva.hora_inicio = nueva_hora_inicio
                reserva.hora_fin = nueva_hora_fin
                reserva.motivo = motivo
                reserva.num_personas = num_personas
                reserva.calcular_costo()
                reserva.save()
                
                flash('✅ Reserva actualizada exitosamente.', 'success')
            except ValueError as e:
                flash(f'❌ Error en los datos: {str(e)}', 'danger')
        
        if current_user.has_role('admin'):
            return redirect(url_for('reservas.reservas_admin'))
        else:
            return redirect(url_for('reservas.reservas'))
    
    # GET
    areas = AreaComun.get_all()
    
    return render_template('reservas/editar_reserva.html', 
                         reserva=reserva,
                         areas=areas,
                         fecha_minima=date.today().isoformat())


# ============================================================================
# CHECK-IN / CHECK-OUT
# ============================================================================

@reservas_bp.route('/check_in/<int:reserva_id>/', methods=['POST'])
@login_required
def check_in(reserva_id):
    """
    NUEVO: Realizar check-in de una reserva
    """
    reserva = Reserva.get_by_id(reserva_id)
    
    if not reserva:
        return jsonify({'success': False, 'error': 'Reserva no encontrada'}), 404
    
    # Verificar permisos
    if current_user.departamento != reserva.departamento and not current_user.has_role('admin'):
        return jsonify({'success': False, 'error': 'Sin permiso'}), 403
    
    if reserva.hacer_check_in():
        flash('✅ Check-in realizado exitosamente. ¡Disfruta del área!', 'success')
        return jsonify({
            'success': True,
            'check_in': reserva.check_in.strftime('%H:%M')
        })
    else:
        return jsonify({
            'success': False,
            'error': 'No puedes hacer check-in aún. Debe ser 15 minutos antes o después del horario.'
        }), 400


@reservas_bp.route('/check_out/<int:reserva_id>/', methods=['POST'])
@login_required
def check_out(reserva_id):
    """
    NUEVO: Realizar check-out de una reserva
    """
    reserva = Reserva.get_by_id(reserva_id)
    
    if not reserva:
        return jsonify({'success': False, 'error': 'Reserva no encontrada'}), 404
    
    # Verificar permisos
    if current_user.departamento != reserva.departamento and not current_user.has_role('admin'):
        return jsonify({'success': False, 'error': 'Sin permiso'}), 403
    
    if reserva.hacer_check_out():
        flash('✅ Check-out realizado. Gracias por usar nuestras instalaciones.', 'success')
        return jsonify({
            'success': True,
            'check_out': reserva.check_out.strftime('%H:%M')
        })
    else:
        return jsonify({
            'success': False,
            'error': 'No puedes hacer check-out. Debes haber hecho check-in primero.'
        }), 400


# ============================================================================
# SISTEMA DE CALIFICACIONES
# ============================================================================

@reservas_bp.route('/calificar/<int:reserva_id>/', methods=['GET', 'POST'])
@login_required
def calificar_area(reserva_id):
    """
    NUEVO: Calificar un área después de usarla
    """
    reserva = Reserva.get_by_id(reserva_id)
    
    if not reserva:
        flash('❌ Reserva no encontrada.', 'danger')
        return redirect(url_for('reservas.reservas'))
    
    # Verificar permisos
    if current_user.departamento != reserva.departamento:
        flash('❌ No tienes permiso para calificar esta reserva.', 'danger')
        return redirect(url_for('reservas.reservas'))
    
    # Verificar que esté completada
    if reserva.estado != 'completada':
        flash('⚠️ Solo puedes calificar reservas completadas.', 'warning')
        return redirect(url_for('reservas.reservas'))
    
    # Verificar que no esté ya evaluada
    if reserva.evaluada:
        flash('ℹ️ Ya has calificado esta reserva.', 'info')
        return redirect(url_for('reservas.reservas'))
    
    if request.method == 'POST':
        rating = int(request.form.get('rating'))
        comentario = request.form.get('comentario', '')
        limpieza = int(request.form.get('limpieza', 0))
        equipamiento = int(request.form.get('equipamiento', 0))
        ubicacion = int(request.form.get('ubicacion', 0))
        
        # Validar rating
        if rating < 1 or rating > 5:
            flash('❌ La calificación debe estar entre 1 y 5 estrellas.', 'danger')
            return redirect(url_for('reservas.calificar_area', reserva_id=reserva_id))
        
        # Crear rating
        area_rating = AreaRating(
            area_id=reserva.area_id,
            reserva_id=reserva.id,
            departamento=current_user.departamento,
            rating=rating,
            comentario=comentario,
            limpieza=limpieza if limpieza > 0 else None,
            equipamiento=equipamiento if equipamiento > 0 else None,
            ubicacion=ubicacion if ubicacion > 0 else None
        )
        area_rating.save()
        
        flash('✅ ¡Gracias por tu calificación! Nos ayuda a mejorar.', 'success')
        return redirect(url_for('reservas.reservas'))
    
    return render_template('reservas/calificar.html', reserva=reserva)


@reservas_bp.route('/ratings/<int:area_id>/')
@login_required
def ver_ratings(area_id):
    """
    NUEVO: Ver calificaciones de un área
    """
    area = AreaComun.get_by_id(area_id)
    
    if not area:
        flash('❌ Área no encontrada.', 'danger')
        return redirect(url_for('reservas.reservas'))
    
    ratings = AreaRating.get_by_area(area_id)
    
    return render_template('reservas/ratings.html', 
                         area=area,
                         ratings=ratings)


# ============================================================================
# API ENDPOINTS (PARA MÓVIL)
# ============================================================================

@reservas_bp.route('/api/fechas_ocupadas/<int:area_id>/')
@login_required
def fechas_ocupadas(area_id):
    """
    API: Obtener fechas ocupadas de un área
    """
    mes = request.args.get('mes', type=int)
    anio = request.args.get('anio', type=int)
    
    fechas = Reserva.get_fechas_ocupadas(area_id, mes, anio)
    fechas_str = [f.isoformat() for f in fechas]
    
    return jsonify({'fechas': fechas_str})


@reservas_bp.route('/api/horarios_disponibles/<int:area_id>/')
@login_required
def horarios_disponibles(area_id):
    """
    API: Obtener horarios disponibles de un área en una fecha
    """
    fecha_str = request.args.get('fecha')
    
    if not fecha_str:
        return jsonify({'error': 'Fecha no proporcionada'}), 400
    
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    horarios = Reserva.get_horarios_disponibles(area_id, fecha)
    
    return jsonify({'horarios': horarios})


@reservas_bp.route('/api/areas_populares/')
@login_required
def areas_populares():
    """
    NUEVO: API - Obtener áreas más populares
    """
    limit = request.args.get('limit', 5, type=int)
    areas = AreaComun.get_mas_populares(limit)
    
    return jsonify({
        'areas': [a.to_dict() for a in areas]
    })


@reservas_bp.route('/api/mis_reservas/')
@login_required
def mis_reservas_api():
    """
    NUEVO: API - Obtener mis reservas
    """
    if not current_user.departamento:
        return jsonify({'error': 'Sin departamento asignado'}), 400
    
    reservas = Reserva.get_proximas_by_departamento(current_user.departamento)
    
    return jsonify({
        'reservas': [r.to_dict() for r in reservas]
    })


# ============================================================================
# GESTIÓN DE ÁREAS (ADMIN)
# ============================================================================

@reservas_bp.route('/areas/', methods=['GET', 'POST'])
@role_required('admin')
def gestionar_areas():
    """
    Administrar áreas comunes (solo admin)
    """
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        capacidad = int(request.form.get('capacidad', 0))
        costo_hora = float(request.form.get('costo_hora', 0))
        hora_apertura_str = request.form.get('hora_apertura', '08:00')
        hora_cierre_str = request.form.get('hora_cierre', '22:00')
        tiempo_minimo = int(request.form.get('tiempo_minimo', 1))
        tiempo_maximo = int(request.form.get('tiempo_maximo', 8))
        
        # NUEVO: Campos adicionales
        requiere_deposito = request.form.get('requiere_deposito') == 'on'
        monto_deposito = float(request.form.get('monto_deposito', 0))
        equipamiento = request.form.get('equipamiento', '')
        reglas = request.form.get('reglas', '')
        
        try:
            hora_apertura = datetime.strptime(hora_apertura_str, '%H:%M').time()
            hora_cierre = datetime.strptime(hora_cierre_str, '%H:%M').time()
            
            area = AreaComun(
                nombre=nombre,
                descripcion=descripcion,
                capacidad=capacidad,
                costo_hora=costo_hora,
                hora_apertura=hora_apertura,
                hora_cierre=hora_cierre
            )
            area.tiempo_minimo = tiempo_minimo
            area.tiempo_maximo = tiempo_maximo
            area.requiere_deposito = requiere_deposito
            area.monto_deposito = monto_deposito
            area.equipamiento = equipamiento
            area.reglas = reglas
            
            area.save()
            
            flash('✅ Área creada exitosamente.', 'success')
        except Exception as e:
            flash(f'❌ Error al crear área: {str(e)}', 'danger')
        
        return redirect(url_for('reservas.gestionar_areas'))
    
    # GET
    areas = AreaComun.get_all()
    
    return render_template('reservas/areas_admin.html', areas=areas)


@reservas_bp.route('/area/<int:area_id>/editar', methods=['POST'])
@role_required('admin')
def editar_area(area_id):
    """
    Editar un área común
    """
    area = AreaComun.get_by_id(area_id)
    
    if not area:
        flash('❌ Área no encontrada.', 'danger')
        return redirect(url_for('reservas.gestionar_areas'))
    
    try:
        area.nombre = request.form.get('nombre')
        area.descripcion = request.form.get('descripcion')
        area.capacidad = int(request.form.get('capacidad', 0))
        area.costo_hora = float(request.form.get('costo_hora', 0))
        area.hora_apertura = datetime.strptime(request.form.get('hora_apertura'), '%H:%M').time()
        area.hora_cierre = datetime.strptime(request.form.get('hora_cierre'), '%H:%M').time()
        area.tiempo_minimo = int(request.form.get('tiempo_minimo', 1))
        area.tiempo_maximo = int(request.form.get('tiempo_maximo', 8))
        
        # NUEVO: Actualizar campos adicionales
        area.requiere_deposito = request.form.get('requiere_deposito') == 'on'
        area.monto_deposito = float(request.form.get('monto_deposito', 0))
        area.equipamiento = request.form.get('equipamiento', '')
        area.reglas = request.form.get('reglas', '')
        
        area.save()
        
        flash('✅ Área actualizada exitosamente.', 'success')
    except Exception as e:
        flash(f'❌ Error al actualizar área: {str(e)}', 'danger')
    
    return redirect(url_for('reservas.gestionar_areas'))


@reservas_bp.route('/area/<int:area_id>/toggle', methods=['POST'])
@role_required('admin')
def toggle_area(area_id):
    """
    Habilitar/Deshabilitar un área
    """
    area = AreaComun.get_by_id(area_id)
    
    if not area:
        return jsonify({'success': False, 'error': 'Área no encontrada'}), 404
    
    data = request.get_json()
    area.disponible = data.get('disponible', True)
    area.save()
    
    return jsonify({'success': True})