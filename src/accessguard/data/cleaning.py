"""Reglas de limpieza del EDA, una función por decisión."""
import pandas as pd

# ROLE_CODE es 1:1 con ROLE_TITLE (343 valores y mapeo exacto en train y test): información duplicada.
REDUNDANT_COLUMNS = ["ROLE_CODE"]


def check_schema(df: pd.DataFrame, expected: list[str]) -> list[str]:
    """Devuelve las columnas esperadas que faltan (lista vacía = esquema correcto)."""
    return [c for c in expected if c not in df.columns]


def find_redundant_pairs(df: pd.DataFrame, cols: list[str]) -> list[tuple[str, str]]:
    """Pares (a, b) donde `a` determina a `b` y `b` determina a `a` (equivalentes uno a uno)."""
    pairs = []
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            if df.groupby(a)[b].nunique().max() == 1 and df.groupby(b)[a].nunique().max() == 1:
                pairs.append((a, b))
    return pairs


def drop_redundant(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """Elimina columnas redundantes (por defecto `REDUNDANT_COLUMNS`) sin alterar el original."""
    columns = REDUNDANT_COLUMNS if columns is None else columns
    return df.drop(columns=[c for c in columns if c in df.columns])
