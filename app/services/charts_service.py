"""Servicio para generar gráficos y visualizaciones de datos."""

import pandas as pd
import plotly.graph_objects as go
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from dateutil.relativedelta import relativedelta

from ..database import cursor_context
from app.constants import MESES
from app.utils_df import (
    set_month_order,
    ensure_all_months,
    df_from_rows,
    to_plot_html,
    ffill_by_month_inplace,
)
from app.queries import (
    q_gastos_por_categoria_mes,
    q_gasolina_por_mes,
    q_historico_categoria_grouped,
    q_gastos_mensuales_aggregates,
    q_presupuestos_mensuales_por_anio,
    q_gastos_mensuales_last_n_months,
    q_presupuestos_last_n_months,
    q_historico_categoria_last_n_months,
    q_gasolina_last_n_months,
)


def get_months() -> List[str]:
    """Devuelve la lista de meses en español (delegado a constants)."""
    return MESES


def get_last_12_months(mes: str = None, anio: int = None) -> List[Tuple[str, int]]:
    """
    Devuelve una lista con 12 meses.

    Args:
        mes: Mes de referencia. Si se proporciona junto con anio, devuelve
             12 meses centrados en esa fecha (del mismo año).
        anio: Año de referencia.

    Returns:
        Lista de tuplas (mes_nombre, anio) ordenadas cronológicamente.
        - Si mes/anio se proporcionan: 12 meses del año especificado
        - Si no: últimos 12 meses desde hoy
        Ejemplo: [('Febrero', 2025), ('Marzo', 2025), ..., ('Enero', 2026)]
    """
    if mes and anio:
        # Devolver los 12 meses del año especificado
        return [(mes_nombre, anio) for mes_nombre in MESES]

    # Comportamiento por defecto: últimos 12 meses desde hoy
    today = datetime.now()
    months_list = []

    for i in range(11, -1, -1):  # De 11 meses atrás hasta hoy
        date = today - relativedelta(months=i)
        mes_nombre = MESES[date.month - 1]  # MESES es 0-indexed
        months_list.append((mes_nombre, date.year))

    return months_list


def format_month_year(mes: str, anio: int) -> str:
    """Formatea mes y año como 'Enero \'26'."""
    return f"{mes} '{str(anio)[-2:]}"


def generate_pie_chart(mes: str, anio: int) -> Optional[str]:
    """Generar gráfico de torta para gastos por categoría."""
    with cursor_context() as (_, cursor):
        cursor.execute(q_gastos_por_categoria_mes(), (mes, anio))
        gastos_por_categoria = cursor.fetchall()

        if not gastos_por_categoria:
            return None

        categorias = [gasto['categoria'] for gasto in gastos_por_categoria]
        montos = [gasto['total'] for gasto in gastos_por_categoria]
        fig = go.Figure(
            data=[go.Pie(labels=categorias, values=montos, sort=False)])

        # Añadir título con el mes actual
        fig.update_layout(title=f'Distribución de gastos {mes}')

    return to_plot_html(fig)


def generate_gas_chart(anio: int = None, mes: str = None) -> str:
    """
    Generar gráfico de barras simple para gastos de gasolina.

    Args:
        anio: Año a visualizar. Si se proporciona, muestra 12 meses de ese año.
        mes: Mes de referencia (usado junto con anio).
             Si no se proporcionan, muestra últimos 12 meses desde hoy.
    """
    last_12_months = get_last_12_months(mes, anio)

    # Crear placeholders para la cláusula IN
    placeholders = ','.join(['(%s, %s)'] * len(last_12_months))
    query = q_gasolina_last_n_months().replace('PLACEHOLDER', placeholders)

    # Aplanar la lista de tuplas para los parámetros
    params = [item for month_year in last_12_months for item in month_year]

    with cursor_context() as (_, cursor):
        cursor.execute(query, params)
        datos_gasolina = cursor.fetchall()

    # Crear DataFrame con los datos
    df = pd.DataFrame(datos_gasolina, columns=["mes", "anio", "total"])
    if not df.empty:
        df["total"] = df["total"].astype(float)

    # Crear DataFrame completo con todos los meses (rellena 0 si faltan)
    df_completo = pd.DataFrame(last_12_months, columns=["mes", "anio"])
    df = df_completo.merge(df, on=["mes", "anio"], how="left")
    df = df.infer_objects(copy=False)
    df = df.fillna(0)

    # Formato de mes con año
    df["mes_formateado"] = df.apply(
        lambda row: format_month_year(row["mes"], row["anio"]), axis=1)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["mes_formateado"],
        y=df["total"],
        name="Gasolina",
        marker_color="#3498db",
        hovertemplate="%{y:.2f}€<extra></extra>"
    ))

    # Título dinámico según contexto
    if anio:
        titulo = f"Gastos Gasolina ({anio})"
    else:
        titulo = "Gastos Gasolina"

    fig.update_layout(
        title=titulo,
        yaxis_title="Monto (€)",
        xaxis=dict(type="category", tickangle=-30),
        showlegend=False
    )

    return to_plot_html(fig)


def generate_category_chart(categoria: str, anio: int = None, mes: str = None) -> str:
    """
    Generar gráfico de barras apiladas para una categoría específica.

    Args:
        categoria: Nombre de la categoría.
        anio: Año a visualizar. Si se proporciona, muestra 12 meses de ese año.
        mes: Mes de referencia (usado junto con anio).
             Si no se proporcionan, muestra últimos 12 meses desde hoy.
    """
    if categoria == 'Gasolina':
        return generate_gas_chart(anio, mes)

    last_12_months = get_last_12_months(mes, anio)

    # Crear placeholders para la cláusula IN
    placeholders = ','.join(['(%s, %s)'] * len(last_12_months))
    query = q_historico_categoria_last_n_months().replace('PLACEHOLDER', placeholders)

    # Parámetros: categoría + tuplas (mes, anio)
    params = [categoria] + \
        [item for month_year in last_12_months for item in month_year]

    with cursor_context() as (_, cursor):
        cursor.execute(query, params)
        datos_historico = cursor.fetchall()

    df = pd.DataFrame(datos_historico, columns=[
        "anio", "mes", "categoria", "descripcion", "total"])

    if not df.empty:
        df["total"] = df["total"].astype(float)

    # Crear un identificador único para cada mes ordenado cronológicamente
    mes_order_map = {(mes, anio): idx for idx, (mes, anio)
                     in enumerate(last_12_months)}

    # Si hay datos, agregar el orden
    if not df.empty:
        df["orden"] = df.apply(lambda row: mes_order_map.get(
            (row['mes'], row['anio']), 999), axis=1)
        df = df.sort_values("orden")

    # Formato coherente: "Enero '25"
    if not df.empty:
        df["orden_fecha"] = df.apply(
            lambda row: format_month_year(row['mes'], row['anio']), axis=1)

    # Crear lista de todos los meses formateados en orden
    meses_completos = [format_month_year(mes, anio)
                       for mes, anio in last_12_months]

    # Obtener descripciones únicas que tengan datos
    orden_descripciones = sorted(
        df[df['total'] > 0]['descripcion'].unique()) if not df.empty else []

    fig = go.Figure()

    # Si no hay descripciones, crear una traza invisible
    if len(orden_descripciones) == 0:
        fig.add_trace(go.Bar(
            x=meses_completos,
            y=[0] * len(meses_completos),
            name="Sin datos",
            visible=True,
            showlegend=False,
            hoverinfo='skip'
        ))
    else:
        for descripcion in orden_descripciones:
            df_desc = df[df['descripcion'] == descripcion].copy()

            # Crear DataFrame con todos los meses
            df_meses_vacios = pd.DataFrame({"orden_fecha": meses_completos})
            df_desc = pd.merge(df_meses_vacios, df_desc,
                               on="orden_fecha", how="left")
            df_desc = df_desc.infer_objects(copy=False)
            df_desc = df_desc.fillna({"total": 0})

            fig.add_trace(go.Bar(
                x=df_desc['orden_fecha'],
                y=df_desc['total'],
                name=descripcion,
                visible=True,
                hovertemplate=f"{descripcion}: %{{y:.2f}}€<extra></extra>"
            ))

    # Título dinámico según contexto
    if anio:
        titulo = f"Gastos {categoria} ({anio})"
    else:
        titulo = f"Gastos {categoria}"

    fig.update_layout(
        barmode='stack',
        title=titulo,
        yaxis_title="Monto (€)",
        xaxis=dict(type='category', tickangle=-30),
    )

    return to_plot_html(fig)


def generate_comparison_chart(anio: int = None, mes: str = None) -> Dict[str, Any]:
    """
    Generar gráfico de comparación de presupuesto mostrando gastos mensuales vs presupuesto.

    Muestra gastos mensuales (solo categorías con incluir_en_resumen=TRUE) con barras codificadas por color
    (rojo si excede presupuesto, verde si está por debajo) y una línea mostrando el saldo presupuestario acumulado.

    El saldo acumulado se calcula considerando TODOS los gastos (incluyendo los que no están en resumen)
    comparados contra los presupuestos mensuales que estaban activos en cada mes.

    Args:
        anio: Año a visualizar. Si se proporciona, muestra 12 meses de ese año.
        mes: Mes de referencia (usado junto con anio).
             Si no se proporcionan, muestra últimos 12 meses desde hoy.
    """
    last_12_months = get_last_12_months(mes, anio)

    # Crear placeholders para la cláusula IN
    placeholders = ','.join(['(%s, %s)'] * len(last_12_months))

    # Query para gastos
    query_gastos = q_gastos_mensuales_last_n_months().replace(
        'PLACEHOLDER', placeholders)
    params_gastos = [
        item for month_year in last_12_months for item in month_year]

    # Query para presupuestos
    query_presupuestos = q_presupuestos_last_n_months().replace(
        'PLACEHOLDER', placeholders)
    params_presupuestos = [
        item for month_year in last_12_months for item in month_year]

    with cursor_context() as (_, cursor):
        # Obtener gastos mensuales (con y sin alquiler)
        cursor.execute(query_gastos, params_gastos)
        datos_gastos = cursor.fetchall()

        # Obtener presupuestos mensuales históricos
        cursor.execute(query_presupuestos, params_presupuestos)
        datos_presupuesto = cursor.fetchall()

    # Preparar DataFrame base con todos los meses
    df_fechas = pd.DataFrame(last_12_months, columns=["mes", "anio"])

    # Preparar datos de gastos
    df_gastos = pd.DataFrame(datos_gastos, columns=[
                             "mes", "anio", "total_incluido_resumen", "total_con_todas"])
    if not df_gastos.empty:
        df_gastos["total_incluido_resumen"] = df_gastos["total_incluido_resumen"].astype(
            float)
        df_gastos["total_con_todas"] = df_gastos["total_con_todas"].astype(
            float)

    df = df_fechas.merge(df_gastos, on=["mes", "anio"], how="left")
    df = df.infer_objects(copy=False)
    df = df.fillna(0)

    # Añadir presupuestos mensuales
    df_presupuesto = pd.DataFrame(datos_presupuesto, columns=[
                                  "mes", "anio", "presupuesto_mensual"])
    if not df_presupuesto.empty:
        df_presupuesto["presupuesto_mensual"] = df_presupuesto["presupuesto_mensual"].astype(
            float)

    df = df.merge(df_presupuesto, on=["mes", "anio"], how="left")

    # Forward-fill presupuestos (propagar el último presupuesto conocido)
    df["presupuesto_mensual"] = df["presupuesto_mensual"].infer_objects(
        copy=False)
    df["presupuesto_mensual"] = df["presupuesto_mensual"].ffill()
    df["presupuesto_mensual"] = df["presupuesto_mensual"].fillna(0)

    # Calcular métricas
    df["excede_presupuesto"] = df["total_con_todas"] > df["presupuesto_mensual"]
    df["saldo_mensual"] = df["presupuesto_mensual"] - df["total_con_todas"]
    df["saldo_acumulado"] = df["saldo_mensual"].cumsum()

    # Marcar meses con gastos
    df["tiene_gastos"] = df["total_con_todas"] > 0

    # Calcular gasto medio acumulado (solo gastos incluidos en resumen, sin alquiler)
    df["gasto_acumulado_resumen"] = df["total_incluido_resumen"].cumsum()
    df["num_meses_con_gastos"] = df["tiene_gastos"].cumsum()
    df["gasto_medio_acumulado"] = df.apply(
        lambda row: row["gasto_acumulado_resumen"] /
        row["num_meses_con_gastos"] if row["num_meses_con_gastos"] > 0 else 0,
        axis=1
    )

    # Formato de mes con año
    df["mes_formateado"] = df.apply(
        lambda row: format_month_year(row["mes"], row["anio"]), axis=1)

    # Crear gráfico
    fig = go.Figure()

    # Barras de gastos variables (sin alquiler) - colores según si excede presupuesto TOTAL
    colores = ["red" if excede else "green" for excede in df["excede_presupuesto"]]
    fig.add_trace(go.Bar(
        x=df["mes_formateado"],
        y=df["total_incluido_resumen"],
        name="Gastos (sin alquiler)",
        marker_color=colores,
        hovertemplate="%{y:.2f}€<extra></extra>",
        showlegend=False
    ))

    # Línea de saldo presupuestario acumulado - solo para meses con gastos
    df_con_gastos = df[df["tiene_gastos"]].copy()
    fig.add_trace(go.Scatter(
        x=df_con_gastos["mes_formateado"],
        y=df_con_gastos["saldo_acumulado"],
        name="Saldo acumulado",
        mode="lines+markers",
        line=dict(color="blue", width=2),
        hovertemplate="Saldo: %{y:.2f}€<extra></extra>"
    ))

    # Línea de gasto medio acumulado - solo para meses con gastos
    fig.add_trace(go.Scatter(
        x=df_con_gastos["mes_formateado"],
        y=df_con_gastos["gasto_medio_acumulado"],
        name="Gasto medio",
        mode="lines+markers",
        line=dict(color='#17BECF', width=2, dash='dash'),
        hovertemplate="Gasto medio: %{y:.2f}€<extra></extra>"
    ))

    # Título dinámico según contexto
    if anio:
        titulo = f"Evolución de Presupuesto y Acumulado ({anio})"
    else:
        titulo = "Evolución de Presupuesto y Acumulado (últimos 12 meses)"

    fig.update_layout(
        title=titulo,
        yaxis_title="Monto (€)",
        xaxis_title="",
        xaxis=dict(type="category", tickangle=-30),
        showlegend=True,
        barmode="relative"
    )

    return {
        "chart": to_plot_html(fig),
        "df_comparacion": df
    }
