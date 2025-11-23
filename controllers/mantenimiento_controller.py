from flask import Blueprint, request, redirect, url_for, flash, Response, current_app
from models.mantenimiento_model import Mantenimiento
from views import mantenimiento_view
from datetime import datetime
from werkzeug.utils import secure_filename
import os
# Importar el decorador de roles y login_required
from utils.decorators import role_required
from flask_login import login_required, current_user 

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from io import BytesIO

mantenimiento_bp = Blueprint("mantenimiento", __name__)

# Configuración de subida de archivos
UPLOAD_FOLDER = 'static/uploads/evidencias'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_socketio():
    """Obtener instancia de socketio desde el contexto de la app"""
    # Usar get en lugar de un acceso directo para evitar errores si no está cargado
    return current_app.extensions.get('socketio')

@mantenimiento_bp.route("/mantenimiento")
@login_required # Todos los usuarios logueados pueden ver la lista
def list_mantenimiento():
    mantenimientos = Mantenimiento.get_all()
    return mantenimiento_view.list_ticket(mantenimientos)

@mantenimiento_bp.route("/mantenimiento/crear", methods=["GET", "POST"])
@login_required # Todos los usuarios logueados pueden crear tickets
def create_ticket():
    if request.method == "POST":
        descripcion = request.form["descripcion"]
        prioridad = request.form["prioridad"]

        ticket = Mantenimiento(descripcion=descripcion, prioridad=prioridad)
        ticket.save()
        
        # Notificar al admin sobre el nuevo ticket
        socketio = get_socketio()
        if socketio:
            # Importar localmente para evitar problemas de dependencia circular
            from socket_events import notify_new_ticket 
            notify_new_ticket(socketio, ticket)
        
        flash("Ticket creado correctamente.", "success")
        return redirect(url_for("mantenimiento.list_mantenimiento"))
    
    return mantenimiento_view.crear_ticket()

@mantenimiento_bp.route("/mantenimiento/actualizar_ini/<int:id>", methods=["GET", "POST"])
@role_required('admin') # Solo los administradores pueden iniciar el mantenimiento
def update_ticket_ini(id):
    ticket = Mantenimiento.get_by_id(id)
    if not ticket:
        flash("Ticket no encontrado.", "error")
        return redirect(url_for("mantenimiento.list_mantenimiento"))
    
    if request.method == "POST":
        responsable = request.form.get("responsable")
        fecha_ini_str = request.form.get("fecha_ini")
        fecha_fin_str = request.form.get("fecha_fin")
        costo_str = request.form.get("costo")
        prioridad = request.form.get("prioridad")

        try:
            fecha_ini = datetime.strptime(fecha_ini_str, "%Y-%m-%d").date() if fecha_ini_str else None
            fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date() if fecha_fin_str else None
            costo = float(costo_str) if costo_str else None

            ticket.update_mantenimiento_inicio(
                responsable=responsable, 
                fecha_ini=fecha_ini, 
                fecha_fin=fecha_fin, 
                costo=costo, 
                prioridad=prioridad
            )

            # Notificar actualización
            socketio = get_socketio()
            if socketio:
                from socket_events import notify_ticket_updated
                notify_ticket_updated(socketio, ticket, 'iniciado')

            flash("Ticket actualizado correctamente.", "success")
            return redirect(url_for("mantenimiento.list_mantenimiento"))
        except Exception as e:
            # Usar 'danger' o 'error' para mensajes de fallo
            flash(f"Error al actualizar el ticket: {str(e)}", "danger") 
    
    return mantenimiento_view.update_ticket_ini(ticket)

@mantenimiento_bp.route("/mantenimiento/actualizar_fin/<int:id>", methods=["GET", "POST"])
@role_required('admin') # Solo los administradores pueden finalizar el mantenimiento
def update_ticket_fin(id):
    ticket = Mantenimiento.get_by_id(id)
    if not ticket:
        flash("Ticket no encontrado.", "error")
        return redirect(url_for("mantenimiento.list_mantenimiento"))
    
    if request.method == "POST":
        # Se asegura que el valor 'si' se traduzca a True
        trabajo_realizado = request.form.get("trabajo_realizado") == "si" 
        
        # Manejo de archivo de evidencia
        evidencia_url = ticket.evidencia_url
        if 'evidencia_url' in request.files:
            file = request.files['evidencia_url']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    # Uso de current_user.id para asegurar unicidad del nombre de archivo
                    filename = secure_filename(f"ticket_{id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                    
                    # Crear directorio si no existe (ya se hace en run.py, pero es buena práctica)
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    # La URL pública debe coincidir con la configuración del servidor web
                    evidencia_url = f"/static/uploads/evidencias/{filename}" 
                else:
                    flash("Tipo de archivo no permitido para la evidencia.", "danger")
                    return redirect(url_for("mantenimiento.update_ticket_fin", id=id))

        try:
            ticket.update_mantenimiento_fin(
                trabajo_realizado=trabajo_realizado, 
                evidencia_url=evidencia_url
            )
            
            # Notificar finalización
            socketio = get_socketio()
            if socketio:
                from socket_events import notify_ticket_updated
                notify_ticket_updated(socketio, ticket, 'finalizado')
            
            flash("Ticket finalizado correctamente.", "success")
            return redirect(url_for("mantenimiento.list_mantenimiento"))
        except Exception as e:
            flash(f"Error al finalizar el ticket: {str(e)}", "danger")
    
    return mantenimiento_view.update_ticket_fin(ticket)

@mantenimiento_bp.route("/mantenimiento/delete/<int:id>", methods=["POST"])
@role_required('admin') # Solo los administradores pueden eliminar tickets
def delete_ticket(id):
    ticket = Mantenimiento.get_by_id(id)
    if not ticket:
        flash("Ticket no encontrado.", "error")
        return redirect(url_for("mantenimiento.list_mantenimiento"))
    
    # Notificar eliminación antes de borrar
    socketio = get_socketio()
    if socketio:
        from socket_events import notify_ticket_updated
        notify_ticket_updated(socketio, ticket, 'eliminado')
    
    ticket.delete()
    flash("Ticket eliminado correctamente.", "success")
    return redirect(url_for("mantenimiento.list_mantenimiento"))

@mantenimiento_bp.route("/mantenimiento/ticket/<int:id>")
@login_required # Todos los usuarios logueados pueden ver el detalle
def generate_ticket(id):
    ticket = Mantenimiento.get_by_id(id)
    if not ticket:
        flash("Ticket no encontrado.", "error")
        return redirect(url_for("mantenimiento.list_mantenimiento"))
    
    # Renderiza la vista de detalle (no genera el PDF todavía)
    return mantenimiento_view.generate_ticket(ticket) 

# Esta ruta genera el PDF
@mantenimiento_bp.route("/mantenimiento/ticket/<int:id>/download")
@login_required # Protección de ruta de descarga
def download_report(id):
    ticket = Mantenimiento.get_by_id(id)
    if not ticket:
        flash("Ticket no encontrado.", "error")
        return redirect(url_for("mantenimiento.list_mantenimiento"))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    # Configurar el estilo del título
    title_style.alignment = 1 # Centro

    # Título
    elements.append(Paragraph("REPORTE DE MANTENIMIENTO", title_style))
    elements.append(Spacer(1, 0.3*inch))

    # Crear tabla con la información
    data = [
        ['ID Ticket:', str(ticket.id_mantenimiento)],
        ['Descripción:', ticket.descripcion or 'N/A'],
        ['Prioridad:', ticket.prioridad or 'N/A'],
        ['Responsable:', ticket.responsable or 'N/A'],
        ['Fecha Inicio:', str(ticket.fecha_ini) if ticket.fecha_ini else 'N/A'],
        ['Fecha Fin:', str(ticket.fecha_fin) if ticket.fecha_fin else 'N/A'],
        ['Costo:', f'${ticket.costo}' if ticket.costo else 'N/A'],
        ['Trabajo Realizado:', 'Sí' if ticket.trabajo_realizado else 'No'],
        ['Evidencia:', 'Disponible' if ticket.evidencia_url else 'No disponible'],
    ]

    table = Table(data, colWidths=[2*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return Response(
        buffer, 
        mimetype='application/pdf', 
        headers={"Content-Disposition": f"attachment;filename=ticket_{ticket.id_mantenimiento}.pdf"}
    )