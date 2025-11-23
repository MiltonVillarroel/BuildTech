# ============================================================
# app/views/finanzas_view.py
# ============================================================
"""
Vistas de renderizado para finanzas
(Las funciones de render están en los controladores directamente)
Este archivo existe para mantener consistencia con la estructura MVC
"""

from flask import render_template
from flask_login import current_user


def resumen_financiero(context):
    """Renderiza el resumen financiero"""
    return render_template(
        'finanzas/resumen.html',
        title='Resumen Financiero',
        current_user=current_user,
        **context
    )


def cargos_departamento(context):
    """Renderiza los cargos de un departamento"""
    return render_template(
        'finanzas/cargos_departamento.html',
        title=f'Cargos Departamento {context.get("departamento")}',
        current_user=current_user,
        **context
    )


def pagar_pendiente(context):
    """Renderiza la vista de pago"""
    return render_template(
        'finanzas/pagar_pendiente.html',
        title='Pagar Cargo Pendiente',
        current_user=current_user,
        **context
    )


def gastos(context):
    """Renderiza la vista de gestión de gastos"""
    return render_template(
        'finanzas/gastos.html',
        title='Gestión de Gastos',
        current_user=current_user,
        **context
    )