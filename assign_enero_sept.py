"""
Script para asignar presupuesto de 1200€ a los meses de Enero-Septiembre 2025.
"""
import os
import pymysql
from dotenv import load_dotenv
from app.constants import MESES

# Cargar variables de entorno
load_dotenv()


def assign_presupuestos():
    """Asigna 1200€ a cada mes de Enero a Septiembre 2025."""
    monto = 1200.00
    anio = 2025
    meses_asignar = MESES[0:9]  # Enero a Septiembre

    print("\n" + "="*60)
    print("ASIGNACIÓN DE PRESUPUESTOS")
    print("="*60)
    print(f"Monto:  {monto}€")
    print(f"Año:    {anio}")
    print(f"Meses:  {', '.join(meses_asignar)}")
    print(f"Total:  {len(meses_asignar)} meses")
    print("="*60 + "\n")

    try:
        conn = pymysql.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'economia_db'),
            port=int(os.getenv('DB_PORT', '3306'))
        )
        cursor = conn.cursor()

        insertados = 0
        actualizados = 0

        for mes in meses_asignar:
            # Verificar si ya existe
            cursor.execute(
                "SELECT id FROM presupuesto WHERE mes = %s AND anio = %s",
                (mes, anio)
            )
            existe = cursor.fetchone()

            if existe:
                # Actualizar
                cursor.execute(
                    "UPDATE presupuesto SET monto = %s, fecha_cambio = NOW() WHERE mes = %s AND anio = %s",
                    (monto, mes, anio)
                )
                actualizados += 1
                print(f"✅ {mes} {anio}: Actualizado a {monto}€")
            else:
                # Insertar
                cursor.execute(
                    "INSERT INTO presupuesto (mes, anio, monto, fecha_cambio) VALUES (%s, %s, %s, NOW())",
                    (mes, anio, monto)
                )
                insertados += 1
                print(f"✅ {mes} {anio}: Creado con {monto}€")

        conn.commit()
        cursor.close()
        conn.close()

        print(f"\n{'='*60}")
        print(f"✅ Operación completada exitosamente")
        print(f"   - Registros insertados: {insertados}")
        print(f"   - Registros actualizados: {actualizados}")
        print(f"   - Total procesado: {insertados + actualizados}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n❌ Error al asignar presupuestos: {e}\n")


if __name__ == "__main__":
    assign_presupuestos()
