"""Configuración central de AccessGuard AI (rutas, columnas y supuestos de costo).

Todo lo que un notebook o un módulo de `src/` necesita saber del caso vive aquí,
para no repetir "números mágicos" en varios sitios.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = ROOT / "reports"

# Los CSV originales se conservan en Data/ (el docente los entrega ahí).
TRAIN_PATH = DATA_DIR / "train.csv"
TEST_PATH = DATA_DIR / "test.csv"

SEED = 42
TARGET = "ACTION"            # 1 = acceso aprobado, 0 = acceso denegado
GROUP_COL = "MGR_ID"         # entidad que se repite -> la partición se hace por este grupo
TEST_ID_COL = "id"           # identificador de fila solo presente en test.csv
FEATURES = [
    "RESOURCE", "MGR_ID", "ROLE_ROLLUP_1", "ROLE_ROLLUP_2", "ROLE_DEPTNAME",
    "ROLE_TITLE", "ROLE_FAMILY_DESC", "ROLE_FAMILY", "ROLE_CODE",
]
HOLDOUT_FRACTION = 0.20

# --- Supuestos de costo (USD por decisión). SON HIPÓTESIS DE TRABAJO, no datos medidos. ---
# El dataset no trae costos: hay que validarlos con Seguridad / Riesgos / Mesa de ayuda.
# Por eso el notebook 01 incluye un análisis de sensibilidad sobre la razón C_FP / C_FN.
COST_FN = 40.0      # Falso Negativo: se bloquea a un usuario legítimo (ticket + horas perdidas)
COST_FP = 2000.0    # Falso Positivo: se concede un acceso indebido (exposición esperada)
COST_REVIEW = 6.0   # Revisión manual de una solicitud por un analista (~15 min)
