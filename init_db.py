# init_db_mejorado.py

import sys
import os

# Agregar el directorio app al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def init_database():
    """Inicializa la base de datos con datos de prueba"""
    
    try:
        from run import create_app
        from models.user_model import User
        from models.finanzas_model import CargoMensual, GastoEdificio
        from models.reservas_model import AreaComun, Reserva, inicializar_areas_comunes
        from datetime import date, time, datetime, timedelta
        from decimal import Decimal
        
        print("\n" + "="*70)
        print("🔧 INICIALIZANDO BASE DE DATOS BUILDTECH")
        print("="*70 + "\n")
        
        app, socketio = create_app()
        
        with app.app_context():
            # 1. CREAR USUARIOS
            print("👥 Creando usuarios...")
            
            # Usuario Admin
            try:
                admin = User.query.filter_by(username='admin').first()
                if not admin:
                    admin = User(
                        username='admin',
                        email='admin@buildtech.com',
                        password='Admin123!',
                        first_name='Administrador',
                        last_name='BuildTech',
                        role='admin'
                    )
                    admin.save()
                    print("   ✓ Admin creado: admin / Admin123!")
                else:
                    print("   ℹ Admin ya existe")
            except Exception as e:
                print(f"   ❌ Error creando admin: {e}")
            
            # Residentes de prueba
            residentes_data = [
                {
                    'username': 'residente1',
                    'email': 'residente1@test.com',
                    'password': 'Residente123!',
                    'first_name': 'Juan',
                    'last_name': 'Pérez',
                    'departamento': 101,
                    'ci': '1234567',
                    'telefono': '70123456'
                },
                {
                    'username': 'residente2',
                    'email': 'residente2@test.com',
                    'password': 'Residente123!',
                    'first_name': 'María',
                    'last_name': 'González',
                    'departamento': 102,
                    'ci': '2345678',
                    'telefono': '70234567'
                },
                {
                    'username': 'residente3',
                    'email': 'residente3@test.com',
                    'password': 'Residente123!',
                    'first_name': 'Pedro',
                    'last_name': 'Ramírez',
                    'departamento': 201,
                    'ci': '3456789',
                    'telefono': '70345678'
                }
            ]
            
            for data in residentes_data:
                try:
                    residente = User.query.filter_by(username=data['username']).first()
                    if not residente:
                        residente = User(
                            username=data['username'],
                            email=data['email'],
                            password=data['password'],
                            first_name=data['first_name'],
                            last_name=data['last_name'],
                            role='residente',
                            departamento=data['departamento'],
                            ci=data['ci'],
                            telefono=data['telefono']
                        )
                        residente.save()
                        print(f"   ✓ Residente creado: {data['username']} / Residente123!")
                    else:
                        print(f"   ℹ {data['username']} ya existe")
                except Exception as e:
                    print(f"   ❌ Error creando {data['username']}: {e}")
            
            # 2. INICIALIZAR ÁREAS COMUNES
            print("\n🏊 Inicializando áreas comunes...")
            try:
                inicializar_areas_comunes()
            except Exception as e:
                print(f"   ⚠️ Error al inicializar áreas: {e}")
                print("   ℹ️ Continuando...")
            
            # 3. CREAR CARGOS MENSUALES DE PRUEBA
            print("\n💰 Creando cargos mensuales de prueba...")
            
            hoy = date.today()
            mes_actual = hoy.month
            anio_actual = hoy.year
            
            departamentos = [101, 102, 201]
            
            for dept in departamentos:
                try:
                    cargo = CargoMensual.query.filter_by(
                        departamento=dept,
                        mes=mes_actual,
                        anio=anio_actual
                    ).first()
                    
                    if not cargo:
                        cargo = CargoMensual(
                            departamento=dept,
                            mes=mes_actual,
                            anio=anio_actual,
                            luz=150.00,
                            agua=80.00,
                            gas=60.00,
                            mantenimiento=200.00,
                            expensas_comunes=150.00
                        )
                        cargo.save()
                        print(f"   ✓ Cargo creado para Dpto {dept}: Bs. {cargo.total:.2f}")
                    else:
                        print(f"   ℹ Cargo del Dpto {dept} ya existe")
                except Exception as e:
                    print(f"   ❌ Error creando cargo Dpto {dept}: {e}")
            
            # 4. CREAR GASTOS DE PRUEBA
            print("\n💸 Creando gastos del edificio...")
            
            gastos_data = [
                {
                    'concepto': 'Mantenimiento de ascensores',
                    'monto': 1500.00,
                    'categoria': 'mantenimiento',
                    'descripcion': 'Mantenimiento preventivo mensual'
                },
                {
                    'concepto': 'Salario del conserje',
                    'monto': 2500.00,
                    'categoria': 'personal',
                    'descripcion': 'Pago mensual del personal'
                },
                {
                    'concepto': 'Limpieza de áreas comunes',
                    'monto': 800.00,
                    'categoria': 'servicios',
                    'descripcion': 'Servicio de limpieza mensual'
                }
            ]
            
            for gasto_data in gastos_data:
                try:
                    gasto = GastoEdificio.query.filter_by(
                        concepto=gasto_data['concepto'],
                        fecha_gasto=hoy
                    ).first()
                    
                    if not gasto:
                        gasto = GastoEdificio(
                            concepto=gasto_data['concepto'],
                            monto=gasto_data['monto'],
                            categoria=gasto_data['categoria'],
                            fecha_gasto=hoy,
                            descripcion=gasto_data['descripcion'],
                            registrado_por='Admin BuildTech'
                        )
                        gasto.save()
                        print(f"   ✓ Gasto registrado: {gasto_data['concepto']}")
                    else:
                        print(f"   ℹ Gasto '{gasto_data['concepto']}' ya existe")
                except Exception as e:
                    print(f"   ❌ Error registrando gasto: {e}")
            
            # 5. CREAR RESERVAS DE PRUEBA
            print("\n📅 Creando reservas de prueba...")
            
            try:
                # Obtener área de ejemplo
                salon_fiestas = AreaComun.query.filter_by(nombre='Salón de Fiestas').first()
                
                if salon_fiestas:
                    # Reserva para el próximo fin de semana
                    proximo_sabado = hoy + timedelta(days=(5 - hoy.weekday()) % 7)
                    
                    reserva = Reserva.query.filter_by(
                        area_id=salon_fiestas.id,
                        fecha=proximo_sabado
                    ).first()
                    
                    if not reserva:
                        reserva = Reserva(
                            area_id=salon_fiestas.id,
                            departamento=101,
                            usuario='Juan Pérez',
                            fecha=proximo_sabado,
                            hora_inicio=time(18, 0),
                            hora_fin=time(22, 0),
                            motivo='Cumpleaños',
                            num_personas=30,
                            telefono='70123456',
                            email='residente1@test.com'
                        )
                        reserva.save()
                        print(f"   ✓ Reserva creada: {salon_fiestas.nombre} - {proximo_sabado}")
                    else:
                        print(f"   ℹ Ya existe reserva para esa fecha")
                else:
                    print("   ⚠️ No se encontró el Salón de Fiestas")
            except Exception as e:
                print(f"   ❌ Error creando reserva: {e}")
            
            print("\n" + "="*70)
            print("✅ BASE DE DATOS INICIALIZADA CORRECTAMENTE")
            print("="*70)
            print("\n📝 CREDENCIALES DE ACCESO:")
            print("\n   ADMINISTRADOR:")
            print("   Usuario: admin")
            print("   Password: Admin123!")
            print("\n   RESIDENTE 1 (Dpto 101):")
            print("   Usuario: residente1")
            print("   Password: Residente123!")
            print("\n   RESIDENTE 2 (Dpto 102):")
            print("   Usuario: residente2")
            print("   Password: Residente123!")
            print("\n   RESIDENTE 3 (Dpto 201):")
            print("   Usuario: residente3")
            print("   Password: Residente123!")
            print("\n" + "="*70)
            print("🚀 Puedes ejecutar ahora: cd app && python3 run.py")
            print("="*70 + "\n")
            
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        print("\nAsegúrate de:")
        print("1. Estar en el directorio buildtech_unified/")
        print("2. Haber eliminado app/buildtech.db")
        print("3. Tener instaladas las dependencias: pip install -r requirements.txt")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    init_database()