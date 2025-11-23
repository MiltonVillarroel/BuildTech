# app/controllers/finanzas_controller.py - VERSIÓN MEJORADA
"""
Controlador de Finanzas - Mejorado con funcionalidades completas
Gestión de cargos mensuales, pagos, gastos y reportes financieros
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from utils.decorators import role_required
from models.finanzas_model import CargoMensual, PagoReserva, GastoEdificio, HistorialPago
from models.reservas_model import Reserva
from models.user_model import User
from datetime import date, datetime
from decimal import Decimal
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

finanzas_bp = Blueprint('finanzas', __name__, url_prefix='/financiera')

# ============================================================================
# RESUMEN FINANCIERO
# ============================================================================

@finanzas_bp.route('/')
@role_required('admin')
def resumen_financiero():
    """
    Vista del resumen financiero general (solo admin)
    Mejorado con más estadísticas y gráficos
    """
    hoy = date.today()
    mes_actual = hoy.month
    anio_actual = hoy.year
    
    # Obtener cargos mensuales
    cargos_pendientes = CargoMensual.get_all_pendientes()
    total_pendiente_cargos = sum(cargo.total for cargo in cargos_pendientes)
    
    # Obtener pagos de reservas pendientes
    pagos_reservas_pendientes = PagoReserva.get_pendientes()
    total_pendiente_reservas = sum(float(pago.monto) for pago in pagos_reservas_pendientes)
    
    # Calcular ingresos del mes actual
    ingresos_cargos = CargoMensual.get_total_recaudado_mes(mes_actual, anio_actual)
    ingresos_reservas = PagoReserva.get_total_recaudado_reservas(mes_actual, anio_actual)
    total_ingresos = ingresos_cargos + ingresos_reservas
    
    # Calcular gastos del mes actual
    gastos_mes = GastoEdificio.get_by_mes(mes_actual, anio_actual)
    total_gastos = sum(float(gasto.monto) for gasto in gastos_mes)
    
    # Balance
    balance = total_ingresos - total_gastos
    
    # Historial reciente
    historial_reciente = HistorialPago.get_all()[:10]
    
    # NUEVO: Estadísticas adicionales
    total_departamentos = len(set([c.departamento for c in CargoMensual.get_all()]))
    tasa_morosidad = (len(cargos_pendientes) / max(total_departamentos, 1)) * 100
    
    # NUEVO: Gastos por categoría
    gastos_por_categoria = {}
    for gasto in gastos_mes:
        cat = gasto.categoria
        gastos_por_categoria[cat] = gastos_por_categoria.get(cat, 0) + float(gasto.monto)
    
    # NUEVO: Proyección mensual
    promedio_ingresos = ingresos_cargos / max(len(set([c.departamento for c in CargoMensual.get_by_mes_pagados(mes_actual, anio_actual)])), 1)
    ingreso_proyectado = promedio_ingresos * total_departamentos
    
    context = {
        'mes_actual': datetime(anio_actual, mes_actual, 1).strftime('%B %Y'),
        'total_pendiente_cargos': total_pendiente_cargos,
        'total_pendiente_reservas': total_pendiente_reservas,
        'cargos_pendientes': cargos_pendientes,
        'pagos_reservas_pendientes': pagos_reservas_pendientes,
        'ingresos_cargos': ingresos_cargos,
        'ingresos_reservas': ingresos_reservas,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'balance': balance,
        'gastos_mes': gastos_mes,
        'historial_reciente': historial_reciente,
        # Nuevas estadísticas
        'total_departamentos': total_departamentos,
        'tasa_morosidad': round(tasa_morosidad, 2),
        'gastos_por_categoria': gastos_por_categoria,
        'ingreso_proyectado': ingreso_proyectado,
    }
    
    return render_template('finanzas/resumen.html', **context)


# ============================================================================
# CARGOS MENSUALES POR DEPARTAMENTO
# ============================================================================

@finanzas_bp.route('/cargos_mensuales/dpto/<int:departamento_id>/')
@login_required
def calcular_cargos_mensuales(departamento_id):
    """
    Vista de cargos mensuales de un departamento específico
    Mejorado con más información y opciones de pago
    """
    # Verificar permisos
    if not current_user.has_role('admin'):
        if current_user.departamento != departamento_id:
            flash('No tienes permiso para ver esta información.', 'danger')
            return redirect(url_for('auth.home'))
    
    # Obtener información del departamento/usuario
    usuario_dpto = User.query.filter_by(departamento=departamento_id).first()
    
    # Obtener o crear cargo del mes actual
    cargo_mes_actual = CargoMensual.get_or_create_mes_actual(departamento_id)
    
    # Obtener todos los cargos pendientes
    cargos_pendientes = CargoMensual.get_pendientes_by_departamento(departamento_id)
    
    # Obtener historial de pagos
    historial = HistorialPago.get_by_departamento(departamento_id)
    
    # Obtener pagos de reservas pendientes
    reservas_pendientes = []
    if hasattr(current_user, 'departamento') and current_user.departamento == departamento_id:
        reservas = Reserva.get_by_departamento(departamento_id)
        for reserva in reservas:
            pago = PagoReserva.get_by_reserva(reserva.id)
            if pago and not pago.pagado:
                reservas_pendientes.append({
                    'reserva': reserva,
                    'pago': pago
                })
    
    # Calcular totales
    total_pendiente = sum(cargo.total for cargo in cargos_pendientes)
    total_reservas_pendiente = sum(item['pago'].monto for item in reservas_pendientes)
    total_pagado = sum(h.monto for h in historial)
    
    # NUEVO: Estadísticas del departamento
    meses_con_deuda = len(cargos_pendientes)
    promedio_mensual = cargo_mes_actual.total if cargo_mes_actual else 0
    
    context = {
        'departamento': departamento_id,
        'usuario_dpto': usuario_dpto,
        'cargo_mes_actual': cargo_mes_actual,
        'cargos_pendientes': cargos_pendientes,
        'reservas_pendientes': reservas_pendientes,
        'historial': historial,
        'total_pendiente': total_pendiente,
        'total_reservas_pendiente': float(total_reservas_pendiente),
        'total_general_pendiente': total_pendiente + float(total_reservas_pendiente),
        'total_pagado': float(total_pagado),
        'meses_con_deuda': meses_con_deuda,
        'promedio_mensual': promedio_mensual,
    }
    
    return render_template('finanzas/cargos_departamento.html', **context)


# ============================================================================
# PROCESAR PAGOS
# ============================================================================

@finanzas_bp.route('/pagar/cargo/<int:departamento_id>/<string:tipo_cargo>/<int:objeto_id>/', 
                    methods=['GET', 'POST'])
@login_required
def pagar_cargo_pendiente(departamento_id, tipo_cargo, objeto_id):
    """
    Procesar el pago de un cargo pendiente
    Mejorado con validaciones y confirmaciones
    """
    # Verificar permisos
    if not current_user.has_role('admin'):
        if current_user.departamento != departamento_id:
            flash('No tienes permiso para realizar esta acción.', 'danger')
            return redirect(url_for('auth.home'))
    
    if tipo_cargo == 'cargo_mensual':
        cargo = CargoMensual.get_by_id(objeto_id)
        if not cargo:
            flash('Cargo no encontrado.', 'danger')
            return redirect(url_for('finanzas.calcular_cargos_mensuales', 
                                  departamento_id=departamento_id))
        
        if cargo.pagado:
            flash('Este cargo ya fue pagado.', 'info')
            return redirect(url_for('finanzas.calcular_cargos_mensuales', 
                                  departamento_id=departamento_id))
        
        if request.method == 'POST':
            metodo_pago = request.form.get('metodo_pago', 'efectivo')
            referencia = request.form.get('referencia', '')
            
            # Marcar como pagado
            cargo.marcar_pagado()
            
            # Registrar en historial
            HistorialPago.registrar_pago(
                tipo_pago='cargo_mensual',
                objeto_id=objeto_id,
                departamento=departamento_id,
                monto=cargo.total,
                metodo_pago=metodo_pago,
                observaciones=f'Pago de cargo mensual {cargo.mes_nombre} {cargo.anio}. Ref: {referencia}'
            )
            
            # NUEVO: Enviar confirmación por email
            try:
                usuario = User.query.filter_by(departamento=departamento_id).first()
                if usuario and usuario.email:
                    from utils.email_utils import enviar_email_confirmacion_pago
                    enviar_email_confirmacion_pago(usuario, cargo, metodo_pago, referencia)
            except Exception as e:
                print(f"Error al enviar email: {e}")
            
            flash(f'Pago registrado exitosamente. Monto: Bs. {cargo.total:.2f}', 'success')
            return redirect(url_for('finanzas.calcular_cargos_mensuales', 
                                  departamento_id=departamento_id))
        
        context = {
            'tipo_pago': 'Cargo Mensual',
            'descripcion': f'{cargo.mes_nombre} {cargo.anio}',
            'detalle': {
                'Luz': f'Bs. {cargo.luz:.2f}',
                'Agua': f'Bs. {cargo.agua:.2f}',
                'Gas': f'Bs. {cargo.gas:.2f}',
                'Mantenimiento': f'Bs. {cargo.mantenimiento:.2f}',
                'Expensas Comunes': f'Bs. {cargo.expensas_comunes:.2f}',
            },
            'monto': cargo.total,
            'objeto': cargo,
            'departamento': departamento_id,
            'tipo_cargo': tipo_cargo,
            'objeto_id': objeto_id
        }
        
        return render_template('finanzas/pagar_pendiente.html', **context)
    
    elif tipo_cargo == 'reserva':
        pago = PagoReserva.get_by_id(objeto_id)
        if not pago:
            flash('Pago de reserva no encontrado.', 'danger')
            return redirect(url_for('finanzas.calcular_cargos_mensuales', 
                                  departamento_id=departamento_id))
        
        if pago.pagado:
            flash('Esta reserva ya fue pagada.', 'info')
            return redirect(url_for('finanzas.calcular_cargos_mensuales', 
                                  departamento_id=departamento_id))
        
        reserva = Reserva.get_by_id(pago.reserva_id)
        
        if request.method == 'POST':
            metodo_pago = request.form.get('metodo_pago', 'efectivo')
            referencia = request.form.get('referencia', '')
            
            pago.marcar_pagado(metodo_pago=metodo_pago, referencia=referencia)
            
            HistorialPago.registrar_pago(
                tipo_pago='reserva',
                objeto_id=pago.reserva_id,
                departamento=departamento_id,
                monto=pago.monto,
                metodo_pago=metodo_pago,
                observaciones=f'Pago de reserva - {reserva.area.nombre if reserva else "Área desconocida"}. Ref: {referencia}'
            )
            
            flash(f'Pago de reserva registrado exitosamente. Monto: Bs. {pago.monto:.2f}', 'success')
            return redirect(url_for('finanzas.calcular_cargos_mensuales', 
                                  departamento_id=departamento_id))
        
        context = {
            'tipo_pago': 'Reserva de Área Común',
            'descripcion': f'{reserva.area.nombre if reserva else "Área"} - {reserva.fecha.strftime("%d/%m/%Y") if reserva else ""}',
            'detalle': {
                'Área': reserva.area.nombre if reserva else 'N/A',
                'Fecha': reserva.fecha.strftime('%d/%m/%Y') if reserva else 'N/A',
                'Horario': f'{reserva.hora_inicio.strftime("%H:%M")} - {reserva.hora_fin.strftime("%H:%M")}' if reserva else 'N/A',
                'Duración': f'{reserva.duracion_horas:.1f} horas' if reserva else 'N/A',
            },
            'monto': float(pago.monto),
            'objeto': pago,
            'reserva': reserva,
            'departamento': departamento_id,
            'tipo_cargo': tipo_cargo,
            'objeto_id': objeto_id
        }
        
        return render_template('finanzas/pagar_pendiente.html', **context)
    
    else:
        flash('Tipo de cargo no válido.', 'danger')
        return redirect(url_for('finanzas.calcular_cargos_mensuales', 
                              departamento_id=departamento_id))


# ============================================================================
# GESTIÓN DE GASTOS
# ============================================================================

@finanzas_bp.route('/gastos/', methods=['GET', 'POST'])
@role_required('admin')
def gestionar_gastos():
    """
    Gestionar gastos del edificio - MEJORADO
    """
    if request.method == 'POST':
        concepto = request.form.get('concepto')
        monto = request.form.get('monto')
        categoria = request.form.get('categoria')
        fecha_gasto_str = request.form.get('fecha_gasto')
        descripcion = request.form.get('descripcion')
        
        try:
            fecha_gasto = datetime.strptime(fecha_gasto_str, '%Y-%m-%d').date()
        except:
            fecha_gasto = date.today()
        
        gasto = GastoEdificio(
            concepto=concepto,
            monto=float(monto),
            categoria=categoria,
            fecha_gasto=fecha_gasto,
            descripcion=descripcion,
            registrado_por=current_user.get_full_name()
        )
        gasto.save()
        
        flash('Gasto registrado exitosamente.', 'success')
        return redirect(url_for('finanzas.gestionar_gastos'))
    
    # GET - Obtener gastos con filtros
    mes_filtro = request.args.get('mes', type=int)
    anio_filtro = request.args.get('anio', type=int)
    categoria_filtro = request.args.get('categoria')
    
    if mes_filtro and anio_filtro:
        gastos = GastoEdificio.get_by_mes(mes_filtro, anio_filtro)
    else:
        gastos = GastoEdificio.get_all()
    
    if categoria_filtro:
        gastos = [g for g in gastos if g.categoria == categoria_filtro]
    
    # Calcular totales por categoría
    totales_categoria = {}
    for gasto in gastos:
        cat = gasto.categoria
        totales_categoria[cat] = totales_categoria.get(cat, 0) + float(gasto.monto)
    
    total_general = sum(float(g.monto) for g in gastos)
    
    context = {
        'gastos': gastos,
        'totales_categoria': totales_categoria,
        'total_general': total_general,
        'mes_filtro': mes_filtro,
        'anio_filtro': anio_filtro,
        'categoria_filtro': categoria_filtro,
    }
    
    return render_template('finanzas/gastos.html', **context)


@finanzas_bp.route('/gastos/eliminar/<int:gasto_id>/', methods=['POST'])
@role_required('admin')
def eliminar_gasto(gasto_id):
    """Eliminar un gasto"""
    gasto = GastoEdificio.get_by_id(gasto_id)
    if gasto:
        gasto.delete()
        flash('Gasto eliminado correctamente.', 'success')
    else:
        flash('Gasto no encontrado.', 'danger')
    
    return redirect(url_for('finanzas.gestionar_gastos'))


# ============================================================================
# REPORTES Y EXPORTACIÓN
# ============================================================================

@finanzas_bp.route('/reporte_mensual/<int:mes>/<int:anio>/')
@role_required('admin')
def reporte_mensual(mes, anio):
    """
    Generar reporte mensual en PDF
    """
    # Obtener datos del mes
    ingresos_cargos = CargoMensual.get_total_recaudado_mes(mes, anio)
    ingresos_reservas = PagoReserva.get_total_recaudado_reservas(mes, anio)
    gastos = GastoEdificio.get_by_mes(mes, anio)
    total_gastos = sum(float(g.monto) for g in gastos)
    
    # Crear PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Título
    mes_nombre = datetime(anio, mes, 1).strftime('%B %Y')
    title = Paragraph(f"REPORTE FINANCIERO<br/>{mes_nombre.upper()}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Tabla de resumen
    data_resumen = [
        ['CONCEPTO', 'MONTO (Bs.)'],
        ['Ingresos por Cargos Mensuales', f'{ingresos_cargos:,.2f}'],
        ['Ingresos por Reservas', f'{ingresos_reservas:,.2f}'],
        ['TOTAL INGRESOS', f'{ingresos_cargos + ingresos_reservas:,.2f}'],
        ['', ''],
        ['TOTAL GASTOS', f'{total_gastos:,.2f}'],
        ['', ''],
        ['BALANCE', f'{(ingresos_cargos + ingresos_reservas) - total_gastos:,.2f}'],
    ]
    
    table_resumen = Table(data_resumen, colWidths=[4*inch, 2*inch])
    table_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 2), (-1, 2), colors.lightblue),
        ('BACKGROUND', (0, 4), (-1, 4), colors.lightcoral),
        ('BACKGROUND', (0, 6), (-1, 6), colors.lightgreen),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table_resumen)
    elements.append(PageBreak())
    
    # Detalle de gastos
    if gastos:
        elements.append(Paragraph("DETALLE DE GASTOS", styles['Heading2']))
        elements.append(Spacer(1, 0.2*inch))
        
        data_gastos = [['Fecha', 'Concepto', 'Categoría', 'Monto (Bs.)']]
        for gasto in gastos:
            data_gastos.append([
                gasto.fecha_gasto.strftime('%d/%m/%Y'),
                gasto.concepto[:40],
                gasto.categoria,
                f'{float(gasto.monto):,.2f}'
            ])
        
        table_gastos = Table(data_gastos, colWidths=[1*inch, 3*inch, 1.5*inch, 1.5*inch])
        table_gastos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table_gastos)
    
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'reporte_financiero_{mes}_{anio}.pdf'
    )


# ============================================================================
# API ENDPOINTS
# ============================================================================

@finanzas_bp.route('/api/resumen_mes/<int:mes>/<int:anio>')
@role_required('admin')
def api_resumen_mes(mes, anio):
    """
    API para obtener resumen financiero de un mes específico
    """
    ingresos_cargos = CargoMensual.get_total_recaudado_mes(mes, anio)
    ingresos_reservas = PagoReserva.get_total_recaudado_reservas(mes, anio)
    gastos = GastoEdificio.get_total_mes(mes, anio)
    
    return jsonify({
        'ingresos_cargos': ingresos_cargos,
        'ingresos_reservas': ingresos_reservas,
        'total_ingresos': ingresos_cargos + ingresos_reservas,
        'gastos': gastos,
        'balance': (ingresos_cargos + ingresos_reservas) - gastos,
        'mes': mes,
        'anio': anio
    })


@finanzas_bp.route('/api/estadisticas/')
@role_required('admin')
def api_estadisticas():
    """
    API para obtener estadísticas generales
    """
    hoy = date.today()
    
    return jsonify({
        'total_pendiente': sum(c.total for c in CargoMensual.get_all_pendientes()),
        'total_departamentos': len(set([c.departamento for c in CargoMensual.get_all()])),
        'ingresos_mes_actual': CargoMensual.get_total_recaudado_mes(hoy.month, hoy.year),
        'gastos_mes_actual': GastoEdificio.get_total_mes(hoy.month, hoy.year),
    })


# ============================================================================
# PAGO RÁPIDO (ADMIN)
# ============================================================================

@finanzas_bp.route('/pagar/<string:tipo_pago>/<int:pk>/', methods=['POST'])
@role_required('admin')
def pagar_pendiente(tipo_pago, pk):
    """
    Marcar un pago como realizado (ruta rápida para admin desde el resumen)
    """
    if tipo_pago == 'cargo':
        cargo = CargoMensual.get_by_id(pk)
        if cargo and not cargo.pagado:
            cargo.marcar_pagado()
            HistorialPago.registrar_pago(
                tipo_pago='cargo_mensual',
                objeto_id=pk,
                departamento=cargo.departamento,
                monto=cargo.total,
                observaciones=f'Pago procesado por admin'
            )
            flash('Cargo marcado como pagado.', 'success')
        else:
            flash('Cargo no encontrado o ya pagado.', 'warning')
    
    elif tipo_pago == 'reserva':
        pago = PagoReserva.get_by_id(pk)
        if pago and not pago.pagado:
            reserva = Reserva.get_by_id(pago.reserva_id)
            pago.marcar_pagado()
            HistorialPago.registrar_pago(
                tipo_pago='reserva',
                objeto_id=pago.reserva_id,
                departamento=reserva.departamento if reserva else 0,
                monto=pago.monto,
                observaciones=f'Pago procesado por admin'
            )
            flash('Pago de reserva marcado como pagado.', 'success')
        else:
            flash('Pago no encontrado o ya realizado.', 'warning')
    
    return redirect(url_for('finanzas.resumen_financiero'))