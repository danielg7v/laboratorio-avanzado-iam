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

# --- Marco de éxito: Ciberseguridad / IGA / Zero Trust (reorientación del proyecto) -----------------------
# El éxito NO se mide en dólares (el dataset no trae costos), sino con métricas de seguridad operativas:
#  1. Tasa de Auto-Aprobación Segura: % de solicitudes rutinarias auto-aprobadas SIN conceder accesos indebidos
#     (0 falsos positivos, FPR = 0 %) y, en la variante práctica, con confianza >= AUTO_APPROVE_CONFIDENCE.
#  2. Reducción de fricción / SLA: latencia de decisión de los accesos legítimos (se mide en ms con el modelo;
#     el tiempo de espera manual actual NO está en los datos: hay que medirlo con los tickets del área IAM).
#  3. Triaje asistido (human-in-the-loop): lo ambiguo o anómalo va a un analista IAM; se mide la carga de
#     revisión y qué tan "rica" en denegaciones es esa cola (lift) para evitar la fatiga de aprobación.
TARGET_FPR = 0.0                  # meta de falsos positivos para la auto-aprobación estricta
AUTO_APPROVE_CONFIDENCE = 0.98    # p(aprobar) mínima para auto-aprobar en la variante práctica
CONFIDENCE_BANDS = (0.90, 0.95, 0.98, 0.99)   # zonas de alta confianza que se reportan en el torneo
SECURITY_PRINCIPLES = ("Menor privilegio (Least Privilege)", "Zero Trust: nunca confiar, siempre verificar",
                       "Prevención de movimiento lateral", "Trazabilidad para auditoría y cumplimiento")

# --- LEGADO (política monetaria anterior) -------------------------------------------------------------
# Valores de trabajo de la fase anterior (USD, SUPUESTOS no medidos). Ya NO definen el éxito del proyecto;
# se conservan solo como referencia histórica (el notebook 06 reorientado ya no los importa).
COST_FN = 30.0
COST_FP = 500.0
COST_REVIEW = 6.0
