"""Ingeniería de variables para IAM: frecuencias, interacciones, agregaciones y target encoding sin fuga.

Todo lo que aprende de los datos vive dentro de un transformador de scikit-learn (`IAMFeatureBuilder`),
así que dentro de un `Pipeline` se ajusta solo con el entrenamiento de cada pliegue.
"""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import StratifiedGroupKFold

BASE_COLS = ["RESOURCE", "MGR_ID", "ROLE_ROLLUP_2", "ROLE_DEPTNAME", "ROLE_TITLE", "ROLE_FAMILY_DESC"]
INTERACTIONS = [
    ("RESOURCE", "MGR_ID"),
    ("ROLE_TITLE", "ROLE_DEPTNAME"),
    ("RESOURCE", "ROLE_TITLE"),
    ("RESOURCE", "ROLE_DEPTNAME"),
    ("MGR_ID", "ROLE_TITLE"),
]
# (columna que se cuenta, agrupada por) -> nº de valores distintos de la primera dentro de cada valor de la segunda
NUNIQUE_PAIRS = [
    ("RESOURCE", "MGR_ID"),
    ("RESOURCE", "ROLE_DEPTNAME"),
    ("RESOURCE", "ROLE_TITLE"),
    ("MGR_ID", "RESOURCE"),
    ("ROLE_TITLE", "RESOURCE"),
    ("ROLE_DEPTNAME", "RESOURCE"),
]
TE_COLS = BASE_COLS  # columnas base + interacciones reciben target encoding
SMOOTH = 20.0        # suavizado bayesiano: una categoría con pocas filas se acerca a la media global


def inter_name(a: str, b: str) -> str:
    return f"{a}_x_{b}"


def _as_text(s: pd.Series) -> pd.Series:
    """Código -> texto estable (117961.0 y 117961 son el mismo código)."""
    return s.astype("Int64").astype(str) if pd.api.types.is_numeric_dtype(s) else s.astype(str)


def add_interactions(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una copia con las columnas de interacción como texto 'a|b'."""
    out = pd.DataFrame({c: _as_text(df[c]) for c in BASE_COLS}, index=df.index)
    for a, b in INTERACTIONS:
        out[inter_name(a, b)] = out[a] + "|" + out[b]
    return out


class IAMFeatureBuilder(BaseEstimator, TransformerMixin):
    """Construye las variables numéricas del modelo a partir de los códigos categóricos.

    - `freq__*`: log(1 + conteo) de cada categoría e interacción vista en entrenamiento (0 = nunca vista).
    - `nuniq__*`: agregaciones por grupo (p. ej. nº de recursos distintos pedidos por cada gerente).
    - `te__*`: target encoding suavizado. En `fit_transform` se calcula **fuera de pliegue** (out-of-fold,
      pliegues estratificados y agrupados por gerente), de modo que la fila nunca ve su propia etiqueta.
      En `transform` usa el ajuste con todo el entrenamiento.
    """

    def __init__(self, n_splits: int = 5, smooth: float = SMOOTH, seed: int = 42, group_col: str = "MGR_ID"):
        self.n_splits = n_splits
        self.smooth = smooth
        self.seed = seed
        self.group_col = group_col

    # --- piezas internas -------------------------------------------------------------
    def _te_table(self, cats: pd.DataFrame, y: np.ndarray) -> dict:
        prior = float(np.mean(y))
        tables = {}
        for c in self.te_cols_:
            g = pd.DataFrame({"k": cats[c].to_numpy(), "y": y}).groupby("k")["y"].agg(["sum", "count"])
            tables[c] = (g["sum"] + self.smooth * prior) / (g["count"] + self.smooth)
        return tables

    def _apply_te(self, cats: pd.DataFrame, tables: dict, prior: float) -> pd.DataFrame:
        return pd.DataFrame(
            {f"te__{c}": cats[c].map(tables[c]).fillna(prior).to_numpy(float) for c in self.te_cols_},
            index=cats.index,
        )

    def _deterministic(self, cats: pd.DataFrame) -> pd.DataFrame:
        """Frecuencias y agregaciones: no usan la etiqueta, solo estructura de los datos de entrenamiento."""
        out = {}
        for c in self.freq_cols_:
            out[f"freq__{c}"] = np.log1p(cats[c].map(self.counts_[c]).fillna(0).to_numpy(float))
        for (a, b), table in self.nuniq_.items():
            out[f"nuniq__{a}_por_{b}"] = cats[b].map(table).fillna(0).to_numpy(float)
        # cuánto pesa este recurso dentro de lo que suele pedir su gerente (0 si el gerente es nuevo)
        pair = self.counts_[inter_name("RESOURCE", "MGR_ID")]
        mgr = self.counts_["MGR_ID"]
        num = cats[inter_name("RESOURCE", "MGR_ID")].map(pair).fillna(0).to_numpy(float)
        den = cats["MGR_ID"].map(mgr).fillna(0).to_numpy(float)
        out["share__RESOURCE_en_MGR"] = np.divide(num, den, out=np.zeros_like(num), where=den > 0)
        return pd.DataFrame(out, index=cats.index)

    # --- API scikit-learn ------------------------------------------------------------
    def fit(self, X, y):
        self.fit_transform(X, y)
        return self

    def fit_transform(self, X, y=None, **fit_params):
        if y is None:
            raise ValueError("IAMFeatureBuilder necesita la etiqueta para el target encoding.")
        y = np.asarray(y)
        cats = add_interactions(X)
        self.freq_cols_ = list(cats.columns)
        self.te_cols_ = list(cats.columns)
        self.counts_ = {c: cats[c].value_counts() for c in self.freq_cols_}
        self.nuniq_ = {
            (a, b): cats.groupby(b)[a].nunique() for a, b in NUNIQUE_PAIRS
        }
        self.prior_ = float(y.mean())
        self.te_tables_ = self._te_table(cats, y)

        # target encoding fuera de pliegue (sin fuga): cada fila se codifica con tablas que no la incluyen
        te_oof = pd.DataFrame(index=cats.index, columns=[f"te__{c}" for c in self.te_cols_], dtype=float)
        groups = X[self.group_col].to_numpy()
        cv = StratifiedGroupKFold(self.n_splits, shuffle=True, random_state=self.seed)
        for tr, va in cv.split(cats, y, groups=groups):
            tables = self._te_table(cats.iloc[tr], y[tr])
            prior = float(y[tr].mean())
            te_oof.iloc[va] = self._apply_te(cats.iloc[va], tables, prior).to_numpy()
        out = pd.concat([self._deterministic(cats), te_oof], axis=1)
        self.feature_names_ = list(out.columns)
        return out

    def transform(self, X):
        cats = add_interactions(X)
        te = self._apply_te(cats, self.te_tables_, self.prior_)
        return pd.concat([self._deterministic(cats), te], axis=1)[self.feature_names_]

    def get_feature_names_out(self, input_features=None):
        return np.array(self.feature_names_)

    def set_output(self, *, transform=None):  # siempre devolvemos DataFrame
        return self
