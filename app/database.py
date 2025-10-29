"""
Módulo para manejar conexiones a la base de datos.
Provee helpers y context managers para obtener conexiones y cursores.
"""
from contextlib import contextmanager
import pymysql

from .config import DefaultConfig
from .exceptions import DatabaseError


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
    """Context manager que entrega una conexión y se asegura de cerrar.

    Raises:
        DatabaseError: Si no se puede establecer o cerrar la conexión.
    """
    conn = None
    try:
        conn = get_connection()
        yield conn
    except pymysql.Error as e:
        raise DatabaseError(f"Error en conexión a base de datos: {e}") from e
    finally:
        if conn:
            try:
                conn.close()
            except pymysql.Error:
                pass  # Ignorar errores al cerrar


@contextmanager
def cursor_context():
    """Context manager que entrega (conn, cursor) y se asegura de cerrar.

    Uso:
        with cursor_context() as (conn, cur):
            cur.execute(...)

    Raises:
        DatabaseError: Si no se puede establecer la conexión o crear el cursor.
    """
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        yield conn, cur
    except pymysql.Error as e:
        raise DatabaseError(f"Error en cursor de base de datos: {e}") from e
    finally:
        if cur:
            try:
                cur.close()
            except pymysql.Error:
                pass  # Ignorar errores al cerrar
        if conn:
            try:
                conn.close()
            except pymysql.Error:
                pass  # Ignorar errores al cerrar
