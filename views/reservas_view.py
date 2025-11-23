# ============================================================
# app/views/reservas_view.py
# ============================================================
"""
Vistas de renderizado para reservas
(Las funciones de render están en los controladores directamente)
Este archivo existe para mantener consistencia con la estructura MVC
"""

from flask import render_template
from flask_login import current_user
from datetime import date


def reservas(areas, mis_reservas):
    """Renderiza la vista de reservas para residentes"""
    return render_template(
        'reservas/reservas.html',
        title='Reservar Área Común',
        current_user=current_user,
        areas=areas,
        mis_reservas=mis_reservas,
        fecha_minima=date.today().isoformat()
    )


def reservas_admin(reservas, areas, reservas_pendientes, estado_filtro='todas', area_filtro='todas'):
    """Renderiza la vista de administración de reservas"""
    return render_template(
        'reservas/reservas_admin.html',
        title='Administración de Reservas',
        current_user=current_user,
        reservas=reservas,
        areas=areas,
        reservas_pendientes=reservas_pendientes,
        estado_filtro=estado_filtro,
        area_filtro=area_filtro
    )


def editar_reserva(reserva, areas):
    """Renderiza la vista de edición de reserva"""
    return render_template(
        'reservas/editar_reserva.html',
        title=f'Editar Reserva #{reserva.id}',
        current_user=current_user,
        reserva=reserva,
        areas=areas,
        fecha_minima=date.today().isoformat()
    )


def gestionar_areas(areas):
    """Renderiza la vista de gestión de áreas comunes"""
    return render_template(
        'reservas/areas_admin.html',
        title='Gestión de Áreas Comunes',
        current_user=current_user,
        areas=areas
    )
