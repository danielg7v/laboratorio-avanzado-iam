# AccessGuard AI — Gobernanza y Control de Accesos IAM

Instrucciones permanentes para Claude. Se leen al inicio de cada conversación. Reglas completas del curso: `curso/kit-estudiante/` (plantilla original) y `.specify/memory/constitution.md`.

## Contexto
Predicción y automatización de solicitudes de acceso a recursos corporativos con el dataset **Amazon Employee Access Challenge**, bajo un marco de **Ciberseguridad / IGA / Zero Trust** (Menor Privilegio; ante la duda, escalar a un analista IAM).
Soy estudiante de la Maestría en Ingeniería Analítica (analista, no desarrollador): explica lo que haces con palabras simples antes y después de cambiar código.

- **Una fila = una solicitud de acceso** (empleado/rol → recurso). **Objetivo:** `ACTION` (1 = aprobado, 0 = denegado; 94,2 % / 5,8 %).
- **Clase positiva = aprobar.** FP = concesión indebida (el error caro); FN = bloqueo a un usuario legítimo.
- **Entidad que se repite: `MGR_ID`** → toda partición y validación cruzada es **por gerente** (`StratifiedGroupKFold`), nunca por fila.
- Las 9 variables son **códigos categóricos anónimos** guardados como enteros: no son cantidades, no se escalan como números.
- `Data/test.csv` **no tiene etiqueta**: no sirve para medir. La reserva cerrada sale de `train.csv` (`Data/processed/holdout_clean.csv`).
- **El éxito NO se mide en dólares** (el dataset no trae costos): se mide con Auto-Aprobación Segura (FPR = 0 % / confianza ≥ 98 %), reducción de fricción/SLA y triaje asistido (`src/accessguard/security_metrics.py`). Las constantes `COST_*` de `config/settings.py` son legado (ya nada las usa). El notebook 06 ya fue ejecutado bajo el marco Zero Trust (2026-11-03): reportes `reports/06_zt_*` y modelo exportado en `models/model.joblib`. Resultado clave: el umbral estricto (FPR = 0 % en validación cruzada) dejó pasar 2 accesos indebidos en la reserva, y la optimización con Optuna no se distingue del ruido frente al modelo por defecto. La reserva ya se abrió dos veces (enfoque monetario y Zero Trust): no volver a usarla para decidir. Los resultados monetarios antiguos están en `reports/legacy_costos/`.
- Léeme antes de generar código: `especificacion-proyecto.md`, `especificaciones/` (una por etapa) y la constitución.

## Pila tecnológica
Python 3.12 · pandas · scikit-learn · XGBoost / LightGBM · MLflow / Databricks · Streamlit · Git / GitHub.

## Estructura
```text
CLAUDE.md  README.md  especificacion-proyecto.md  especificaciones/  requirements.txt  .env.example  .gitignore
.specify/ .claude/   # Spec Kit (constitución, plantillas) y subagentes (agents/)
specs/               # lo que genera Spec Kit + contratos del curso (contratos-curso/)
curso/               # guías del curso (guias/, kit-estudiante/)
Data/                # train.csv y test.csv originales (NO se modifican); raw/ y processed/ (regenerable)
config/settings.py   # rutas, columnas, semilla y supuestos de costo
notebooks/           # 01_caso_de_negocio, 02_eda, 03_preprocesamiento: solo orquestan
src/accessguard/     # data/ (cleaning, split, loading), features.py, stats.py
tests/               # pytest
models/  app/  reports/  presentacion/  scripts/
```
- La lógica reutilizable va en `src/`; los notebooks importan de `src/`, nunca al revés.

## Estilo
- Textos, comentarios y documentación en **español**; nombres de variables, funciones y archivos de código en **inglés**.
- Cambios pequeños, una cosa por vez. Si no estás seguro, pregunta antes de inventar.

## Reglas que no se negocian
1. **No inventes datos ni métricas.** Si algo no existe, dilo.
2. **No subas secretos** (`.env`). Este dataset no trae datos personales; si aparecieran, se eliminan al cargar.
3. **Partición por gerente** (`MGR_ID`) y estratificada por `ACTION`; hay una prueba (`tests/test_split.py`) que lo verifica.
4. **No uses la reserva ni `test.csv` para decidir nada.** Se abre una sola vez, en la etapa de validación.
5. **Todo lo que aprende de los datos va dentro de un `Pipeline`** ajustado solo con entrenamiento (target encoding, frecuencias, escalado).
6. **Cada decisión de datos se escribe con su motivo** en `reports/` y tiene función en `src/` y prueba en `tests/`.
7. Métrica principal: **Tasa de Auto-Aprobación Segura** (con su cota de FPR al 95 %); reporta también ROC-AUC y PR-AUC de la clase *denegar* y la precisión en zonas de alta confianza. **Nunca accuracy sola.**
8. MLflow en Databricks para experimentos (conexión desde `.env`; `PYTHONUTF8=1` en Windows). La app **no** consulta Databricks: carga `models/model.joblib`.
9. Ejecuta `pytest` antes de dar un cambio por terminado.

## Cómo ejecutar
```bash
# Entorno (en este equipo ya existe ../venv-iam)
python -m pytest -q
python -m nbconvert --to notebook --execute --inplace notebooks/01_caso_de_negocio.ipynb   # idem 02 y 03
```

## Cómo quiero que respondas
1. Resume en 2–3 frases qué vas a hacer y por qué. 2. Haz el cambio. 3. Dime el comando exacto para comprobarlo y qué debería ver.
4. Avisa de riesgos (fuga de información, métrica engañosa, supuestos de costo).
