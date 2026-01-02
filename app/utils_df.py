"""Utilidades comunes para manejo de DataFrames y meses.

Este módulo centraliza lógica repetitiva usada en services (especialmente charts):
- Lista de meses y orden categórico
- Construcción de DataFrames con todos los meses del año
- Conversión segura Decimal→float
- Helpers para HTML de Plotly
"""
from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Union

import pandas as pd
from decimal import Decimal

from .constants import MESES


def get_months() -> List[str]:
    """Devuelve la lista de meses en español.

    Se delega a ``constants.MESES`` para mantener una única fuente de verdad.
    """
    return MESES


def set_month_order(df: pd.DataFrame, col: str = "mes") -> pd.DataFrame:
    """Aplica orden categórico de meses a la columna indicada.

    Retorna el mismo DataFrame para permitir piping.
    """
    if col in df.columns:
        df[col] = pd.Categorical(df[col], categories=MESES, ordered=True)
    return df


def df_from_rows(rows: Union[Sequence[dict], pd.DataFrame], columns: Optional[Sequence[str]] = None) -> pd.DataFrame:
    """Crea un DataFrame a partir de una lista de dicts o un DataFrame existente.

    - Si ``rows`` ya es un DataFrame, se devuelve una copia.
    - Si está vacío, devuelve un DataFrame vacío con las columnas indicadas (si se proporcionan).
    """
    if isinstance(rows, pd.DataFrame):
        return rows.copy()
    if not rows:
        return pd.DataFrame(columns=list(columns) if columns else None)
    return pd.DataFrame(rows)


def ensure_all_months(
    rows_or_df: Union[Sequence[dict], pd.DataFrame],
    month_col: str = "mes",
    value_cols: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """Devuelve un DataFrame que garantiza presencia de los 12 meses.

    - Construye un DF base con la columna ``month_col`` conteniendo todos los meses de MESES.
    - Hace un merge left con los datos existentes y rellena ausentes con 0 en columnas de valor.
    - Aplica orden categórico y ordena por ``month_col``.
    """
    base = pd.DataFrame({month_col: MESES})
    df = df_from_rows(rows_or_df)

    # Si no hay datos, devolver base con columnas de valor inicializadas a 0
    if df.empty:
        df = base.copy()
        if value_cols:
            for c in value_cols:
                df[c] = 0
        return set_month_order(df, month_col).sort_values(month_col)

    # Limitar columnas al mes + valores si value_cols está definido
    if value_cols:
        keep_cols = [month_col] + list(value_cols)
        df = df[[c for c in keep_cols if c in df.columns]].copy()

    out = base.merge(df, on=month_col, how="left")
    if value_cols:
        for c in value_cols:
            if c in out.columns:
                out[c] = out[c].fillna(0)
    return set_month_order(out, month_col).sort_values(month_col)


def ffill_by_month_inplace(df: pd.DataFrame, col: str, month_col: str = "mes") -> None:
    """Rellena hacia delante los valores de ``col`` respetando el orden de meses.

    Modifica el DataFrame in-place.
    """
    if col not in df.columns or month_col not in df.columns:
        return
    set_month_order(df, month_col)
    df.sort_values(month_col, inplace=True)
    df[col] = df[col].ffill().infer_objects(copy=False)


def decimal_to_float(val, default: float = 0.0) -> float:
    """Convierte Decimal/None/cadenas a float de forma segura.

    - None → default
    - Decimal → float(Decimal)
    - str → float(str)
    - float/int → tal cual
    """
    if val is None:
        return default
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(val)
    except Exception:
        return default


def to_plot_html(fig) -> str:
    """Devuelve el HTML embebible de una figura de Plotly."""
    return fig.to_html(full_html=False)
