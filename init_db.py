"""
Script para inicializar la base de datos con el schema.
"""
import pymysql
from app.config import DefaultConfig


def init_database():
    """Crea las tablas necesarias en la base de datos."""
    # Conectar sin seleccionar BD
    conn = pymysql.connect(
        host=DefaultConfig.DB_HOST,
        user=DefaultConfig.DB_USER,
        password=DefaultConfig.DB_PASSWORD,
        port=DefaultConfig.DB_PORT
    )

    cursor = conn.cursor()

    # Leer y ejecutar schema.sql
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
    init_database()
