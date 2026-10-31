# Informe del EDA — AccessGuard AI

Resultado de `notebooks/02_eda.ipynb` (30-oct-2026). Cada hallazgo termina en una decisión; cada decisión tiene función en `src/accessguard/` y prueba en `tests/`.

## Qué son los datos

- `train.csv`: 32.769 solicitudes × 10 columnas; `test.csv`: 58.921 × 10 (sin `ACTION`, con `id`).
- Una fila = una **solicitud de acceso**. Las 9 variables son **códigos categóricos anónimos** (enteros). 0 vacíos, 0 duplicados, sin datos personales.
- Objetivo `ACTION`: 94,21 % aprobadas / 5,79 % denegadas (≈ 16:1).
- Entidades repetidas: 4.243 gerentes (≈ 7,7 solicitudes c/u) y 7.518 recursos.
- Deriva `train→test` (PSI): `MGR_ID` ≈ 0,28, `ROLE_FAMILY_DESC` ≈ 0,18, `RESOURCE` ≈ 0,09.

## Decisiones: hallazgo → decisión → motivo

| # | Hallazgo (con cifra) | Decisión | Motivo | Se implementa en |
|---|---|---|---|---|
| 1 | 9 columnas de entrada son enteros que **identifican categorías**; 0 vacíos y 0 duplicados en train y test | Tratar todas como **categóricas** (texto), no escalarlas como cantidades; mantener un imputador de seguridad | El tamaño de un código no significa nada; en producción pueden llegar vacíos | `features.to_str`, `build_preprocessor` |
| 2 | `ACTION`: 94,2 % aprobadas / 5,8 % denegadas (≈ 16:1) | Métrica principal = **costo esperado**; reportar ROC-AUC y PR-AUC de *denegar*; **estratificar** las particiones | Accuracy trivial = 94,2 %; la clase rara es la costosa | `split_by_group` (estratificado) |
| 3 | `MGR_ID`: 4.243 gerentes para 32.769 filas (≈ 7,7 solicitudes por gerente, máx. 152); `RESOURCE` igual | Partir train/validación **por `MGR_ID`** (`StratifiedGroupKFold`), reserva cerrada | Evitar fuga: un gerente decide de forma correlacionada | `split_by_group` + `test_split.py` |
| 4 | `ROLE_TITLE` ↔ `ROLE_CODE`: correspondencia 1 a 1 (343 = 343) en train y test | **Eliminar `ROLE_CODE`** | Información duplicada; no aporta y complica la interpretación | `drop_redundant` + `test_cleaning.py` |
| 5 | Alta cardinalidad: `RESOURCE` 7.518, `MGR_ID` 4.243, `ROLE_FAMILY_DESC` 2.358 categorías; en test hay 670 gerentes y 593 familias-desc. nuevos (≈ 2,8 % y 2,1 % de las filas) | **No usar one-hot** en esas 3: *target encoding* con validación cruzada + frecuencia; las de baja cardinalidad con one-hot agrupando categorías raras (`min_frequency`) | One-hot crearía >14.000 columnas casi vacías; lo desconocido debe tener un valor por defecto sensato | `build_preprocessor` + `test_features.py` |
| 6 | La tasa de denegación baja de 7,1 % (recurso con 1 solicitud) a 4,5 % (>100); en gerentes la relación no es monótona | Agregar **variables de frecuencia** (`log(1+conteo)` en train) y **escalarlas**, como hipótesis a confirmar con ablación | Los conteos son numéricos y sesgados; la novedad del recurso es una señal modesta | `FrequencyEncoder` |
| 7 | V de Cramér ≈ 1,00 entre `ROLE_TITLE`/`ROLE_CODE`/`ROLE_FAMILY`, 0,96 entre `ROLLUP_1`/`ROLLUP_2` y 0,80 con `ROLE_FAMILY_DESC` (jerarquía de roles) | Verificar con ablación en `03` qué columnas del bloque de roles aportan; no eliminar a ciegas | V se infla con alta cardinalidad; el criterio es el desempeño en validación | `03_preprocesamiento` §5 |
| 8 | PSI train→test: `MGR_ID` 0,28; `ROLE_FAMILY_DESC` 0,18; `test.csv` no tiene `ACTION` | **No usarlo para medir**: solo para generar predicciones; la reserva cerrada sale de `train.csv`; validar de forma conservadora y con tolerancia a categorías nuevas | Sin etiqueta no hay métrica, y hay deriva en las columnas de alta cardinalidad | `03_preprocesamiento` |
| 9 | `RESOURCE = 0` aparece en 13 filas de train y 25 de test | Conservarlo como categoría y preguntar al dueño del dato si es un código real o un valor por defecto | No hay evidencia para tratarlo como error |
