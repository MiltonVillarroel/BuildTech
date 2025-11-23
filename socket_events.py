from flask_socketio import emit, join_room, leave_room
from models.chat_model import ChatMessage, Notification
from models.mantenimiento_model import Mantenimiento

def register_socket_events(socketio):
    """Registrar todos los eventos de Socket.IO"""
    
    @socketio.on('connect')
    def handle_connect():
        print('Cliente conectado')
        emit('connection_response', {'data': 'Conectado al servidor'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print('Cliente desconectado')
    
    # ============= CHAT GENERAL =============
    
    @socketio.on('join_general_chat')
    def handle_join_general():
        """Usuario se une al chat general"""
        join_room('general')
        print('Usuario se unió al chat general')
        
        # Enviar mensajes recientes
        messages = ChatMessage.get_recent(50)
        messages_data = [msg.to_dict() for msg in reversed(messages)]
        emit('load_messages', messages_data)
    
    @socketio.on('send_message')
    def handle_send_message(data):
        """Enviar mensaje al chat general"""
        content = data.get('message')
        username = data.get('username', 'Anónimo')
        
        if not content:
            return
        
        # Guardar en base de datos
        message = ChatMessage(content=content, username=username)
        message.save()
        
        # Broadcast a todos en el chat general
        emit('new_message', message.to_dict(), room='general', broadcast=True)
    
    # ============= CHAT DE TICKET =============
    
    @socketio.on('join_ticket_chat')
    def handle_join_ticket(data):
        """Usuario se une al chat de un ticket específico"""
        ticket_id = data.get('ticket_id')
        room = f'ticket_{ticket_id}'
        join_room(room)
        print(f'Usuario se unió al chat del ticket {ticket_id}')
        
        # Enviar mensajes del ticket
        messages = ChatMessage.get_by_ticket(ticket_id)
        messages_data = [msg.to_dict() for msg in messages]
        emit('load_messages', messages_data)
    
    @socketio.on('send_ticket_message')
    def handle_send_ticket_message(data):
        """Enviar mensaje al chat de un ticket"""
        content = data.get('message')
        username = data.get('username', 'Anónimo')
        ticket_id = data.get('ticket_id')
        
        if not content or not ticket_id:
            return
        
        # Guardar en base de datos
        message = ChatMessage(content=content, username=username, ticket_id=ticket_id)
        message.save()
        
        # Broadcast a todos en ese chat de ticket
        room = f'ticket_{ticket_id}'
        emit('new_message', message.to_dict(), room=room, broadcast=True)
    
    @socketio.on('leave_ticket_chat')
    def handle_leave_ticket(data):
        """Usuario sale del chat de un ticket"""
        ticket_id = data.get('ticket_id')
        room = f'ticket_{ticket_id}'
        leave_room(room)
        print(f'Usuario salió del chat del ticket {ticket_id}')
    
    # ============= NOTIFICACIONES =============
    
    @socketio.on('join_notifications')
    def handle_join_notifications():
        """Unirse a la sala de notificaciones (admin)"""
        join_room('admin_notifications')
        print('Admin se unió a notificaciones')
        
        # Enviar notificaciones no leídas
        notifications = Notification.get_no_leidas()
        emit('unread_notifications', {
            'count': len(notifications),
            'notifications': [n.to_dict() for n in notifications]
        })
    
    @socketio.on('mark_notification_read')
    def handle_mark_read(data):
        """Marcar notificación como leída"""
        notification_id = data.get('notification_id')
        notification = Notification.query.get(notification_id)
        
        if notification:
            notification.marcar_leido()
            emit('notification_marked', {'id': notification_id})

def notify_new_ticket(socketio, ticket):
    """Notificar a los admins sobre un nuevo ticket"""
    notification = Notification(
        tipo='nuevo_ticket',
        mensaje=f'Nuevo ticket creado: {ticket.descripcion[:50]}...',
        ticket_id=ticket.id_mantenimiento
    )
    notification.save()
    
    # Emitir notificación a todos los admins
    socketio.emit('new_notification', notification.to_dict(), room='admin_notifications')

def notify_ticket_updated(socketio, ticket, tipo_actualizacion):
    """Notificar sobre actualización de ticket"""
    mensajes = {
        'iniciado': f'Ticket #{ticket.id_mantenimiento} iniciado por {ticket.responsable}',
        'finalizado': f'Ticket #{ticket.id_mantenimiento} finalizado',
        'eliminado': f'Ticket #{ticket.id_mantenimiento} eliminado'
    }
    
    notification = Notification(
        tipo='ticket_actualizado',
        mensaje=mensajes.get(tipo_actualizacion, 'Ticket actualizado'),
        ticket_id=ticket.id_mantenimiento
    )
    notification.save()
    
    socketio.emit('new_notification', notification.to_dict(), room='admin_notifications')

def notify_new_queja(socketio, queja):
    """Notificar a los admins sobre una nueva queja"""
    autor = queja.autor if not queja.anonima else 'Anónimo'
    notification = Notification(
        tipo='nueva_queja',
        mensaje=f'Nueva queja recibida de {autor} - Categoría: {queja.categoria}',
        ticket_id=None  # Las quejas no están relacionadas con tickets
    )
    notification.save()
    
    # Emitir notificación a todos los admins
    socketio.emit('new_notification', notification.to_dict(), room='admin_notifications')