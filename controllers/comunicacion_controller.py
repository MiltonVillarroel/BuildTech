# app/controllers/comunicacion_controller.py
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from models.chat_model import ChatMessage, Notification
from models.comunicacion_model import Aviso, Queja
from models.mantenimiento_model import Mantenimiento
from flask_login import login_required, current_user
from utils.decorators import role_required

comunicacion_bp = Blueprint("comunicacion", __name__, url_prefix="/comunicacion")

def get_socketio():
    """Obtener instancia de socketio desde el contexto de la app"""
    return current_app.extensions.get('socketio')

# ============= CHAT =============

@comunicacion_bp.route("/chat")
@login_required
def chat_general():
    """Chat general del sistema"""
    username = current_user.first_name if current_user.is_authenticated else 'Anónimo'
    return render_template(
        "comunicacion/chat.html",
        title="Chat General",
        current_username=username 
    )

@comunicacion_bp.route("/chat/ticket/<int:ticket_id>")
@login_required
def chat_ticket(ticket_id):
    """Chat específico de un ticket"""
    ticket = Mantenimiento.get_by_id(ticket_id)
    if not ticket:
        flash("Ticket no encontrado", "error")
        return redirect(url_for('mantenimiento.list_mantenimiento'))
    
    username = current_user.first_name if current_user.is_authenticated else 'Anónimo'
    
    return render_template(
        "comunicacion/chat_ticket.html",
        title=f"Chat - Ticket #{ticket_id}",
        ticket=ticket,
        current_username=username 
    )

# ============= AVISOS =============

@comunicacion_bp.route("/avisos")
@login_required
def avisos():
    """Ver todos los avisos activos"""
    avisos = Aviso.get_all_activos()
    return render_template(
        "comunicacion/avisos.html",
        title="Avisos Importantes",
        avisos=avisos
    )

@comunicacion_bp.route("/avisos/crear", methods=["GET", "POST"])
@role_required('admin')
def crear_aviso():
    """Crear un nuevo aviso (solo admin)"""
    if request.method == "POST":
        titulo = request.form.get("titulo")
        contenido = request.form.get("contenido")
        categoria = request.form.get("categoria")
        
        if not titulo or not contenido or not categoria:
            flash("Todos los campos son obligatorios", "danger")
            return redirect(url_for('comunicacion.crear_aviso'))
        
        autor = f"{current_user.first_name} {current_user.last_name}"
        aviso = Aviso(titulo=titulo, contenido=contenido, categoria=categoria, autor=autor)
        aviso.save()
        
        flash("Aviso publicado exitosamente", "success")
        return redirect(url_for('comunicacion.avisos'))
    
    return render_template("comunicacion/crear_aviso.html", title="Crear Aviso")

@comunicacion_bp.route("/avisos/<int:aviso_id>/archivar", methods=["POST"])
@role_required('admin')
def archivar_aviso(aviso_id):
    """Archivar un aviso (no lo elimina)"""
    aviso = Aviso.get_by_id(aviso_id)
    if not aviso:
        flash("Aviso no encontrado", "error")
        return redirect(url_for('comunicacion.avisos'))
    
    aviso.archivar()
    flash("Aviso archivado correctamente", "success")
    return redirect(url_for('comunicacion.avisos'))

@comunicacion_bp.route("/avisos/<int:aviso_id>/reactivar", methods=["POST"])
@role_required('admin')
def reactivar_aviso(aviso_id):
    """Reactivar un aviso archivado"""
    aviso = Aviso.get_by_id(aviso_id)
    if not aviso:
        flash("Aviso no encontrado", "error")
        return redirect(url_for('comunicacion.avisos_archivados'))
    
    aviso.reactivar()
    flash("Aviso reactivado correctamente", "success")
    return redirect(url_for('comunicacion.avisos'))

@comunicacion_bp.route("/avisos/archivados")
@role_required('admin')
def avisos_archivados():
    """Ver avisos archivados (solo admin)"""
    avisos = [a for a in Aviso.get_all() if not a.activo]
    return render_template(
        "comunicacion/avisos_archivados.html",
        title="Avisos Archivados",
        avisos=avisos
    )

# ============= QUEJAS =============

@comunicacion_bp.route("/quejas")
@login_required
def quejas():
    """Ver quejas (admin ve todas, usuarios solo las suyas)"""
    if current_user.has_role('admin'):
        quejas = Queja.get_all()
    else:
        # Usuarios ven solo las quejas que enviaron con su nombre
        autor_nombre = f"{current_user.first_name} {current_user.last_name}"
        quejas = [q for q in Queja.get_all() if q.autor == autor_nombre]
    
    return render_template(
        "comunicacion/quejas.html",
        title="Quejas y Sugerencias",
        quejas=quejas
    )

@comunicacion_bp.route("/quejas/crear", methods=["GET", "POST"])
@login_required
def crear_queja():
    """Crear una nueva queja"""
    if request.method == "POST":
        contenido = request.form.get("contenido")
        categoria = request.form.get("categoria")
        anonima = request.form.get("anonima") == "si"
        
        if not contenido or not categoria:
            flash("Por favor complete todos los campos obligatorios", "danger")
            return redirect(url_for('comunicacion.crear_queja'))
        
        autor = None if anonima else f"{current_user.first_name} {current_user.last_name}"
        queja = Queja(contenido=contenido, categoria=categoria, anonima=anonima, autor=autor)
        queja.save()
        
        # Notificar a los admins sobre la nueva queja
        socketio = get_socketio()
        if socketio:
            from socket_events import notify_new_queja
            notify_new_queja(socketio, queja)
        
        flash("Queja enviada exitosamente. Será revisada por un administrador", "success")
        return redirect(url_for('comunicacion.quejas'))
    
    return render_template("comunicacion/crear_queja.html", title="Enviar Queja")

@comunicacion_bp.route("/quejas/<int:queja_id>")
@login_required
def ver_queja(queja_id):
    """Ver detalle de una queja"""
    queja = Queja.get_by_id(queja_id)
    if not queja:
        flash("Queja no encontrada", "error")
        return redirect(url_for('comunicacion.quejas'))
    
    # Verificar permisos: admin puede ver todas, usuario solo las suyas no anónimas
    if not current_user.has_role('admin'):
        autor_nombre = f"{current_user.first_name} {current_user.last_name}"
        if queja.anonima or queja.autor != autor_nombre:
            flash("No tienes permiso para ver esta queja", "danger")
            return redirect(url_for('comunicacion.quejas'))
    
    return render_template(
        "comunicacion/ver_queja.html",
        title=f"Queja #{queja_id}",
        queja=queja
    )

@comunicacion_bp.route("/quejas/<int:queja_id>/responder", methods=["GET", "POST"])
@role_required('admin')
def responder_queja(queja_id):
    """Responder a una queja (solo admin)"""
    queja = Queja.get_by_id(queja_id)
    if not queja:
        flash("Queja no encontrada", "error")
        return redirect(url_for('comunicacion.quejas'))
    
    if request.method == "POST":
        respuesta = request.form.get("respuesta")
        
        if not respuesta:
            flash("La respuesta no puede estar vacía", "danger")
            return redirect(url_for('comunicacion.responder_queja', queja_id=queja_id))
        
        admin_nombre = f"{current_user.first_name} {current_user.last_name}"
        queja.responder(respuesta, admin_nombre)
        
        flash("Respuesta enviada exitosamente", "success")
        return redirect(url_for('comunicacion.ver_queja', queja_id=queja_id))
    
    return render_template(
        "comunicacion/responder_queja.html",
        title="Responder Queja",
        queja=queja
    )

@comunicacion_bp.route("/quejas/<int:queja_id>/estado", methods=["POST"])
@role_required('admin')
def cambiar_estado_queja(queja_id):
    """Cambiar el estado de una queja (solo admin)"""
    queja = Queja.get_by_id(queja_id)
    if not queja:
        return jsonify({'success': False, 'error': 'Queja no encontrada'}), 404
    
    nuevo_estado = request.json.get('estado')
    if queja.cambiar_estado(nuevo_estado):
        return jsonify({'success': True, 'nuevo_estado': nuevo_estado})
    else:
        return jsonify({'success': False, 'error': 'Estado inválido'}), 400

# ============= NOTIFICACIONES =============

@comunicacion_bp.route("/notificaciones")
@role_required('admin')
def notificaciones():
    """Ver todas las notificaciones"""
    notificaciones = Notification.get_all()
    return render_template(
        "comunicacion/notificaciones.html",
        title="Notificaciones",
        notificaciones=notificaciones
    )

@comunicacion_bp.route("/api/notificaciones/no-leidas")
@login_required
def notificaciones_no_leidas():
    """API: Obtener notificaciones no leídas"""
    if current_user.has_role('admin'):
        notificaciones = Notification.get_no_leidas()
        return jsonify({
            'count': len(notificaciones),
            'notificaciones': [n.to_dict() for n in notificaciones]
        })
    return jsonify({'count': 0, 'notificaciones': []})

@comunicacion_bp.route("/api/notificaciones/<int:id>/marcar-leida", methods=["POST"])
@login_required
def marcar_notificacion_leida(id):
    """API: Marcar notificación como leída"""
    if not current_user.has_role('admin'):
        return jsonify({'success': False, 'error': 'Permiso denegado'}), 403
        
    notificacion = Notification.query.get(id)
    if notificacion:
        notificacion.marcar_leido()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Notificación no encontrada'}), 404