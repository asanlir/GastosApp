"""Service for generating charts and data visualizations."""

from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from typing import List, Dict, Optional, Any

from ..database import cursor_context
from app.queries import (
    q_gastos_por_categoria_mes,
    q_gasolina_por_mes,
    q_historico_categoria_grouped,
    q_gastos_mensuales_aggregates,
    q_presupuestos_mensuales_por_anio,
)


def get_months() -> List[str]:
    """Returns the list of months in Spanish."""
    return ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


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

        return fig.to_html(full_html=False)


def generate_gas_chart(anio: int) -> str:
    """Generate simple bar chart for gas expenses for a specific year."""
    meses = get_months()

    with cursor_context() as (_, cursor):
        cursor.execute(q_gasolina_por_mes(), (anio,))
        datos_gasolina = cursor.fetchall()

    # Crear dataframe con todos los meses del año
    df = pd.DataFrame({
        "mes": meses,
        "total": [0] * 12
    })

    # Añadir datos existentes
    if datos_gasolina:
        df_datos = pd.DataFrame(datos_gasolina)
        df = df.merge(df_datos, on="mes", how="left")
        df["total"] = df["total_y"].fillna(df["total_x"])

    # Ordenar meses
    df["mes"] = pd.Categorical(df["mes"], categories=meses, ordered=True)
    df = df.sort_values("mes")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["mes"],
        y=df["total"],
        name="Gasolina",
        marker_color="lightblue",
        hovertemplate="%{y:.2f}€<extra></extra>"
    ))

    fig.update_layout(
        title=f"Gastos en Gasolina {anio}",
        yaxis_title="Euros",
        xaxis_title="Mes",
        xaxis=dict(type="category", tickangle=-30),
        showlegend=False
    )

    return fig.to_html(full_html=False)


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

    # Crear dataframe con todos los meses del año actual
    anio_actual = datetime.now().year
    df_fechas = pd.DataFrame({
        "anio": [anio_actual] * 12,
        "mes": meses
    })

    df = df_fechas.merge(df, on=["anio", "mes"], how="left").fillna(0)
    df["mes"] = pd.Categorical(df['mes'], categories=meses, ordered=True)
    df = df.sort_values(["anio", "mes"])
    df["orden_fecha"] = df.apply(
        lambda row: f"{row['mes']} {row['anio']}", axis=1)

    meses_completos = df['orden_fecha'].unique()
    orden_descripciones = sorted(
        df[df['categoria'] == categoria]['descripcion'].unique())

    fig = go.Figure()

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
            hovertemplate=f"{descripcion} {{y:.2f}}€<extra></extra>"
        ))

    fig.update_layout(
        barmode='stack',
        title=f"Gastos {categoria}",
        yaxis_title="Monto (€)",
        xaxis=dict(type='category', tickangle=-30),
    )

    return fig.to_html(full_html=False)


def generate_comparison_chart(anio: int) -> Dict[str, Any]:
    """
    Generate budget comparison chart showing monthly expenses vs budget.

    Shows monthly expenses (excluding rent) with color-coded bars (red if over budget, 
    green if under budget) and a line showing cumulative budget balance.

    The cumulative balance is calculated considering ALL expenses (including rent)
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
                             "mes", "total_sin_alquiler", "total_con_alquiler"])
    df = df_fechas.merge(df_gastos, on=["mes"], how="left").fillna(0)

    # Añadir presupuestos mensuales
    df_presupuesto = pd.DataFrame(datos_presupuesto, columns=[
                                  "mes", "presupuesto_mensual"])
    df = df.merge(df_presupuesto, on=["mes"], how="left")

    # Asegurar que tenemos un presupuesto para cada mes (usar el último conocido si falta)
    df["presupuesto_mensual"] = df["presupuesto_mensual"].fillna(
        df["presupuesto_mensual"].iloc[0] if not df["presupuesto_mensual"].empty else 0)

    # Calcular métricas
    df["excede_presupuesto"] = df["total_sin_alquiler"] > df["presupuesto_mensual"]
    df["saldo_mensual"] = df["presupuesto_mensual"] - \
        df["total_con_alquiler"]  # Usa total_con_alquiler
    df["saldo_acumulado"] = df["saldo_mensual"].cumsum()

    # Ordenar meses
    df["mes"] = pd.Categorical(df["mes"], categories=meses, ordered=True)
    df = df.sort_values("mes")

    # Crear gráfico
    fig = go.Figure()

    # Barras de gastos variables (sin alquiler)
    colores = ["red" if excede else "green" for excede in df["excede_presupuesto"]]
    fig.add_trace(go.Bar(
        x=df["mes"],
        y=df["total_sin_alquiler"],
        name="Gastos (sin alquiler)",
        marker_color=colores,
        hovertemplate="%{y:.2f}€<extra></extra>"
    ))

    # Línea de saldo presupuestario acumulado
    fig.add_trace(go.Scatter(
        x=df["mes"],
        y=df["saldo_acumulado"],
        name="Saldo Presupuestario Acumulado",
        mode="lines+markers",
        line=dict(color="blue", width=2),
        hovertemplate="Saldo: %{y:.2f}€<extra></extra>"
    ))

    fig.update_layout(
        title=f"Comparación con Presupuesto {anio}",
        yaxis_title="Euros",
        xaxis_title="Mes",
        xaxis=dict(type="category", tickangle=-30),
        showlegend=True,
        barmode="relative"
    )

    return {
        "chart": fig.to_html(full_html=False),
        "df_comparacion": df
    }
