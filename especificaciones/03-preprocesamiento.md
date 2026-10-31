# Especificación · Etapa 3 · Preprocesamiento (limpieza y partición) — AccessGuard AI

> Claude la implementa; el grupo revisa con `curso/kit-estudiante/checklist-revision-ia.md`.
> Código: `src/accessguard/` · Notebook: `notebooks/03_preprocesamiento.ipynb` · Informe: `reports/03_preprocesamiento.md`.

**Grupo:** AccessGuard AI   **Fecha:** 2026-10-30   **Estado:** ☐ borrador  ☑ cerrada (pendiente de revisión del grupo)

## 1. Unidad de análisis y partición

- **Una fila es:** una solicitud de acceso (empleado/rol → recurso).
- **Entidad que se repite (columna):** `MGR_ID`.
- **Se parte por:** ☑ grupo (`StratifiedGroupKFold`) ☐ fila
- **Proporción de prueba:** 20 % (reserva cerrada) y 20 % del resto para validación interna. **Semilla:** 42.
- **¿Hay orden temporal que respetar?** ☑ no (no hay fechas).
- **Dónde se guarda la prueba:** `Data/processed/holdout_clean.csv` (cerrada: **no se mira** hasta la etapa 7). `Data/test.csv` no tiene etiqueta.

## 2. Datos personales

| Columna | Qué es | Se elimina en | Prueba que lo verifica |
|---|---|---|---|
| — | No hay datos personales (solo códigos anónimos) | — | `check_schema` en el notebook 03 |

## 3. Reglas de limpieza

| # (EDA) | Columna(s) | Problema | Regla exacta | Función | Prueba |
|---|---|---|---|---|---|
| 4 | `ROLE_CODE` | Equivalente 1 a 1 con `ROLE_TITLE` (343 = 343, train y test) | Detectar el par con `find_redundant_pairs` y eliminar `ROLE_CODE` | `cleaning.drop_redundant` | `tests/test_cleaning.py` |
| 1 | las 9 | Códigos guardados como enteros | Tratar como texto categórico; con un vacío la columna pasa a float: `117961.0` → `117961` | `features._label` / `to_str` | `tests/test_features.py::test_nan_in_batch_does_not_change_other_rows` |
| 3 | `MGR_ID` | Entidad repetida | Partición por grupo, estratificada por `ACTION` | `split.split_by_group` | `tests/test_split.py` |
| 5 | `RESOURCE`, `MGR_ID`, `ROLE_FAMILY_DESC` | Alta cardinalidad; categorías nuevas en test (≈ 2–3 % de filas) | Target encoding con CV interno (5) + escalado; frecuencia `log(1+n)` + escalado; desconocido → prior / frecuencia 0 | `features.build_preprocessor` | `tests/test_features.py` |
| 5 | 5 columnas `ROLE_*` | Cardinalidad media | One-hot con `min_frequency=10`, `handle_unknown="infrequent_if_exist"` | `features.build_preprocessor` | `tests/test_features.py` |
| 7 | `ROLE_ROLLUP_1`, `ROLE_FAMILY` | Redundancia jerárquica; ablación sin pérdida | Se excluyen de las variables del modelo (provisional) | notebook 03 §5 | verificación en el notebook |

## 4. Vacíos

| Columna | Qué significa el vacío | Tratamiento hoy | Tratamiento en la etapa 4 (dentro del `Pipeline`) |
|---|---|---|---|
| todas | ☑ no se anotó (hoy hay 0) | ☑ dejar vacío | Imputador constante `"DESCONOCIDO"` (categoría explícita), nunca medias |

## 5. Entradas y salidas

| | Ruta |
|---|---|
| Entrada | `Data/train.csv`, `Data/test.csv` (nunca se modifican) |
| Salida: entrenamiento | `Data/processed/train_clean.csv` |
| Salida: prueba (cerrada) | `Data/processed/holdout_clean.csv` |
| Salida: test sin etiqueta | `Data/processed/test_clean.csv` |
| Variables elegidas | `Data/processed/selected_features.json` |
| Código | `src/accessguard/data/{cleaning,split,loading}.py`, `features.py`, `stats.py` |
| Notebook que orquesta | `notebooks/03_preprocesamiento.ipynb` |

## 6. Pruebas que deben existir

- ☑ **Partición:** ningún gerente en dos particiones y no se pierde ninguna fila (`tests/test_split.py`).
- ☑ **La prueba de partición contrasta con la partición por fila** (`test_row_split_would_leak` demuestra que por fila sí se filtran gerentes).
- ☑ Una prueba por regla de limpieza (`test_cleaning.py`, `test_features.py`).
- ☑ Datos personales: no aplica (ninguno).
- ☑ `pytest` en verde desde la raíz (11+ pruebas).

## 7. Criterios de cierre (H1)

- ☑ La limpieza corre de principio a fin desde cero (`Data/processed/` regenerable con el notebook 03).
- ☑ Unidad de análisis y forma de partir escritas.
- ☑ `pytest` en verde.
- ☑ Conjunto de prueba guardado y sin mirar.
- ☑ `Data/train.csv` y `Data/test.csv` intactos.
- ☐ Subido a GitHub (pendiente: el commit/push lo decide el estudiante).
- ☐ Revisión del código de Claude con `checklist-revision-ia.md`; cada integrante explica una función.
- **Hallazgo que no esperábamos:** al probar entradas con vacíos, un `NaN` volvía float toda la columna y **todos** los códigos pasaban a "no vistos" (bug corregido y con prueba). Y partir por fila infla el PR-AUC(denegar) de 0,16 a 0,42.
