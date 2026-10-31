# Informe de preprocesamiento — AccessGuard AI

Resultado de `notebooks/03_preprocesamiento.ipynb` (30-oct-2026). Particiones: entrenamiento 80 % / reserva cerrada 20 % por gerente (`MGR_ID`), estratificadas; selección de variables por ablación con CV de 5 pliegues por gerente.

**Cifras clave:** partición por fila → ROC-AUC 0,82 / PR-AUC(denegar) 0,42 (1.866 gerentes compartidos); por gerente → 0,71 / 0,16. Con las variables seleccionadas el ROC-AUC de CV es 0,702 (igual que con todas). Son diagnósticos del preprocesamiento con una regresión logística simple, **no el modelo final**.

## Decisiones de preprocesamiento

| # | Decisión | Evidencia | Código / prueba |
|---|---|---|---|
| 1 | Eliminar `ROLE_CODE` | Equivalente uno a uno con `ROLE_TITLE` (343 = 343) en train y test | `drop_redundant` · `tests/test_cleaning.py` |
| 2 | Partir por `MGR_ID`, estratificado por `ACTION`; reserva cerrada del 20 % | Partir por fila comparte 1.866 gerentes y sube el PR-AUC(denegar) de 0,16 a 0,42 | `split_by_group` · `tests/test_split.py` |
| 3 | Tratar todos los códigos como categóricos (texto); revertir `117961.0` → `117961` cuando un vacío vuelve float la columna | Se encontró un bug real al probar entradas con vacíos: todos los códigos pasaban a "no vistos" | `features._label` · `tests/test_features.py` |
| 4 | Imputador de seguridad (`DESCONOCIDO`); sin imputar medias | 0 vacíos hoy; la producción puede traerlos | `build_preprocessor` · `tests/test_features.py` |
| 5 | One-hot (`min_frequency=10`) para 5 columnas; target encoding con CV interno + escalado para 3 columnas de alta cardinalidad | 735 columnas one-hot vs. miles; categorías nuevas → "infrecuente"/prior | `build_preprocessor` |
| 6 | Variables de frecuencia `log(1+conteo)` escaladas | Quitarlas baja el ROC-AUC ≈ 0,009 | `FrequencyEncoder` · `tests/test_features.py` |
| 7 | Selección: se descartan `ROLE_ROLLUP_1` y `ROLE_FAMILY`; `MGR_ID` queda como caso límite | Ablación con CV por gerente (5 pliegues), tolerancia 0,002 | Este notebook, §5 |
| 8 | `test.csv` solo para predecir (sin etiqueta) | No tiene `ACTION` | — |

Salidas en `Data/processed/`: `train_clean.csv`, `holdout_clean.csv` (cerrada), `test_clean.csv`, `selected_features.json`.
