"""
Servicio que maneja la lógica de negocio relacionada con los gastos.
"""
from typing import Optional, List, Dict, Any
from app.database import cursor_context
from app.queries import (
    q_gasto_by_id,
    q_list_gastos,
    q_categoria_nombre_by_id,
    q_insert_gasto,
    q_update_gasto,
    q_delete_gasto,
    q_total_gastos,
)


def get_gasto_by_id(gasto_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene un gasto por su ID.

    Args:
        gasto_id: ID del gasto a buscar

    Returns:
        Diccionario con los datos del gasto o None si no existe
    """
    with cursor_context() as (_, cursor):
        query, params = q_gasto_by_id(gasto_id)
        cursor.execute(query, params)
        return cursor.fetchone()


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
    """
    try:
        with cursor_context() as (conn, cursor):
            # Obtener el nombre de la categoría
            cursor.execute(q_categoria_nombre_by_id(), (categoria_id,))
            categoria_result = cursor.fetchone()

            if not categoria_result:
                return False

            categoria = categoria_result["nombre"]

            # Insertar el gasto
            cursor.execute(
                q_insert_gasto(),
                (categoria, descripcion, float(monto), mes, int(anio))
            )
            conn.commit()
            return True

    except Exception:
        return False


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
    """
    try:
        with cursor_context() as (conn, cursor):
            # Obtener el nombre de la categoría: admitir id (numérico) o nombre directo
            if isinstance(categoria_id, (int,)) or (isinstance(categoria_id, str) and categoria_id.isdigit()):
                cursor.execute(q_categoria_nombre_by_id(),
                               (int(categoria_id),))
                categoria_result = cursor.fetchone()
                if not categoria_result:
                    return False
                categoria = categoria_result["nombre"]
            else:
                # ya viene como nombre
                categoria = str(categoria_id)

            # Actualizar el gasto
            cursor.execute(q_update_gasto(), (categoria,
                           descripcion, float(monto), gasto_id))
            conn.commit()
            return cursor.rowcount > 0

    except Exception:
        return False


def delete_gasto(gasto_id: int) -> bool:
    """
    Elimina un gasto existente.

    Args:
        id: ID del gasto a eliminar

    Returns:
        True si el gasto fue eliminado correctamente, False en caso contrario
    """
    try:
        with cursor_context() as (conn, cursor):
            cursor.execute(q_delete_gasto(), (gasto_id,))
            conn.commit()
            return cursor.rowcount > 0
    except Exception:
        return False


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
        return float(result["total"]) if result and result["total"] else 0.0
