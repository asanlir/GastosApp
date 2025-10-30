"""
Módulo para manejar conexiones a la base de datos.
Provee helpers y context managers para obtener conexiones y cursores.
"""
from contextlib import contextmanager
import pymysql
from flask import current_app, has_app_context

from .config import DefaultConfig
from .exceptions import DatabaseError


def _get_db_params():
    """Obtiene parámetros de BD, priorizando la configuración de Flask si está disponible."""
    # Si estamos en contexto de Flask y hay configuración de testing
    if has_app_context() and current_app.config.get('TESTING'):
        return {
            'host': current_app.config.get('DB_HOST', DefaultConfig.DB_HOST),
            'user': current_app.config.get('DB_USER', DefaultConfig.DB_USER),
            'password': current_app.config.get('DB_PASSWORD', DefaultConfig.DB_PASSWORD),
            'database': current_app.config.get('DB_NAME', DefaultConfig.DB_NAME),
            'port': current_app.config.get('DB_PORT', DefaultConfig.DB_PORT),
        }

    # Usar DefaultConfig en otros casos
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
