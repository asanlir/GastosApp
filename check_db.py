"""
Script temporal para verificar el estado de la base de datos.
"""
import os
from dotenv import load_dotenv
import pymysql

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    'port': int(os.getenv('DB_PORT', '3306'))
}


def check_tables():
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Verificar categorías
        cursor.execute("SELECT * FROM categorias")
        categorias = cursor.fetchall()
        print("\nCategorías existentes:")
        for cat in categorias:
            print(f"ID: {cat['id']}, Nombre: {cat['nombre']}")

        # Verificar presupuestos
        cursor.execute(
            "SELECT * FROM presupuesto ORDER BY anio DESC, mes DESC LIMIT 5")
        presupuestos = cursor.fetchall()
        print("\nÚltimos 5 presupuestos:")
        for pres in presupuestos:
            print(
                f"Mes: {pres['mes']}, Año: {pres['anio']}, Monto: {pres['monto']}")

        # Verificar gastos
        cursor.execute("SELECT COUNT(*) as total FROM gastos")
        total_gastos = cursor.fetchone()['total']
        print(f"\nTotal de gastos registrados: {total_gastos}")

        cursor.execute("""
            SELECT mes, anio, COUNT(*) as num_gastos, SUM(monto) as total_monto 
            FROM gastos 
            GROUP BY anio, mes 
            ORDER BY anio DESC, FIELD(mes, 'Diciembre', 'Noviembre', 'Octubre', 'Septiembre', 
                'Agosto', 'Julio', 'Junio', 'Mayo', 'Abril', 'Marzo', 'Febrero', 'Enero') 
            LIMIT 5""")
        ultimos_gastos = cursor.fetchall()
        print("\nResumen de los últimos meses:")
        for g in ultimos_gastos:
            print(
                f"Mes: {g['mes']} {g['anio']}: {g['num_gastos']} gastos, Total: {g['total_monto']}€")

    except pymysql.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    check_tables()
