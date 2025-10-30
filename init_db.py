"""
Script para inicializar la base de datos con el schema.
⚠️  ADVERTENCIA: Solo ejecutar en bases de datos VACÍAS.
    Para agregar tablas a una BD con datos, usar scripts específicos.
"""
import sys
import pymysql
from app.config import DefaultConfig


def check_database_has_data(cursor):
    """Verifica si la base de datos tiene datos existentes."""
    try:
        cursor.execute("USE economia_db")

        # Verificar si hay gastos
        cursor.execute("SELECT COUNT(*) FROM gastos")
        gastos_count = cursor.fetchone()[0]

        # Verificar si hay categorías
        cursor.execute("SELECT COUNT(*) FROM categorias")
        categorias_count = cursor.fetchone()[0]

        return gastos_count > 0 or categorias_count > 0
    except pymysql.err.ProgrammingError:
        # La base de datos o las tablas no existen
        return False


def init_database(force=False):
    """
    Crea las tablas necesarias en la base de datos.

    Args:
        force: Si es True, ejecuta sin verificar datos existentes (PELIGROSO)
    """
    # Conectar sin seleccionar BD
    conn = pymysql.connect(
        host=DefaultConfig.DB_HOST,
        user=DefaultConfig.DB_USER,
        password=DefaultConfig.DB_PASSWORD,
        port=DefaultConfig.DB_PORT
    )

    cursor = conn.cursor()

    # PROTECCIÓN: Verificar si hay datos existentes
    if not force and check_database_has_data(cursor):
        print("\n" + "="*70)
        print("⛔ ERROR: La base de datos contiene datos existentes")
        print("="*70)
        print("\n❌ Este script NO debe ejecutarse sobre una BD con datos.")
        print("   Riesgo: Podría causar pérdida de información.\n")
        print("Opciones:")
        print("  1. Si necesitas agregar una tabla específica, edita manualmente")
        print("     el archivo database/schema.sql y ejecuta solo ese comando.")
        print("  2. Si realmente quieres reinicializar (BORRARÁ DATOS), ejecuta:")
        print("     python init_db.py --force\n")

        cursor.close()
        conn.close()
        sys.exit(1)

    # Leer y ejecutar schema.sql
    print("\n🔧 Iniciando creación de esquema de base de datos...")
    with open('database/schema.sql', 'r', encoding='utf-8') as f:
        sql_commands = f.read()

        # Ejecutar cada comando
        for command in sql_commands.split(';'):
            command = command.strip()
            if command:
                try:
                    cursor.execute(command)
                    print(f"✅ Ejecutado: {command[:50]}...")
                except Exception as e:
                    print(f"⚠️  Error: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("\n✅ Base de datos inicializada correctamente")


if __name__ == '__main__':
    # Verificar si se pasó el flag --force
    force_mode = '--force' in sys.argv

    if force_mode:
        confirm = input("\n⚠️  ADVERTENCIA: Estás usando --force. Esto puede BORRAR DATOS.\n"
                        "   ¿Estás seguro? Escribe 'SI' para continuar: ")
        if confirm != 'SI':
            print("❌ Operación cancelada.")
            sys.exit(0)

    init_database(force=force_mode)
