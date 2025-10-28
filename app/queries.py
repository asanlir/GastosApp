"""
Módulo centralizado de queries SQL.

- Provee funciones pequeñas que devuelven (sql, params)
- Evita SQL embebido en rutas/servicios y documenta consultas comunes

Contrato:
- Cada helper retorna una tupla: (query: str, params: tuple | list)
- Nunca formatear valores directamente en el SQL (usar placeholders %s)
- Para ordenar por meses, usamos los fragmentos de app.constants
"""
from typing import Optional, Tuple, List

from .constants import MESES, SQL_MONTH_FIELD, SQL_MONTH_FIELD_DESC


# ==========================
# Utilidades de composición
# ==========================

def _month_field_literal() -> str:
    """Devuelve FIELD(mes, 'Enero', ..., 'Diciembre') con literales."""
    return SQL_MONTH_FIELD


# ==========================
# Gastos
# ==========================

def q_gasto_by_id(gasto_id: int) -> Tuple[str, Tuple[int]]:
    sql = """
        SELECT g.id,
               c.nombre AS categoria,
               g.descripcion,
               g.monto,
               g.mes,
               g.anio
        FROM gastos g
        LEFT JOIN categorias c ON g.categoria = c.nombre
        WHERE g.id = %s
    """
    return sql, (gasto_id,)


def q_list_gastos(mes: Optional[str] = None,
                  anio: Optional[int] = None,
                  categoria: Optional[str] = None) -> Tuple[str, List]:
    sql = """
        SELECT g.id,
               c.nombre AS categoria,
               g.descripcion,
               g.monto,
               g.mes,
               g.anio
        FROM gastos g
        LEFT JOIN categorias c ON g.categoria = c.nombre
        WHERE 1=1
    """
    params: List = []
    if mes:
        sql += " AND g.mes = %s"
        params.append(mes)
    if anio:
        sql += " AND g.anio = %s"
        params.append(anio)
    if categoria:
        sql += " AND g.categoria = %s"
        params.append(categoria)

    sql += f""" ORDER BY anio DESC,
            {_month_field_literal()},
            id DESC;"""
    return sql, params


def q_categoria_nombre_by_id() -> str:
    return "SELECT nombre FROM categorias WHERE id = %s;"


def q_insert_gasto() -> str:
    return (
        "INSERT INTO gastos (categoria, descripcion, monto, mes, anio) "
        "VALUES (%s, %s, %s, %s, %s);"
    )


def q_update_gasto() -> str:
    return (
        "UPDATE gastos SET categoria = %s, descripcion = %s, monto = %s "
        "WHERE id = %s;"
    )


def q_delete_gasto() -> str:
    return "DELETE FROM gastos WHERE id = %s;"


def q_total_gastos(mes: Optional[str] = None, anio: Optional[int] = None) -> Tuple[str, List]:
    sql = "SELECT SUM(monto) as total FROM gastos WHERE 1=1"
    params: List = []
    if mes:
        sql += " AND mes = %s"
        params.append(mes)
    if anio:
        sql += " AND anio = %s"
        params.append(anio)
    return sql, params


# ==========================
# Presupuesto
# ==========================

def q_presupuesto_vigente() -> str:
    """Presupuesto vigente hasta un mes/año concreto.

    Nota: mantiene los FIELD con literales para ordenación estable.
    """
    return f"""
        SELECT monto
        FROM presupuesto
        WHERE (anio < %s)
           OR (anio = %s AND {SQL_MONTH_FIELD} <= FIELD(%s, '{("', '").join(MESES)}'))
        ORDER BY anio DESC, {SQL_MONTH_FIELD_DESC}
        LIMIT 1;
    """


def q_historial_presupuestos() -> str:
    return f"""
        SELECT mes, anio, monto
        FROM presupuesto
        ORDER BY anio, {SQL_MONTH_FIELD};
    """


def q_presupuesto_exists() -> str:
    return "SELECT id FROM presupuesto WHERE mes = %s AND anio = %s;"


def q_update_presupuesto() -> str:
    return "UPDATE presupuesto SET monto = %s WHERE mes = %s AND anio = %s;"


def q_insert_presupuesto() -> str:
    return "INSERT INTO presupuesto (mes, anio, monto) VALUES (%s, %s, %s);"


def q_sum_gastos_hasta_mes() -> str:
    return f"""
        SELECT SUM(monto) AS total_gastos
        FROM gastos
        WHERE anio = %s
          AND {SQL_MONTH_FIELD} <= FIELD(%s, '{("', '").join(MESES)}');
    """


# ==========================
# Categorías
# ==========================

def q_list_categorias() -> str:
    return "SELECT * FROM categorias ORDER BY nombre ASC;"


def q_insert_categoria() -> str:
    return "INSERT INTO categorias (nombre) VALUES (%s);"


def q_update_categoria() -> str:
    return "UPDATE categorias SET nombre = %s WHERE id = %s;"


def q_delete_categoria() -> str:
    return "DELETE FROM categorias WHERE id = %s;"


# ==========================
# Consultas para gráficos
# ==========================

def q_gastos_por_categoria_mes() -> str:
    return (
        "SELECT categoria, SUM(monto) as total "
        "FROM gastos WHERE mes = %s AND anio = %s "
        "GROUP BY categoria ORDER BY categoria;"
    )


def q_gasolina_por_mes() -> str:
    return f"""
        SELECT mes, SUM(monto) AS total
        FROM gastos
        WHERE categoria = 'Gasolina' AND anio = %s
        GROUP BY mes
        ORDER BY {SQL_MONTH_FIELD};
    """


def q_historico_categoria_grouped() -> str:
    return f"""
        SELECT anio, mes, categoria, descripcion, SUM(monto) AS total
        FROM gastos
        WHERE categoria = %s
        GROUP BY anio, mes, categoria, descripcion
        ORDER BY anio ASC, {SQL_MONTH_FIELD};
    """


def q_gastos_mensuales_aggregates() -> str:
    return f"""
        SELECT mes,
               SUM(CASE WHEN categoria = 'Alquiler' THEN 0 ELSE monto END) as total_sin_alquiler,
               SUM(monto) as total_con_alquiler
        FROM gastos
        WHERE anio = %s
        GROUP BY mes
        ORDER BY {SQL_MONTH_FIELD};
    """


def q_presupuestos_mensuales_por_anio() -> str:
    return f"""
        SELECT mes, monto as presupuesto_mensual
        FROM presupuesto
        WHERE anio = %s
        ORDER BY {SQL_MONTH_FIELD};
    """
