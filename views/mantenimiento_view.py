# views/mantenimiento_view.py - CORREGIDO
from flask import render_template, url_for

def crear_ticket():
    return render_template(
        "mantenimiento/crear.html",  # ✅ CORREGIDO: era maintenance/
        title="Crear ticket"
    )

def list_ticket(tickets):
    return render_template(
        "mantenimiento/list_tickets.html",  # ✅ CORREGIDO: era maintenance/
        tickets=tickets,
        title="Lista de tickets"
    )

def update_ticket_ini(ticket):
    return render_template(
        "mantenimiento/actualizar_ini.html",  # ✅ CORREGIDO: era maintenance/
        title="Actualizar ticket",
        ticket=ticket
    )

def update_ticket_fin(ticket):
    return render_template(
        "mantenimiento/actualizar_fin.html",  # ✅ CORREGIDO: era maintenance/
        title="Finalizar ticket",
        ticket=ticket
    )

def generate_ticket(ticket):
    return render_template(
        "mantenimiento/generate_ticket.html",  # ✅ CORREGIDO: era maintenance/
        title="Ticket",
        ticket=ticket,
        download_url=url_for('mantenimiento.download_report', id=ticket.id_mantenimiento)
    )