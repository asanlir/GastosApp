"""
Módulo para manejar conexiones a la base de datos.
Provee helpers y context managers para obtener conexiones y cursores.
"""
from contextlib import contextmanager
import pymysql

from .config import DefaultConfig


def _get_db_params():
    return {
        'host': DefaultConfig.DB_HOST,
        'user': DefaultConfig.DB_USER,
        'password': DefaultConfig.DB_PASSWORD,
        'database': DefaultConfig.DB_NAME,
        'port': DefaultConfig.DB_PORT,
    }


def get_connection():
    """Obtiene una nueva conexión a la base de datos."""
    params = _get_db_params()
    return pymysql.connect(
        **params,
        cursorclass=pymysql.cursors.DictCursor
    )


@contextmanager
def connection_context():
    conn = get_connection()
    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass


@contextmanager
def cursor_context():
    """Context manager que entrega (conn, cursor) y se asegura de cerrar.

    Uso:
        with cursor_context() as (conn, cur):
            cur.execute(...)
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        yield conn, cur
    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
