# migrate_reservas.py
"""
Script de migración para actualizar el sistema de reservas
Ejecutar desde app/: python migrate_reservas.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run import create_app
from database import db

def migrate_database():
    """Aplica las migraciones necesarias"""
    
    print("\n" + "="*70)
    print("🔄 MIGRACIÓN DE BASE DE DATOS - SISTEMA DE RESERVAS MEJORADO")
    print("="*70 + "\n")
    
    app, socketio = create_app()
    
    with app.app_context():
        try:
            # Crear todas las tablas (incluyendo nuevas columnas)
            print("📋 Creando/actualizando tablas...")
            db.create_all()
            print("✅ Tablas actualizadas correctamente")
            
            # Verificar y actualizar áreas existentes
            print("\n📊 Actualizando áreas comunes...")
            from models.reservas_model import AreaComun
            
            areas = AreaComun.query.all()
            for area in areas:
                # Actualizar campos nuevos si no existen
                if not hasattr(area, 'requiere_deposito'):
                    area.requiere_deposito = False
                    area.monto_deposito = 0.00
                
                if not hasattr(area, 'rating_promedio'):
                    area.rating_promedio = 0.00
                    area.total_ratings = 0
                
                if not hasattr(area, 'total_reservas'):
                    # Calcular reservas existentes
                    from models.reservas_model import Reserva
                    total = Reserva.query.filter_by(area_id=area.id).count()
                    area.total_reservas = total
                
                db.session.commit()
                print(f"   ✓ Área actualizada: {area.nombre}")
            
            # Verificar y actualizar reservas existentes
            print("\n📅 Actualizando reservas...")
            from models.reservas_model import Reserva
            
            reservas = Reserva.query.all()
            for reserva in reservas:
                if not hasattr(reserva, 'recordatorio_24h_enviado'):
                    reserva.recordatorio_24h_enviado = False
                    reserva.recordatorio_1h_enviado = False
                
                if not hasattr(reserva, 'evaluada'):
                    reserva.evaluada = False
                
                db.session.commit()
            
            if reservas:
                print(f"   ✓ {len(reservas)} reservas actualizadas")
            
            print("\n" + "="*70)
            print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
            print("="*70)
            print("\n📝 Nuevas funcionalidades disponibles:")
            print("   • Sistema de calificaciones (ratings)")
            print("   • Recordatorios automáticos")
            print("   • Check-in / Check-out")
            print("   • Estadísticas de popularidad")
            print("   • Sistema de depósitos")
            print("   • Gestión de equipamiento")
            print("\n" + "="*70 + "\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERROR DURANTE LA MIGRACIÓN: {str(e)}")
            print("\nSi el error persiste:")
            print("1. Hacer backup de buildtech.db")
            print("2. Eliminar buildtech.db")
            print("3. Ejecutar: python init_db.py")
            print("4. Ejecutar: python migrate_reservas.py")
            import traceback
            traceback.print_exc()
            return False


def verificar_integridad():
    """Verifica la integridad de los datos después de la migración"""
    
    print("\n🔍 Verificando integridad de datos...")
    
    app, socketio = create_app()
    
    with app.app_context():
        from models.reservas_model import AreaComun, Reserva, AreaRating
        
        # Verificar áreas
        areas = AreaComun.query.all()
        print(f"   ✓ {len(areas)} áreas comunes en la base de datos")
        
        # Verificar reservas
        reservas = Reserva.query.all()
        print(f"   ✓ {len(reservas)} reservas en la base de datos")
        
        # Verificar estados
        estados = {}
        for reserva in reservas:
            estado = reserva.estado
            estados[estado] = estados.get(estado, 0) + 1
        
        if estados:
            print("   📊 Distribución de estados:")
            for estado, count in estados.items():
                print(f"      • {estado}: {count}")
        
        # Verificar ratings
        ratings = AreaRating.query.all()
        print(f"   ✓ {len(ratings)} calificaciones registradas")
        
        print("\n✅ Verificación completada - Todo en orden")


if __name__ == '__main__':
    print("\n⚠️  IMPORTANTE: Asegúrate de tener un backup de tu base de datos")
    print("   antes de ejecutar esta migración.\n")
    
    respuesta = input("¿Deseas continuar con la migración? (s/n): ")
    
    if respuesta.lower() in ['s', 'si', 'yes', 'y']:
        if migrate_database():
            verificar_integridad()
    else:
        print("\n❌ Migración cancelada por el usuario")