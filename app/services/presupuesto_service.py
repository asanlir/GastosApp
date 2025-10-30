"""
Servicio que maneja la lógica de negocio relacionada con los presupuestos.
"""
from typing import Dict, Any
import pymysql
from app.constants import MESES
from app.database import cursor_context
from app.exceptions import DatabaseError, ValidationError
from app.utils_df import decimal_to_float
from app.queries import (
    q_presupuesto_vigente,
    q_historial_presupuestos,
    q_presupuesto_exists,
    q_update_presupuesto,
    q_insert_presupuesto,
    q_sum_gastos_hasta_mes,
)


def get_presupuesto_mensual(mes: str, anio: int) -> float:
    """
    Obtiene el presupuesto vigente para un mes y año específicos.
    Si no hay presupuesto para ese mes/año, busca el último presupuesto anterior.

    Args:
        mes: Mes para el que se busca el presupuesto
        anio: Año para el que se busca el presupuesto

    Returns:
        Monto del presupuesto vigente
    """
    with cursor_context() as (_, cursor):
        cursor.execute(q_presupuesto_vigente(), (anio, anio, mes))
    presupuesto_result = cursor.fetchone()
    return decimal_to_float(presupuesto_result["monto"]) if presupuesto_result else 0.0


def get_historial_presupuestos() -> Dict[str, Any]:
    """
    Obtiene el historial completo de presupuestos.

    Returns:
        Diccionario con el historial de presupuestos
    """
    with cursor_context() as (_, cursor):
        cursor.execute(q_historial_presupuestos())
        return {"presupuestos": cursor.fetchall()}


def update_presupuesto(mes: str, anio: int, monto: float) -> bool:
    """
    Actualiza o crea un presupuesto para un mes y año específicos.

    Args:
        mes: Mes del presupuesto
        anio: Año del presupuesto
        monto: Monto del presupuesto

    Returns:
        True si el presupuesto fue actualizado/creado correctamente

    Raises:
        ValidationError: Si los datos son inválidos
        DatabaseError: Si hay un error en la base de datos
    """
    if monto <= 0:
        raise ValidationError("El monto del presupuesto debe ser mayor a cero")

    if mes not in MESES:
        raise ValidationError(f"Mes inválido: {mes}")

    try:
        with cursor_context() as (conn, cursor):
            # Verificar si ya existe un presupuesto para ese mes/año
            cursor.execute(q_presupuesto_exists(), (mes, anio))
            existing = cursor.fetchone()

            if existing:
                # Actualizar presupuesto existente
                cursor.execute(q_update_presupuesto(), (monto, mes, anio))
            else:
                # Crear nuevo presupuesto
                cursor.execute(q_insert_presupuesto(), (mes, anio, monto))

            conn.commit()
            return True

    except (ValidationError, DatabaseError):
        raise
    except pymysql.Error as e:
        raise DatabaseError(f"Error al actualizar presupuesto: {e}") from e
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Datos inválidos: {e}") from e


def calcular_acumulado(mes: str, anio: int) -> float:
    """
    Calcula el presupuesto acumulado hasta un mes específico.
    Suma los presupuestos individuales de cada mes del año hasta el mes dado.

    Args:
        mes: Mes hasta el que se calcula el acumulado
        anio: Año del cálculo

    Returns:
        Monto acumulado del presupuesto (presupuesto total - gastos totales)
    """
    meses = MESES

    mes_index = meses.index(mes)

    # Sumar el presupuesto de cada mes hasta el mes actual
    presupuesto_total_acumulado = 0.0
    for i in range(mes_index + 1):
        mes_actual = meses[i]
        presupuesto_mes = get_presupuesto_mensual(mes_actual, anio)
        presupuesto_total_acumulado += presupuesto_mes

    with cursor_context() as (_, cursor):
        # Obtener total de gastos hasta el mes actual
        cursor.execute(q_sum_gastos_hasta_mes(), (anio, mes))
        row = cursor.fetchone()
    total_val = row["total_gastos"] if row and row["total_gastos"] else 0.0
    total_gastos_anual = decimal_to_float(total_val)

    return presupuesto_total_acumulado - total_gastos_anual
