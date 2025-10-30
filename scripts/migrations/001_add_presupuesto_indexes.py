"""
Crea índices recomendados en la tabla `presupuesto` si no existen.

Índices:
- idx_presupuesto_mes_anio (mes, anio)
- idx_presupuesto_anio_mes (anio, mes)

Seguro: consulta INFORMATION_SCHEMA antes de crear; no borra ni modifica datos.
"""
from app.config import DefaultConfig
import pymysql
import os
import sys

# Asegurar que se pueda importar el paquete `app` al ejecutar desde scripts/migrations/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


INDEX_DEFS = [
    ("idx_presupuesto_mes_anio",
     "CREATE INDEX idx_presupuesto_mes_anio ON presupuesto (mes, anio)"),
    ("idx_presupuesto_anio_mes",
     "CREATE INDEX idx_presupuesto_anio_mes ON presupuesto (anio, mes)"),
]


def index_exists(cursor, schema: str, table: str, index_name: str) -> bool:
    cursor.execute(
        """
        SELECT 1
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND INDEX_NAME=%s
        LIMIT 1
        """,
        (schema, table, index_name),
    )
    return cursor.fetchone() is not None


def main():
    # Leer DB params de env vars si están disponibles (puestas por migrate.py)
    # Sino, usar DefaultConfig
    params = {
        "host": os.getenv("DB_HOST", DefaultConfig.DB_HOST),
        "user": os.getenv("DB_USER", DefaultConfig.DB_USER),
        "password": os.getenv("DB_PASSWORD", DefaultConfig.DB_PASSWORD),
        "database": os.getenv("DB_NAME", DefaultConfig.DB_NAME),
        "port": int(os.getenv("DB_PORT", DefaultConfig.DB_PORT)),
        "cursorclass": pymysql.cursors.DictCursor,
    }

    conn = pymysql.connect(**params)
    try:
        cur = conn.cursor()
        created = []
        for name, create_sql in INDEX_DEFS:
            if index_exists(cur, params["database"], "presupuesto", name):
                print(f"[OK] Indice ya existe: {name}")
            else:
                try:
                    cur.execute(create_sql)
                    created.append(name)
                    print(f"[CREATED] Indice creado: {name}")
                except pymysql.Error as e:
                    print(f"[WARN] Error creando {name}: {e}")
        conn.commit()
        if not created:
            print("[INFO] No habia indices pendientes; nada que hacer.")
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()


if __name__ == "__main__":
    main()
