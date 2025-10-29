"""
Script para asignar presupuestos a meses anteriores de forma masiva.

Permite asignar el mismo presupuesto a múltiples meses/años de una vez.
"""
import pymysql
from app.config import Config
from app.constants import MESES


def assign_bulk_presupuesto():
    """Asigna presupuesto a múltiples meses de forma interactiva."""
    print("\n" + "="*60)
    print("ASIGNACIÓN MASIVA DE PRESUPUESTOS")
    print("="*60)

    # Solicitar el monto
    try:
        monto = float(
            input("\nIngresa el monto del presupuesto mensual (€): "))
        if monto <= 0:
            print("❌ El monto debe ser mayor que 0")
            return
    except ValueError:
        print("❌ Monto inválido")
        return

    # Solicitar el año
    try:
        anio = int(input("Ingresa el año (ej: 2025): "))
        if anio < 2000 or anio > 2100:
            print("❌ Año inválido")
            return
    except ValueError:
        print("❌ Año inválido")
        return

    # Mostrar meses disponibles
    print("\nMeses disponibles:")
    for i, mes in enumerate(MESES, 1):
        print(f"{i:2d}. {mes}")

    # Solicitar rango de meses
    print("\nIngresa el rango de meses a asignar:")
    print("Ejemplos: '1-12' (todo el año), '1-6' (primer semestre), '1' (solo enero)")
    rango = input("Rango: ").strip()

    try:
        if '-' in rango:
            inicio, fin = map(int, rango.split('-'))
        else:
            inicio = fin = int(rango)

        if inicio < 1 or fin > 12 or inicio > fin:
            print("❌ Rango de meses inválido")
            return
    except ValueError:
        print("❌ Formato de rango inválido")
        return

    # Obtener los meses a asignar
    meses_a_asignar = MESES[inicio-1:fin]

    # Confirmar
    print(f"\n{'='*60}")
    print("CONFIRMACIÓN")
    print(f"{'='*60}")
    print(f"Monto:  {monto}€")
    print(f"Año:    {anio}")
    print(f"Meses:  {', '.join(meses_a_asignar)}")
    print(f"Total:  {len(meses_a_asignar)} meses")
    print(f"{'='*60}")

    confirmar = input("\n¿Confirmas la asignación? (si/no): ").strip().lower()
    if confirmar not in ['si', 's', 'sí']:
        print("❌ Operación cancelada")
        return

    # Realizar la asignación
    try:
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE
        )
        cursor = conn.cursor()

        insertados = 0
        actualizados = 0

        for mes in meses_a_asignar:
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
    assign_bulk_presupuesto()
