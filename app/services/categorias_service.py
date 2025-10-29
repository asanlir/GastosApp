"""
Servicio que maneja la lógica de negocio relacionada con las categorías.
"""
from typing import List, Dict, Any
import pymysql
from app.database import cursor_context
from app.exceptions import DatabaseError, ValidationError
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

    Raises:
        ValidationError: Si el nombre está vacío
        DatabaseError: Si hay un error en la base de datos
    """
    if not nombre or not nombre.strip():
        raise ValidationError("El nombre de la categoría no puede estar vacío")

    try:
        with cursor_context() as (conn, cursor):
            cursor.execute(q_insert_categoria(), (nombre.strip(),))
            conn.commit()
            return True
    except DatabaseError:
        raise
    except pymysql.Error as e:
        raise DatabaseError(f"Error al agregar categoría: {e}") from e


def update_categoria(categoria_id: int, nombre: str) -> bool:
    """
    Actualiza una categoría existente.

    Args:
        categoria_id: ID de la categoría a actualizar
        nombre: Nuevo nombre de la categoría

    Returns:
        True si la categoría fue actualizada correctamente, False en caso contrario

    Raises:
        ValidationError: Si el nombre está vacío
        DatabaseError: Si hay un error en la base de datos
    """
    if not nombre or not nombre.strip():
        raise ValidationError("El nombre de la categoría no puede estar vacío")

    try:
        with cursor_context() as (conn, cursor):
            cursor.execute(q_update_categoria(),
                           (nombre.strip(), categoria_id))
            conn.commit()
            return cursor.rowcount > 0
    except DatabaseError:
        raise
    except pymysql.Error as e:
        raise DatabaseError(f"Error al actualizar categoría: {e}") from e


def delete_categoria(categoria_id: int) -> bool:
    """
    Elimina una categoría existente.

    Args:
        categoria_id: ID de la categoría a eliminar

    Returns:
        True si la categoría fue eliminada correctamente, False en caso contrario

    Raises:
        DatabaseError: Si hay un error en la base de datos
        ValueError: Si la categoría tiene gastos asociados
    """
    try:
        with cursor_context() as (conn, cursor):
            # Primero verificar si la categoría tiene gastos asociados
            cursor.execute(
                "SELECT COUNT(*) as count FROM gastos WHERE categoria = (SELECT nombre FROM categorias WHERE id = %s)",
                (categoria_id,)
            )
            result = cursor.fetchone()

            if result and result['count'] > 0:
                raise ValueError(
                    "No se puede eliminar la categoría porque tiene gastos asociados. "
                    "Elimine primero los gastos o asígnelos a otra categoría."
                )

            # Si no hay gastos asociados, proceder con la eliminación
            cursor.execute(q_delete_categoria(), (categoria_id,))
            conn.commit()
            return cursor.rowcount > 0
    except DatabaseError:
        raise
    except ValueError:
        raise
    except pymysql.Error as e:
        raise DatabaseError(f"Error al eliminar categoría: {e}") from e
