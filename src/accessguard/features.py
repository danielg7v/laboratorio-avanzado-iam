"""Preprocesamiento de variables, todo dentro de un Pipeline ajustado solo con entrenamiento."""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler, TargetEncoder

LOW_CARD = ["ROLE_ROLLUP_1", "ROLE_ROLLUP_2", "ROLE_DEPTNAME", "ROLE_TITLE", "ROLE_FAMILY"]
HIGH_CARD = ["RESOURCE", "MGR_ID", "ROLE_FAMILY_DESC"]


def _label(v):
    """Código -> texto estable. Un NaN en una columna convierte los enteros en float (117961 -> 117961.0);
    aquí se revierte para que el mismo código se llame igual con o sin vacíos en el lote."""
    if pd.isna(v):
        return np.nan
    if isinstance(v, (float, np.floating)) and float(v).is_integer():
        return str(int(v))
    return str(v)


class FrequencyEncoder(BaseEstimator, TransformerMixin):
    """Cuenta cuántas veces apareció cada categoría en entrenamiento y devuelve log(1 + conteo).

    Una categoría nunca vista vale 0: "no hay historial de esta categoría".
    """

    def fit(self, X, y=None):
        X = pd.DataFrame(X)
        self.columns_ = list(X.columns)
        self.counts_ = {c: X[c].map(_label).value_counts() for c in self.columns_}
        return self

    def transform(self, X):
        X = pd.DataFrame(X, columns=self.columns_)
        out = {c: X[c].map(_label).map(self.counts_[c]).fillna(0).to_numpy(float) for c in self.columns_}
        return np.log1p(pd.DataFrame(out).to_numpy())

    def get_feature_names_out(self, input_features=None):
        return np.array([f"{c}__logfreq" for c in self.columns_])


def to_str(X):
    """Los identificadores son etiquetas, no cantidades: se tratan siempre como texto.

    Los vacíos se dejan como np.nan para que el imputador los reconozca.
    """
    return pd.DataFrame(X).astype(object).map(_label).to_numpy(dtype=object)


def build_preprocessor(low_card=None, high_card=None, seed: int = 42, use_freq: bool = True) -> ColumnTransformer:
    """Construye el preprocesador: imputación -> codificación -> escalado de lo numérico."""
    low_card = LOW_CARD if low_card is None else low_card
    high_card = HIGH_CARD if high_card is None else high_card

    def as_str():
        return FunctionTransformer(to_str, feature_names_out="one-to-one")

    def impute():  # hoy hay 0 vacíos; protege la inferencia en producción
        return SimpleImputer(strategy="constant", fill_value="DESCONOCIDO")

    blocks = []
    if low_card:
        blocks.append(("onehot", Pipeline([
            ("str", as_str()), ("impute", impute()),
            ("ohe", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=10)),
        ]), low_card))
    if high_card:
        blocks.append(("target", Pipeline([
            ("str", as_str()), ("impute", impute()),
            ("te", TargetEncoder(target_type="binary", cv=KFold(5, shuffle=True, random_state=seed))),
            ("scale", StandardScaler()),
        ]), high_card))
        if use_freq:
            blocks.append(("freq", Pipeline([
                ("freq", FrequencyEncoder()), ("scale", StandardScaler()),
            ]), high_card))
    return ColumnTransformer(blocks, remainder="drop", verbose_feature_names_out=True)
