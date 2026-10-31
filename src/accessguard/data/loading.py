"""Carga de datos. El dataset no trae datos personales: solo identificadores numéricos anónimos."""
from pathlib import Path

import pandas as pd


def load_split_file(path: Path | str) -> pd.DataFrame:
    """Lee un CSV del dataset y lo devuelve tal cual (los datos originales nunca se modifican)."""
    return pd.read_csv(path)
