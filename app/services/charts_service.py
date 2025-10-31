"""Service for generating charts and data visualizations."""

import pandas as pd
import plotly.graph_objects as go
from typing import List, Dict, Optional, Any

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
)


def get_months() -> List[str]:
    """Returns the list of months in Spanish (delegated to constants)."""
    return MESES


def generate_pie_chart(mes: str, anio: int) -> Optional[str]:
    """Generate pie chart for expenses by category."""
    with cursor_context() as (_, cursor):
        cursor.execute(q_gastos_por_categoria_mes(), (mes, anio))
        gastos_por_categoria = cursor.fetchall()

        if not gastos_por_categoria:
            return None

        categorias = [gasto['categoria'] for gasto in gastos_por_categoria]
        montos = [gasto['total'] for gasto in gastos_por_categoria]
        fig = go.Figure(
            data=[go.Pie(labels=categorias, values=montos, sort=False)])

    return to_plot_html(fig)


def generate_gas_chart(anio: int) -> str:
    """Generate simple bar chart for gas expenses for a specific year."""
    with cursor_context() as ((_, cursor)):
        cursor.execute(q_gasolina_por_mes(), (anio,))
        datos_gasolina = cursor.fetchall()

    # DataFrame con todos los meses y totales (rellena 0 si faltan)
    df = ensure_all_months(df_from_rows(datos_gasolina),
                           month_col="mes", value_cols=["total"])

    # Añadir formato de mes con año abreviado (Enero '25)
    df["mes_formateado"] = df["mes"].apply(lambda m: f"{m} '{str(anio)[-2:]}")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["mes_formateado"],
        y=df["total"],
        name="Gasolina",
        marker_color="#3498db",  # Azul coherente con el tema de la app
        hovertemplate="%{y:.2f}€<extra></extra>"
    ))

    fig.update_layout(
        title="Gastos Gasolina",
        yaxis_title="Monto (€)",
        xaxis=dict(type="category", tickangle=-30),
        showlegend=False
    )

    return to_plot_html(fig)


def generate_category_bar_chart(categoria: str, anio: int) -> str:
    """Generate stacked bar chart for a specific category."""
    if categoria == 'Gasolina':
        return generate_gas_chart(anio)

    meses = get_months()

    with cursor_context() as (_, cursor):
        cursor.execute(q_historico_categoria_grouped(), (categoria,))
        datos_historico = cursor.fetchall()

    df = pd.DataFrame(datos_historico, columns=[
        "anio", "mes", "categoria", "descripcion", "total"])

    # Crear dataframe con todos los meses del año seleccionado
    df_fechas = pd.DataFrame({
        "anio": [anio] * 12,
        "mes": meses
    })

    df = df_fechas.merge(df, on=["anio", "mes"], how="left").fillna(0)
    set_month_order(df, "mes")
    df = df.sort_values(["anio", "mes"])
    # Formato coherente: "Enero '25"
    df["orden_fecha"] = df.apply(
        lambda row: f"{row['mes']} '{str(row['anio'])[-2:]}", axis=1)

    meses_completos = df['orden_fecha'].unique()
    orden_descripciones = sorted(
        df[df['categoria'] == categoria]['descripcion'].unique())

    fig = go.Figure()

    # Si no hay descripciones (año futuro sin datos), crear una traza invisible
    # para que se muestren los meses en el eje X
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
            df_meses_vacios = pd.DataFrame({"orden_fecha": meses_completos})
            df_desc = pd.merge(df_meses_vacios, df_desc,
                               on="orden_fecha", how="left").fillna({"total": 0})

            fig.add_trace(go.Bar(
                x=df_desc['orden_fecha'],
                y=df_desc['total'],
                name=descripcion,
                visible=True,
                hovertemplate=f"{descripcion}: %{{y:.2f}}€<extra></extra>"
            ))

    fig.update_layout(
        barmode='stack',
        title=f"Gastos {categoria}",
        yaxis_title="Monto (€)",
        xaxis=dict(type='category', tickangle=-30),
    )

    return to_plot_html(fig)


def generate_comparison_chart(anio: int) -> Dict[str, Any]:
    """
    Generate budget comparison chart showing monthly expenses vs budget.

    Shows monthly expenses (only categories with incluir_en_resumen=TRUE) with color-coded bars 
    (red if over budget, green if under budget) and a line showing cumulative budget balance.

    The cumulative balance is calculated considering ALL expenses (including those not in summary)
    compared against the monthly budgets that were active in each month.
    """
    meses = get_months()

    with cursor_context() as (_, cursor):
        # Obtener gastos mensuales (con y sin alquiler)
        cursor.execute(q_gastos_mensuales_aggregates(), (anio,))
        datos_gastos = cursor.fetchall()

        # Obtener presupuestos mensuales históricos
        cursor.execute(q_presupuestos_mensuales_por_anio(), (anio,))
        datos_presupuesto = cursor.fetchall()

    # Preparar DataFrame base con todos los meses del año
    df_fechas = pd.DataFrame({
        "anio": [anio] * 12,
        "mes": meses
    })

    # Preparar datos de gastos
    df_gastos = pd.DataFrame(datos_gastos, columns=[
                             "mes", "total_incluido_resumen", "total_con_todas"])
    df = df_fechas.merge(df_gastos, on=["mes"], how="left").fillna(0)

    # Añadir presupuestos mensuales
    df_presupuesto = pd.DataFrame(datos_presupuesto, columns=[
                                  "mes", "presupuesto_mensual"])
    df = df.merge(df_presupuesto, on=["mes"], how="left")

    # Asegurar presupuesto para cada mes: forward-fill por orden de mes
    ffill_by_month_inplace(df, "presupuesto_mensual", month_col="mes")
    df["presupuesto_mensual"] = df["presupuesto_mensual"].fillna(0)

    # Calcular métricas
    # La comparación debe hacerse con el gasto TOTAL (incluyendo alquiler)
    df["excede_presupuesto"] = df["total_con_todas"] > df["presupuesto_mensual"]
    df["saldo_mensual"] = df["presupuesto_mensual"] - \
        df["total_con_todas"]  # Usa total_con_todas
    df["saldo_acumulado"] = df["saldo_mensual"].cumsum()

    # Marcar meses con gastos (para mostrar solo esos en la línea)
    df["tiene_gastos"] = df["total_con_todas"] > 0

    # Ordenar meses
    set_month_order(df, "mes")
    df = df.sort_values("mes")

    # Formato coherente: "Enero '25"
    df["mes_formateado"] = df["mes"].apply(lambda m: f"{m} '{str(anio)[-2:]}")

    # Crear gráfico
    fig = go.Figure()

    # Barras de gastos variables (sin alquiler) - colores según si excede presupuesto TOTAL
    colores = ["red" if excede else "green" for excede in df["excede_presupuesto"]]
    fig.add_trace(go.Bar(
        x=df["mes_formateado"],
        y=df["total_incluido_resumen"],
        name="Gastos (sin alquiler)",
        marker_color=colores,
        hovertemplate="%{y:.2f}€<extra></extra>"
    ))

    # Línea de saldo presupuestario acumulado - solo para meses con gastos
    df_con_gastos = df[df["tiene_gastos"]].copy()
    fig.add_trace(go.Scatter(
        x=df_con_gastos["mes_formateado"],
        y=df_con_gastos["saldo_acumulado"],
        name="Saldo Presupuestario Acumulado",
        mode="lines+markers",
        line=dict(color="blue", width=2),
        hovertemplate="Saldo: %{y:.2f}€<extra></extra>"
    ))

    fig.update_layout(
        title="Evolución de Presupuesto y Acumulado",
        yaxis_title="Monto (€)",
        xaxis_title="",
        xaxis=dict(type="category", tickangle=-30),
        showlegend=False,
        barmode="relative"
    )

    return {
        "chart": to_plot_html(fig),
        "df_comparacion": df
    }
