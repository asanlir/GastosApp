"""
Funciones auxiliares utilizadas en toda la aplicación.
"""
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, TypeVar, Union
import mysql.connector
from mysql.connector.cursor import MySQLCursor

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


def execute_query(cursor: MySQLCursor, query: str, params: tuple = ()) -> None:
    """
    Ejecuta una consulta SQL de manera segura.

    Args:
        cursor: Cursor de MySQL
        query: Consulta SQL
        params: Parámetros para la consulta
    """
    try:
        cursor.execute(query, params)
    except mysql.connector.Error as err:
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
