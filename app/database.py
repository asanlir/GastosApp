"""
Módulo para manejar conexiones a la base de datos.
Provee helpers y context managers para obtener conexiones y cursores.
"""
from contextlib import contextmanager
import os
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


def ensure_database_exists():
    """
    Verifica que la base de datos existe y la crea si es necesaria.
    También ejecuta el schema inicial si la BD está vacía.

    Esta función se ejecuta automáticamente al arrancar la aplicación
    para facilitar la experiencia de usuarios no técnicos.

    Raises:
        DatabaseError: Si no se puede crear la BD o hay problemas de permisos.
    """
    params = _get_db_params()
    db_name = params['database']

    # Conectar sin especificar base de datos
    conn_params = params.copy()
    del conn_params['database']

    try:
        # Conexión al servidor MySQL (sin BD específica)
        conn = pymysql.connect(**conn_params)
        cursor = conn.cursor()

        # Verificar si la BD existe
        cursor.execute("SHOW DATABASES LIKE %s", (db_name,))
        db_exists = cursor.fetchone() is not None

        if not db_exists:
            print(f"📦 Creando base de datos '{db_name}'...")
            cursor.execute(
                f"CREATE DATABASE {db_name} "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            print(f"✅ Base de datos '{db_name}' creada correctamente")

        cursor.close()
        conn.close()

        # Ahora conectar a la BD específica y verificar tablas
        conn = pymysql.connect(**params)
        cursor = conn.cursor()

        # Verificar si las tablas existen
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        if not tables:
            print("📋 Inicializando estructura de la base de datos...")
            _apply_schema(conn, cursor)
            print("✅ Estructura de base de datos creada correctamente")

        cursor.close()
        conn.close()

    except pymysql.err.OperationalError as e:
        if "Access denied" in str(e):
            raise DatabaseError(
                f"❌ Error de acceso a MySQL: Verifica usuario y contraseña en .env\n"
                f"   Usuario actual: {params['user']}\n"
                f"   Host: {params['host']}:{params['port']}"
            ) from e
        elif "Can't connect" in str(e):
            raise DatabaseError(
                f"❌ No se puede conectar a MySQL:\n"
                f"   - Verifica que MySQL esté ejecutándose\n"
                f"   - Comprueba host y puerto en .env: {params['host']}:{params['port']}"
            ) from e
        else:
            raise DatabaseError(f"❌ Error de base de datos: {e}") from e
    except pymysql.err.InternalError as e:
        if "Access denied" in str(e) or "CREATE command denied" in str(e):
            raise DatabaseError(
                f"❌ El usuario MySQL '{params['user']}' no tiene permisos para crear bases de datos.\n"
                f"   Solución:\n"
                f"   1. Usa un usuario con permisos (como 'root')\n"
                f"   2. O crea manualmente la BD: CREATE DATABASE {db_name};"
            ) from e
        raise DatabaseError(f"❌ Error interno de MySQL: {e}") from e
    except Exception as e:
        raise DatabaseError(
            f"❌ Error inesperado al inicializar BD: {e}") from e


def _apply_schema(conn, cursor):
    """Aplica el schema inicial desde database/schema.sql"""
    try:
        # Importar frozen_utils para detectar si estamos en ejecutable
        try:
            from .frozen_utils import is_frozen, get_base_path
            base_path = get_base_path()
        except ImportError:
            # Si no existe frozen_utils, asumir modo desarrollo
            base_path = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))

        schema_path = os.path.join(base_path, 'database', 'schema.sql')

        if not os.path.exists(schema_path):
            raise DatabaseError(
                f"❌ No se encuentra el archivo schema.sql en: {schema_path}"
            )

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # Ejecutar cada statement (separado por ;)
        # Filtrar líneas vacías y comentarios
        statements = []
        current_statement = []

        for line in schema_sql.split('\n'):
            line = line.strip()
            # Ignorar comentarios y líneas vacías
            if not line or line.startswith('--'):
                continue
            # Ignorar CREATE DATABASE y USE (ya estamos conectados a la BD)
            if line.upper().startswith('CREATE DATABASE') or line.upper().startswith('USE '):
                continue

            current_statement.append(line)

            # Si termina en ;, ejecutar el statement
            if line.endswith(';'):
                statement = ' '.join(current_statement)
                if statement.strip():
                    cursor.execute(statement)
                current_statement = []

        conn.commit()

    except FileNotFoundError as e:
        raise DatabaseError(
            f"❌ No se encuentra el archivo schema.sql. "
            f"Asegúrate de que existe en database/schema.sql"
        ) from e
    except pymysql.Error as e:
        conn.rollback()
        raise DatabaseError(f"❌ Error al aplicar schema: {e}") from e
