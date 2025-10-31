"""
Migración 003: Añadir columna incluir_en_resumen a categorias
Permite controlar qué categorías se incluyen en el cálculo del resumen/presupuesto
"""

from app.config import DevelopmentConfig
import sys
import pymysql
from pathlib import Path

# Añadir el directorio raíz al path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))


def up():
    """Añadir columna incluir_en_resumen a la tabla categorias"""
    conn = pymysql.connect(
        host=DevelopmentConfig.DB_HOST,
        user=DevelopmentConfig.DB_USER,
        password=DevelopmentConfig.DB_PASSWORD,
        database=DevelopmentConfig.DB_NAME
    )

    try:
        cursor = conn.cursor()

        # Añadir columna si no existe
        cursor.execute("""
            ALTER TABLE categorias 
            ADD COLUMN IF NOT EXISTS incluir_en_resumen BOOLEAN NOT NULL DEFAULT TRUE
        """)

        conn.commit()
        print("✓ Columna 'incluir_en_resumen' añadida exitosamente")

        # Verificar que se añadió
        cursor.execute(
            "SHOW COLUMNS FROM categorias LIKE 'incluir_en_resumen'")
        result = cursor.fetchone()
        if result:
            print(f"✓ Verificación: Columna existe con tipo {result[1]}")

    except Exception as e:
        conn.rollback()
        print(f"✗ Error en migración UP: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def down():
    """Revertir: eliminar columna incluir_en_resumen"""
    conn = pymysql.connect(
        host=DevelopmentConfig.DB_HOST,
        user=DevelopmentConfig.DB_USER,
        password=DevelopmentConfig.DB_PASSWORD,
        database=DevelopmentConfig.DB_NAME
    )

    try:
        cursor = conn.cursor()

        cursor.execute("""
            ALTER TABLE categorias 
            DROP COLUMN IF EXISTS incluir_en_resumen
        """)

        conn.commit()
        print("✓ Columna 'incluir_en_resumen' eliminada exitosamente")

    except Exception as e:
        conn.rollback()
        print(f"✗ Error en migración DOWN: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "down":
        print("Revirtiendo migración 003...")
        down()
    else:
        print("Aplicando migración 003...")
        up()
