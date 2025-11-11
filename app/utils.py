"""
Funciones auxiliares utilizadas en toda la aplicación.
"""
import os
import secrets
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, TypeVar, Union
import pymysql
from pymysql.cursors import DictCursor

from .constants import MESES

T = TypeVar('T')


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Convierte un valor a float de manera segura.

    Args:
        value: Valor a convertir
        default: Valor por defecto si la conversión falla

    Returns:
        float: El valor convertido o el valor por defecto
    """
    if value is None:
        return default
    try:
        return float(str(value))
    except (ValueError, TypeError):
        return default


def safe_get(
    row: Optional[Dict[str, Any]],
    key: str,
    default: Optional[T] = None,
) -> Optional[Union[Any, T]]:
    """
    Obtiene un valor de un diccionario de manera segura.

    Args:
        row: Diccionario del que obtener el valor
        key: Clave a buscar
        default: Valor por defecto si la clave no existe o row es None

    Returns:
        El valor encontrado o el valor por defecto
    """
    if row is None:
        return default
    try:
        return row[key] if key in row else default
    except (TypeError, KeyError):
        return default


def get_current_month_year() -> Tuple[str, int]:
    """
    Obtiene el mes actual y año como strings formateados.

    Returns:
        Tuple[str, int]: (mes_actual, anio_actual)
    """
    now = datetime.now()
    return MESES[now.month - 1], now.year


def execute_query(cursor: DictCursor, query: str, params: tuple = ()) -> None:
    """
    Ejecuta una consulta SQL de manera segura.

    Args:
        cursor: Cursor de MySQL
        query: Consulta SQL
        params: Parámetros para la consulta
    """
    try:
        cursor.execute(query, params)
    except pymysql.Error as err:
        print(f"Error al ejecutar la consulta: {err}")
        raise


def format_currency(amount: float) -> str:
    """
    Formatea un número como moneda (€).

    Args:
        amount: Cantidad a formatear

    Returns:
        str: Cantidad formateada (ej: "1.234,56 €")
    """
    return f"{amount:,.2f} €".replace(",", "@").replace(".", ",").replace("@", ".")


def create_env_file(
    db_host: str,
    db_user: str,
    db_password: str,
    db_name: str,
    db_port: str = "3306"
) -> bool:
    """
    Crea el archivo .env con la configuración de la base de datos.

    Args:
        db_host: Host de MySQL
        db_user: Usuario de MySQL
        db_password: Contraseña de MySQL
        db_name: Nombre de la base de datos
        db_port: Puerto de MySQL (por defecto 3306)

    Returns:
        bool: True si se creó correctamente, False en caso de error
    """
    try:
        # Generar SECRET_KEY segura
        secret_key = secrets.token_urlsafe(32)

        # Contenido del archivo .env
        env_content = f"""# Configuración de Base de Datos
DB_HOST={db_host}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_NAME={db_name}
DB_PORT={db_port}

# Configuración de Flask
SECRET_KEY={secret_key}

# Logging
LOG_LEVEL=INFO
"""

        # Escribir archivo .env
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)

        return True
    except Exception as e:
        print(f"Error al crear archivo .env: {e}")
        return False


def test_mysql_connection(
    db_host: str,
    db_user: str,
    db_password: str,
    db_port: str = "3306"
) -> Tuple[bool, str]:
    """
    Prueba la conexión a MySQL con las credenciales proporcionadas.

    Args:
        db_host: Host de MySQL
        db_user: Usuario de MySQL
        db_password: Contraseña de MySQL
        db_port: Puerto de MySQL (por defecto 3306)

    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    try:
        connection = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            port=int(db_port),
            connect_timeout=5
        )
        connection.close()
        return True, "✅ Conexión exitosa a MySQL"
    except pymysql.err.OperationalError as e:
        error_code = e.args[0]
        if error_code == 1045:
            return False, "❌ Usuario o contraseña incorrectos"
        elif error_code == 2003:
            return False, f"❌ No se puede conectar a MySQL en {db_host}:{db_port}. Verifica que MySQL esté ejecutándose."
        else:
            return False, f"❌ Error de conexión: {e.args[1]}"
    except Exception as e:
        return False, f"❌ Error inesperado: {str(e)}"


def env_file_exists() -> bool:
    """
    Verifica si el archivo .env existe.

    Returns:
        bool: True si existe, False si no
    """
    return os.path.exists('.env')
