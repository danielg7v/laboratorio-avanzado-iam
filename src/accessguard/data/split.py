"""Partición por grupo: ningún gerente (MGR_ID) aparece en entrenamiento y en reserva a la vez."""
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold


def split_by_group(
    df: pd.DataFrame, group_col: str, target_col: str, test_size: float = 0.2, seed: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Parte `df` en (entrenamiento, reserva) por grupo y estratificando por el objetivo.

    Usa un `StratifiedGroupKFold` con 1/test_size pliegues y toma el primero como reserva.
    Conserva el índice original, así que se puede comprobar que no se pierde ninguna fila.
    """
    n_splits = round(1 / test_size)
    cv = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    train_idx, test_idx = next(cv.split(df, df[target_col], groups=df[group_col]))
    return df.iloc[train_idx], df.iloc[test_idx]
