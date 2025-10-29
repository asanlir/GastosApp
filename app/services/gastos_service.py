"""
Servicio que maneja la lógica de negocio relacionada con los gastos.
"""
from typing import Optional, List, Dict, Any
import pymysql
from app.database import cursor_context
from app.utils_df import decimal_to_float
from app.exceptions import DatabaseError, ValidationError
from app.logging_config import get_logger
from app.queries import (
    q_gasto_by_id,
    q_list_gastos,
    q_categoria_nombre_by_id,
    q_insert_gasto,
    q_update_gasto,
    q_delete_gasto,
    q_total_gastos,
)

logger = get_logger(__name__)


def get_gasto_by_id(gasto_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene un gasto por su ID.

    Args:
        gasto_id: ID del gasto a buscar

    Returns:
        Diccionario con los datos del gasto o None si no existe
    """
    logger.debug(f"Obteniendo gasto con ID: {gasto_id}")
    with cursor_context() as (_, cursor):
        query, params = q_gasto_by_id(gasto_id)
        cursor.execute(query, params)
        result = cursor.fetchone()
        if result:
            logger.debug(f"Gasto encontrado: {result['descripcion']}")
        else:
            logger.debug(f"Gasto con ID {gasto_id} no encontrado")
        return result


def list_gastos(mes: Optional[str] = None,
                anio: Optional[int] = None,
                categoria: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Obtiene la lista de gastos aplicando filtros opcionales.

    Args:
        mes: Mes para filtrar los gastos (opcional)
        anio: Año para filtrar los gastos (opcional)
        categoria: Categoría para filtrar los gastos (opcional)

    Returns:
        Lista de diccionarios con los gastos encontrados
    """
    with cursor_context() as (_, cursor):
        query, params = q_list_gastos(mes=mes, anio=anio, categoria=categoria)
        cursor.execute(query, params)
        return list(cursor.fetchall())


def add_gasto(categoria_id: str, descripcion: str, monto: float, mes: str, anio: int) -> bool:
    """
    Agrega un nuevo gasto.

    Args:
        categoria_id: ID de la categoría del gasto
        descripcion: Descripción del gasto
        monto: Monto del gasto
        mes: Mes del gasto
        anio: Año del gasto

    Returns:
        True si el gasto fue agregado correctamente, False en caso contrario

    Raises:
        ValidationError: Si la categoría no existe o datos inválidos
        DatabaseError: Si hay un error en la base de datos
    """
    logger.info(f"Agregando gasto: {descripcion} - {monto}€ ({mes} {anio})")
    try:
        with cursor_context() as (conn, cursor):
            # Obtener el nombre de la categoría
            cursor.execute(q_categoria_nombre_by_id(), (categoria_id,))
            categoria_result = cursor.fetchone()

            if not categoria_result:
                logger.warning(
                    f"Intento de agregar gasto con categoría inexistente: ID {categoria_id}")
                raise ValidationError(
                    f"Categoría con ID {categoria_id} no existe")

            categoria = categoria_result["nombre"]

            # Insertar el gasto
            cursor.execute(
                q_insert_gasto(),
                (categoria, descripcion, float(monto), mes, int(anio))
            )
            conn.commit()
            logger.info(f"Gasto agregado exitosamente: {descripcion}")
            return True

    except (ValidationError, DatabaseError):
        raise
    except pymysql.Error as e:
        logger.error(f"Error de base de datos al agregar gasto: {e}")
        raise DatabaseError(f"Error al agregar gasto: {e}") from e
    except (ValueError, TypeError) as e:
        logger.error(f"Datos inválidos al agregar gasto: {e}")
        raise ValidationError(f"Datos inválidos: {e}") from e


def update_gasto(gasto_id: int, categoria_id: str, descripcion: str, monto: float) -> bool:
    """
    Actualiza un gasto existente.

    Args:
        id: ID del gasto a actualizar
        categoria_id: Nuevo ID de categoría
        descripcion: Nueva descripción
        monto: Nuevo monto

    Returns:
        True si el gasto fue actualizado correctamente, False en caso contrario

    Raises:
        ValidationError: Si la categoría no existe o datos inválidos
        DatabaseError: Si hay un error en la base de datos
    """
    try:
        with cursor_context() as (conn, cursor):
            # Obtener el nombre de la categoría: admitir id (numérico) o nombre directo
            if isinstance(categoria_id, (int,)) or (isinstance(categoria_id, str) and categoria_id.isdigit()):
                cursor.execute(q_categoria_nombre_by_id(),
                               (int(categoria_id),))
                categoria_result = cursor.fetchone()
                if not categoria_result:
                    raise ValidationError(
                        f"Categoría con ID {categoria_id} no existe")
                categoria = categoria_result["nombre"]
            else:
                # ya viene como nombre
                categoria = str(categoria_id)

            # Actualizar el gasto
            cursor.execute(q_update_gasto(), (categoria,
                           descripcion, float(monto), gasto_id))
            conn.commit()
            return cursor.rowcount > 0

    except (ValidationError, DatabaseError):
        raise
    except pymysql.Error as e:
        raise DatabaseError(f"Error al actualizar gasto: {e}") from e
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Datos inválidos: {e}") from e


def delete_gasto(gasto_id: int) -> bool:
    """
    Elimina un gasto existente.

    Args:
        id: ID del gasto a eliminar

    Returns:
        True si el gasto fue eliminado correctamente, False en caso contrario

    Raises:
        DatabaseError: Si hay un error en la base de datos
    """
    try:
        with cursor_context() as (conn, cursor):
            cursor.execute(q_delete_gasto(), (gasto_id,))
            conn.commit()
            return cursor.rowcount > 0
    except DatabaseError:
        raise
    except pymysql.Error as e:
        raise DatabaseError(f"Error al eliminar gasto: {e}") from e


def get_total_gastos(mes: Optional[str] = None, anio: Optional[int] = None) -> float:
    """
    Calcula el total de gastos para un período específico.

    Args:
        mes: Mes para filtrar los gastos (opcional)
        anio: Año para filtrar los gastos (opcional)

    Returns:
        Total de gastos para el período especificado
    """
    with cursor_context() as (_, cursor):
        query, params = q_total_gastos(mes=mes, anio=anio)
        cursor.execute(query, params)
    result = cursor.fetchone()
    return decimal_to_float(result["total"]) if result and result["total"] is not None else 0.0
