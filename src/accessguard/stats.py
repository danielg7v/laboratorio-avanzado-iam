"""Medidas de asociación entre variables categóricas (todas las columnas del dataset IAM lo son)."""
import numpy as np
import pandas as pd
from scipy import sparse


def cramers_v(x: pd.Series, y: pd.Series) -> float:
    """V de Cramér con corrección de sesgo (Bergsma). 0 = independientes, 1 = una determina a la otra.

    Usa una tabla de contingencia dispersa: las columnas de alta cardinalidad (miles de categorías)
    no caben como tabla densa. chi2 = suma(O^2 / E) - n sobre las celdas no vacías.
    """
    xi, _ = pd.factorize(x)
    yi, _ = pd.factorize(y)
    n = len(xi)
    r, k = xi.max() + 1, yi.max() + 1
    if r < 2 or k < 2:
        return 0.0
    table = sparse.coo_matrix((np.ones(n), (xi, yi)), shape=(r, k)).tocsr().tocoo()
    row_tot = np.asarray(table.tocsr().sum(axis=1)).ravel()
    col_tot = np.asarray(table.tocsr().sum(axis=0)).ravel()
    expected = row_tot[table.row] * col_tot[table.col] / n
    chi2 = float((table.data ** 2 / expected).sum() - n)
    phi2 = max(0.0, chi2 / n - (k - 1) * (r - 1) / (n - 1))
    r_c = r - (r - 1) ** 2 / (n - 1)
    k_c = k - (k - 1) ** 2 / (n - 1)
    denom = min(k_c - 1, r_c - 1)
    return float(np.sqrt(phi2 / denom)) if denom > 0 else 0.0


def cramers_matrix(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Matriz simétrica de V de Cramér entre todas las columnas de `cols`."""
    out = pd.DataFrame(np.eye(len(cols)), index=cols, columns=cols)
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            out.loc[a, b] = out.loc[b, a] = cramers_v(df[a], df[b])
    return out
