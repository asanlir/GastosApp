"""
Servicio que maneja la lógica de negocio relacionada con las categorías.
"""
from typing import List, Dict, Any
from app.database import cursor_context
from app.queries import (
    q_list_categorias,
    q_insert_categoria,
    q_update_categoria,
    q_delete_categoria,
)


def list_categorias() -> List[Dict[str, Any]]:
    """
    Obtiene la lista de todas las categorías.

    Returns:
        Lista de diccionarios con las categorías
    """
    with cursor_context() as (_, cursor):
        cursor.execute(q_list_categorias())
        return list(cursor.fetchall())


def add_categoria(nombre: str) -> bool:
    """
    Agrega una nueva categoría.

    Args:
        nombre: Nombre de la categoría

    Returns:
        True si la categoría fue agregada correctamente, False en caso contrario
    """
    try:
        with cursor_context() as (conn, cursor):
            cursor.execute(q_insert_categoria(), (nombre,))
            conn.commit()
            return True
    except Exception:
        return False


def update_categoria(categoria_id: int, nombre: str) -> bool:
    """
    Actualiza una categoría existente.

    Args:
        categoria_id: ID de la categoría a actualizar
        nombre: Nuevo nombre de la categoría

    Returns:
        True si la categoría fue actualizada correctamente, False en caso contrario
    """
    try:
        with cursor_context() as (conn, cursor):
            cursor.execute(q_update_categoria(), (nombre, categoria_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception:
        return False


def delete_categoria(categoria_id: int) -> bool:
    """
    Elimina una categoría existente.

    Args:
        categoria_id: ID de la categoría a eliminar

    Returns:
        True si la categoría fue eliminada correctamente, False en caso contrario
    """
    try:
        with cursor_context() as (conn, cursor):
            cursor.execute(q_delete_categoria(), (categoria_id,))
            conn.commit()
            return cursor.rowcount > 0
    except Exception:
        return False
