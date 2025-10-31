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


def add_categoria(nombre: str, mostrar_en_graficas: bool = True, incluir_en_resumen: bool = True) -> bool:
    """
    Agrega una nueva categoría.

    Args:
        nombre: Nombre de la categoría
        mostrar_en_graficas: Si la categoría se muestra en gráficas (default: True)
        incluir_en_resumen: Si la categoría se incluye en el resumen (default: True)

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
            cursor.execute(q_insert_categoria(),
                           (nombre.strip(), mostrar_en_graficas, incluir_en_resumen))
            conn.commit()
            return True
    except DatabaseError:
        raise
    except pymysql.Error as e:
        raise DatabaseError(f"Error al agregar categoría: {e}") from e


def update_categoria(categoria_id: int, nombre: str, mostrar_en_graficas: bool = True, incluir_en_resumen: bool = True) -> bool:
    """
    Actualiza una categoría existente.
    Los gastos asociados se actualizan automáticamente gracias a ON UPDATE CASCADE.

    Args:
        categoria_id: ID de la categoría a actualizar
        nombre: Nuevo nombre de la categoría
        mostrar_en_graficas: Si la categoría se muestra en gráficas
        incluir_en_resumen: Si la categoría se incluye en el resumen

    Returns:
        True si la categoría fue actualizada correctamente, False en caso contrario

    Raises:
        ValidationError: Si el nombre está vacío o ya existe otra categoría con ese nombre
        DatabaseError: Si hay un error en la base de datos
    """
    if not nombre or not nombre.strip():
        raise ValidationError("El nombre de la categoría no puede estar vacío")

    try:
        with cursor_context() as (conn, cursor):
            # Verificar que la categoría existe
            cursor.execute(
                "SELECT nombre, mostrar_en_graficas, incluir_en_resumen FROM categorias WHERE id = %s", (categoria_id,))
            result = cursor.fetchone()

            if not result:
                return False

            nombre_anterior = result['nombre']
            nuevo_nombre = nombre.strip()

            # Si nada cambió, no hacer nada
            if (nombre_anterior == nuevo_nombre and 
                result['mostrar_en_graficas'] == mostrar_en_graficas and 
                result['incluir_en_resumen'] == incluir_en_resumen):
                return True

            # Actualizar la categoría (ON UPDATE CASCADE se encarga de los gastos)
            cursor.execute(q_update_categoria(), (nuevo_nombre,
                           mostrar_en_graficas, incluir_en_resumen, categoria_id))
            conn.commit()
            return True
    except DatabaseError:
        raise
    except pymysql.IntegrityError as e:
        # Error de nombre duplicado (UNIQUE constraint)
        raise ValidationError(
            f"Ya existe una categoría con el nombre '{nombre.strip()}'") from e
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
