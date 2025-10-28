"""
Funciones auxiliares utilizadas en toda la aplicación.
"""
from typing import Any, Dict, Optional, TypeVar, Union

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

def safe_get(row: Optional[Dict[str, Any]], key: str, default: T = None) -> Union[Any, T]:
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