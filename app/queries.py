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
    """
    Obtiene un gasto por su ID con información de categoría.

    Args:
        gasto_id: ID único del gasto.

    Returns:
        (sql, params): Query y parámetros para obtener un gasto por ID.
    """
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
    """
    Lista gastos con filtros opcionales por mes, año y categoría.

    Args:
        mes: Filtrar por mes (ej: "Enero", "Febrero").
        anio: Filtrar por año (ej: 2025).
        categoria: Filtrar por nombre de categoría.

    Returns:
        (sql, params): Query con ordenación DESC por año/mes/id y parámetros.

    Ejemplo:
        sql, params = q_list_gastos(mes="Octubre", anio=2025)
    """
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

    sql += " ORDER BY g.id DESC;"
    return sql, params


def q_categoria_nombre_by_id() -> str:
    """
    Obtiene el nombre de una categoría por su ID.

    Returns:
        SQL para SELECT nombre dado un ID de categoría.
    """
    return "SELECT nombre FROM categorias WHERE id = %s;"


def q_insert_gasto() -> str:
    """
    Inserta un nuevo gasto en la base de datos.

    Parámetros esperados (en orden):
        - categoria (str): Nombre de la categoría.
        - descripcion (str): Descripción del gasto.
        - monto (float): Monto del gasto.
        - mes (str): Mes del gasto.
        - anio (int): Año del gasto.

    Returns:
        SQL INSERT para gastos.
    """
    return (
        "INSERT INTO gastos (categoria, descripcion, monto, mes, anio) "
        "VALUES (%s, %s, %s, %s, %s);"
    )


def q_update_gasto() -> str:
    """
    Actualiza un gasto existente.

    Parámetros esperados (en orden):
        - categoria (str): Nuevo nombre de categoría.
        - descripcion (str): Nueva descripción.
        - monto (float): Nuevo monto.
        - id (int): ID del gasto a actualizar.

    Returns:
        SQL UPDATE para gastos.
    """
    return (
        "UPDATE gastos SET categoria = %s, descripcion = %s, monto = %s "
        "WHERE id = %s;"
    )


def q_delete_gasto() -> str:
    """
    Elimina un gasto por su ID.

    Parámetros esperados:
        - id (int): ID del gasto a eliminar.

    Returns:
        SQL DELETE para gastos.
    """
    return "DELETE FROM gastos WHERE id = %s;"


def q_total_gastos(mes: Optional[str] = None, anio: Optional[int] = None) -> Tuple[str, List]:
    """
    Calcula el total de gastos con filtros opcionales.

    Args:
        mes: Filtrar por mes.
        anio: Filtrar por año.

    Returns:
        (sql, params): Query SUM con filtros y parámetros.
    """
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
    """
    Obtiene el historial completo de presupuestos ordenado por año y mes.

    Returns:
        SQL SELECT para historial de presupuestos.
    """
    return f"""
        SELECT mes, anio, monto
        FROM presupuesto
        ORDER BY anio, {SQL_MONTH_FIELD};
    """


def q_presupuesto_exists() -> str:
    """
    Comprueba si existe un presupuesto para un mes/año concreto.

    Parámetros esperados:
        - mes (str): Mes del presupuesto.
        - anio (int): Año del presupuesto.

    Returns:
        SQL SELECT id para verificar existencia.
    """
    return "SELECT id FROM presupuesto WHERE mes = %s AND anio = %s;"


def q_update_presupuesto() -> str:
    """
    Actualiza el monto de un presupuesto existente.

    Parámetros esperados:
        - monto (float): Nuevo monto.
        - mes (str): Mes del presupuesto.
        - anio (int): Año del presupuesto.

    Returns:
        SQL UPDATE para presupuesto.
    """
    return "UPDATE presupuesto SET monto = %s WHERE mes = %s AND anio = %s;"


def q_insert_presupuesto() -> str:
    """
    Inserta un nuevo presupuesto en la base de datos.

    Parámetros esperados:
        - mes (str): Mes del presupuesto.
        - anio (int): Año del presupuesto.
        - monto (float): Monto del presupuesto.

    Returns:
        SQL INSERT para presupuesto (incluye fecha_cambio con NOW()).
    """
    return "INSERT INTO presupuesto (mes, anio, monto, fecha_cambio) VALUES (%s, %s, %s, NOW());"


def q_sum_gastos_hasta_mes() -> str:
    """
    Suma total de gastos hasta un mes específico en un año.

    Parámetros esperados:
        - anio (int): Año de referencia.
        - mes (str): Mes límite (incluido).

    Returns:
        SQL SELECT SUM con ordenación de meses.
    """
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
    """
    Lista todas las categorías ordenadas alfabéticamente.

    Returns:
        SQL SELECT * para categorías.
    """
    return "SELECT * FROM categorias ORDER BY nombre ASC;"


def q_insert_categoria() -> str:
    """
    Inserta una nueva categoría.

    Parámetros esperados:
        - nombre (str): Nombre de la categoría.
        - mostrar_en_graficas (bool): Si se muestra en gráficas (default TRUE).
        - incluir_en_resumen (bool): Si se incluye en el resumen (default TRUE).

    Returns:
        SQL INSERT para categorías.
    """
    return "INSERT INTO categorias (nombre, mostrar_en_graficas, incluir_en_resumen) VALUES (%s, %s, %s);"


def q_update_categoria() -> str:
    """
    Actualiza una categoría existente.

    Parámetros esperados:
        - nombre (str): Nuevo nombre de la categoría.
        - mostrar_en_graficas (bool): Si se muestra en gráficas.
        - incluir_en_resumen (bool): Si se incluye en el resumen.
        - id (int): ID de la categoría a actualizar.

    Returns:
        SQL UPDATE para categorías.
    """
    return "UPDATE categorias SET nombre = %s, mostrar_en_graficas = %s, incluir_en_resumen = %s WHERE id = %s;"


def q_delete_categoria() -> str:
    """
    Elimina una categoría por su ID.

    Parámetros esperados:
        - id (int): ID de la categoría a eliminar.

    Returns:
        SQL DELETE para categorías.
    """
    return "DELETE FROM categorias WHERE id = %s;"


# ==========================
# Consultas para gráficos
# ==========================

def q_gastos_por_categoria_mes() -> str:
    """
    Agrupa gastos por categoría para un mes/año específico.

    Parámetros esperados:
        - mes (str): Mes de referencia.
        - anio (int): Año de referencia.

    Returns:
        SQL SELECT con SUM agrupado por categoría.

    Uso:
        Para generar gráficos de torta de gastos por categoría.
    """
    return (
        "SELECT categoria, SUM(monto) as total "
        "FROM gastos WHERE mes = %s AND anio = %s "
        "GROUP BY categoria ORDER BY categoria;"
    )


def q_gasolina_por_mes() -> str:
    """
    Obtiene gastos de gasolina agregados por mes en un año.

    Parámetros esperados:
        - anio (int): Año de referencia.

    Returns:
        SQL SELECT SUM para categoría 'Gasolina' ordenado por mes.
    """
    return f"""
        SELECT mes, SUM(monto) AS total
        FROM gastos
        WHERE categoria = 'Gasolina' AND anio = %s
        GROUP BY mes
        ORDER BY {SQL_MONTH_FIELD};
    """


def q_historico_categoria_grouped() -> str:
    """
    Obtiene histórico de gastos de una categoría agrupado por año/mes/descripción.

    Parámetros esperados:
        - categoria (str): Nombre de la categoría a consultar.

    Returns:
        SQL SELECT con agrupación para gráficos apilados por descripción.
    """
    return f"""
        SELECT anio, mes, categoria, descripcion, SUM(monto) AS total
        FROM gastos
        WHERE categoria = %s
        GROUP BY anio, mes, categoria, descripcion
        ORDER BY anio ASC, {SQL_MONTH_FIELD};
    """


def q_gastos_mensuales_aggregates() -> str:
    """
    Obtiene agregados de gastos mensuales para un año.
    
    Calcula dos totales:
    - total_incluido_resumen: solo categorías con incluir_en_resumen=TRUE
    - total_con_todas: todas las categorías

    Parámetros esperados:
        - anio (int): Año de referencia.

    Returns:
        SQL SELECT con CASE para separar gastos según incluir_en_resumen.

    Uso:
        Para gráficos de comparación presupuestaria.
    """
    return f"""
        SELECT g.mes,
               SUM(CASE WHEN c.incluir_en_resumen = TRUE THEN g.monto ELSE 0 END) as total_incluido_resumen,
               SUM(g.monto) as total_con_todas
        FROM gastos g
        LEFT JOIN categorias c ON g.categoria = c.nombre
        WHERE g.anio = %s
        GROUP BY g.mes
        ORDER BY {SQL_MONTH_FIELD};
    """


def q_presupuestos_mensuales_por_anio() -> str:
    """
    Obtiene presupuestos mensuales históricos para un año.

    Parámetros esperados:
        - anio (int): Año de referencia.

    Returns:
        SQL SELECT mes/monto de presupuestos ordenado por mes.
    """
    return f"""
        SELECT mes, monto as presupuesto_mensual
        FROM presupuesto
        WHERE anio = %s
        ORDER BY {SQL_MONTH_FIELD};
    """
