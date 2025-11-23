# app/utils/email_utils.py
"""
Utilidades para envío de correos electrónicos
IMPORTANTE: Configurar variables de entorno antes de usar
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ✅ SEGURIDAD: Usar variables de entorno en lugar de hardcodear credenciales
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
EMAIL_USER = os.environ.get('EMAIL_USER', '')  # Configurar en entorno
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')  # Configurar en entorno
DEFAULT_FROM = os.environ.get('EMAIL_FROM', 'BuildTech <noreply@buildtech.com>')

# Flag para habilitar/deshabilitar emails (útil en desarrollo)
EMAIL_ENABLED = os.environ.get('EMAIL_ENABLED', 'False').lower() == 'true'


def enviar_email(destinatario, asunto, cuerpo_html, cuerpo_texto=None):
    """
    Envía un email
    
    Args:
        destinatario: Email del destinatario
        asunto: Asunto del email
        cuerpo_html: Cuerpo del mensaje en HTML
        cuerpo_texto: Cuerpo del mensaje en texto plano (opcional)
    
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    # Si los emails están deshabilitados, solo registrar en consola
    if not EMAIL_ENABLED:
        print(f"\n{'='*70}")
        print(f"📧 EMAIL (modo desarrollo - no enviado)")
        print(f"{'='*70}")
        print(f"Para: {destinatario}")
        print(f"Asunto: {asunto}")
        print(f"{'='*70}\n")
        return True
    
    # Validar configuración
    if not EMAIL_USER or not EMAIL_PASSWORD:
        print("⚠️ Advertencia: Credenciales de email no configuradas")
        print("   Configura EMAIL_USER y EMAIL_PASSWORD en variables de entorno")
        return False
    
    try:
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['From'] = DEFAULT_FROM
        msg['To'] = destinatario
        msg['Subject'] = asunto
        
        # Agregar versión texto plano
        if cuerpo_texto:
            part1 = MIMEText(cuerpo_texto, 'plain', 'utf-8')
            msg.attach(part1)
        
        # Agregar versión HTML
        part2 = MIMEText(cuerpo_html, 'html', 'utf-8')
        msg.attach(part2)
        
        # Conectar y enviar
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, destinatario, msg.as_string())
        server.quit()
        
        print(f"✅ Email enviado exitosamente a {destinatario}")
        return True
        
    except Exception as e:
        print(f"❌ Error al enviar email a {destinatario}: {str(e)}")
        return False


def enviar_email_confirmacion_reserva(reserva):
    """
    Envía un email de confirmación de reserva
    """
    if not reserva.email:
        print(f"⚠️ Reserva #{reserva.id} no tiene email configurado")
        return False
    
    asunto = f"Confirmación de Reserva - {reserva.area.nombre}"
    
    cuerpo_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; }}
            .header {{ color: #0d6efd; text-align: center; margin-bottom: 20px; }}
            .details {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            .details p {{ margin: 10px 0; }}
            .footer {{ margin-top: 30px; text-align: center; color: #666; font-size: 0.9em; }}
            .important {{ background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2 class="header">🎉 Reserva Confirmada</h2>
            
            <p>Estimado/a <strong>{reserva.usuario}</strong>,</p>
            
            <p>Tu reserva ha sido registrada exitosamente. A continuación los detalles:</p>
            
            <div class="details">
                <p><strong>📍 Área:</strong> {reserva.area.nombre}</p>
                <p><strong>📅 Fecha:</strong> {reserva.fecha.strftime('%d/%m/%Y')}</p>
                <p><strong>🕐 Horario:</strong> {reserva.hora_inicio.strftime('%H:%M')} - {reserva.hora_fin.strftime('%H:%M')}</p>
                <p><strong>👥 Personas:</strong> {reserva.num_personas}</p>
                <p><strong>💰 Costo:</strong> Bs. {reserva.costo_total:.2f}</p>
                <p><strong>📋 Estado:</strong> {reserva.estado.upper()}</p>
            </div>
            
            <div class="important">
                <p><strong>⚠️ Importante:</strong></p>
                <ul>
                    <li>Recuerda realizar el pago antes de la fecha de tu reserva</li>
                    <li>Llega 10 minutos antes del horario reservado</li>
                    <li>Cuida las instalaciones y deja todo en orden</li>
                </ul>
            </div>
            
            <div class="footer">
                <p><small>BuildTech - Sistema de Gestión Integral</small></p>
                <p><small>Este es un mensaje automático, por favor no responder</small></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    cuerpo_texto = f"""
CONFIRMACIÓN DE RESERVA

Estimado/a {reserva.usuario},

Tu reserva ha sido registrada exitosamente.

DETALLES:
- Área: {reserva.area.nombre}
- Fecha: {reserva.fecha.strftime('%d/%m/%Y')}
- Horario: {reserva.hora_inicio.strftime('%H:%M')} - {reserva.hora_fin.strftime('%H:%M')}
- Personas: {reserva.num_personas}
- Costo: Bs. {reserva.costo_total:.2f}
- Estado: {reserva.estado.upper()}

IMPORTANTE:
- Recuerda realizar el pago antes de la fecha de tu reserva
- Llega 10 minutos antes del horario reservado
- Cuida las instalaciones y deja todo en orden

BuildTech - Sistema de Gestión Integral
    """
    
    return enviar_email(reserva.email, asunto, cuerpo_html, cuerpo_texto)


def enviar_email_pago_confirmado(cargo_o_pago, tipo='cargo_mensual'):
    """
    Envía un email cuando se confirma un pago
    """
    # TODO: Implementar según necesidades
    print(f"📧 Email de pago confirmado para {tipo} (pendiente de implementar)")
    return True


def enviar_email_recordatorio_pago(departamento, cargos_pendientes):
    """
    Envía un recordatorio de pagos pendientes
    """
    # TODO: Implementar según necesidades
    print(f"📧 Email de recordatorio para Dpto {departamento} (pendiente de implementar)")
    return True


# ✅ Función para configurar emails desde archivo .env
def configurar_email_desde_env():
    """
    Muestra cómo configurar las variables de entorno necesarias
    """
    instrucciones = """
    ╔═══════════════════════════════════════════════════════════╗
    ║          CONFIGURACIÓN DE EMAIL - BuildTech              ║
    ╚═══════════════════════════════════════════════════════════╝
    
    Para habilitar el envío de emails, configura estas variables:
    
    1. Crear archivo .env en la raíz del proyecto:
    
       EMAIL_ENABLED=true
       SMTP_SERVER=smtp.gmail.com
       SMTP_PORT=587
       EMAIL_USER=tu_email@gmail.com
       EMAIL_PASSWORD=tu_password_de_aplicacion
       EMAIL_FROM=BuildTech <noreply@buildtech.com>
    
    2. Para Gmail, necesitas crear una "Contraseña de aplicación":
       - Ve a tu cuenta de Google
       - Seguridad > Verificación en dos pasos
       - Contraseñas de aplicaciones
       - Genera una nueva contraseña
    
    3. Instalar python-dotenv:
       pip install python-dotenv
    
    4. En run.py, cargar variables al inicio:
       from dotenv import load_dotenv
       load_dotenv()
    
    ═══════════════════════════════════════════════════════════
    """
    print(instrucciones)


if __name__ == '__main__':
    # Mostrar instrucciones si se ejecuta directamente
    configurar_email_desde_env()