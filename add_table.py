"""
Script para agregar una tabla específica a la base de datos de forma segura.
Este script es seguro de usar con datos existentes.
"""
import sys
import pymysql
from app.config import DefaultConfig


def add_table(table_name, create_sql):
    """
    Agrega una tabla específica a la base de datos.

    Args:
        table_name: Nombre de la tabla a crear
        create_sql: SQL completo de CREATE TABLE
    """
    print(f"\n🔧 Agregando tabla: {table_name}")
    print("="*70)

    conn = pymysql.connect(
        host=DefaultConfig.DB_HOST,
        user=DefaultConfig.DB_USER,
        password=DefaultConfig.DB_PASSWORD,
        database=DefaultConfig.DB_NAME,
        port=DefaultConfig.DB_PORT
    )

    cursor = conn.cursor()

    try:
        # Verificar si la tabla ya existe
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        exists = cursor.fetchone()

        if exists:
            print(f"ℹ️  La tabla '{table_name}' ya existe.")

            # Mostrar estructura actual
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            print(f"\n📋 Estructura actual de '{table_name}':")
            for col in columns:
                print(f"   - {col[0]}: {col[1]}")

            # Verificar si hay datos
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"\n📊 Registros en la tabla: {count}")

            if count > 0:
                print(
                    f"\n✅ La tabla '{table_name}' ya existe con {count} registros. No se realizaron cambios.")
            else:
                print(
                    f"\n✅ La tabla '{table_name}' ya existe (vacía). No se realizaron cambios.")
        else:
            # Crear la tabla
            cursor.execute(create_sql)
            conn.commit()
            print(f"\n✅ Tabla '{table_name}' creada exitosamente.")

            # Mostrar estructura
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            print(f"\n📋 Estructura de la nueva tabla:")
            for col in columns:
                print(f"   - {col[0]}: {col[1]}")

    except pymysql.Error as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()


# Definición de tablas disponibles
TABLES = {
    'presupuesto': """
        CREATE TABLE IF NOT EXISTS presupuesto (
            id INT AUTO_INCREMENT PRIMARY KEY,
            monto DECIMAL(10,2) NOT NULL,
            fecha_cambio DATETIME NOT NULL,
            mes VARCHAR(20) NOT NULL,
            anio INT NOT NULL,
            INDEX idx_mes_anio (mes, anio),
            INDEX idx_anio_mes (anio, mes)
        )
    """,
    'categorias': """
        CREATE TABLE IF NOT EXISTS categorias (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL UNIQUE
        )
    """,
    'gastos': """
        CREATE TABLE IF NOT EXISTS gastos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            categoria VARCHAR(100) NOT NULL,
            descripcion TEXT,
            monto DECIMAL(10,2) NOT NULL,
            mes VARCHAR(20) NOT NULL,
            anio INT NOT NULL,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_categoria (categoria),
            INDEX idx_mes_anio (mes, anio),
            INDEX idx_anio_mes (anio, mes),
            INDEX idx_anio (anio),
            INDEX idx_categoria_anio_mes (categoria, anio, mes),
            FOREIGN KEY (categoria) REFERENCES categorias(nombre)
                ON UPDATE CASCADE
                ON DELETE RESTRICT
        )
    """
}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("\n📚 Uso: python add_table.py <nombre_tabla>")
        print("\nTablas disponibles:")
        for table in TABLES.keys():
            print(f"  - {table}")
        print("\nEjemplo:")
        print("  python add_table.py presupuesto")
        sys.exit(0)

    table_name = sys.argv[1]

    if table_name not in TABLES:
        print(f"\n❌ Error: Tabla '{table_name}' no reconocida.")
        print("\nTablas disponibles:")
        for table in TABLES.keys():
            print(f"  - {table}")
        sys.exit(1)

    add_table(table_name, TABLES[table_name])
    print("\n✅ Operación completada.\n")
