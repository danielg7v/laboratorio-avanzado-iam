# AccessGuard AI — Gobernanza y control de accesos IAM

**Problema:** gobierno de accesos (IGA) bajo **Zero Trust y Menor Privilegio**: **auto-aprobar con seguridad** las solicitudes rutinarias —sin conceder accesos indebidos— y escalar a un analista IAM lo ambiguo (*human-in-the-loop*), con el dataset *Amazon Employee Access Challenge*.

**Éxito del proyecto (sin costos en USD):** (1) Tasa de Auto-Aprobación Segura @ FPR = 0 % / confianza ≥ 98 %; (2) reducción de fricción y SLA (de días a milisegundos; el SLA manual real debe medirse); (3) triaje asistido para prevenir la fatiga de aprobación.

## Estado (hito H1 · clase 2, 30-oct-2026)
| Entregable | Ubicación |
|---|---|
| Caso de negocio (variable respuesta, matriz FP/FN, líneas base, métrica) | `notebooks/01_caso_de_negocio.ipynb` · `reports/00_caso.md` |
| EDA (calidad, cardinalidad, jerarquía de roles, V de Cramér, deriva train→test, 9 decisiones) | `notebooks/02_eda.ipynb` · `reports/01_eda.md` |
| Preprocesamiento (limpieza, partición por gerente, imputación, codificación, escalado, selección) | `notebooks/03_preprocesamiento.ipynb` · `reports/03_preprocesamiento.md` |
| Especificaciones por etapa | `especificaciones/02-eda.md`, `03-preprocesamiento.md`, `especificacion-proyecto.md` |
| Código reutilizable y pruebas | `src/accessguard/`, `tests/` (11 pruebas) |

## Estructura
`Data/` (train.csv, test.csv originales; `processed/` se regenera) · `config/settings.py` · `notebooks/` · `src/accessguard/` · `tests/` · `app/` · `models/` · `reports/` · `especificaciones/` · `.specify/` y `.claude/` (Spec Kit y subagentes) · `curso/` (guías) · `specs/contratos-curso/`.

## Cómo reproducirlo
```bash
pip install -r requirements.txt          # Python 3.12
python -m pytest -q
# ejecutar los notebooks en orden 01 → 02 → 03 (03 genera Data/processed/)
```

## Advertencias
- El proyecto se **reorientó** (2026-10-31) de un enfoque de costo monetario a un marco de seguridad. Las constantes `COST_*` de `config/settings.py` son **legado**: solo las usa `notebooks/06_optimizacion_optuna.ipynb`, **pendiente de reorientar** (sus resultados en `reports/06_*` son del enfoque anterior).
- Resultado actual (notebook 05): la auto-aprobación segura (FPR = 0 %) es de ≈ 1 – 2 % de las solicitudes; la mayoría debe ir a revisión humana.
- Solo 32.769 filas con etiqueta y todas las variables categóricas: puede no cumplir `curso/evaluacion/criterios-dataset.md`; consultar al instructor.
- `Data/test.csv` no tiene `ACTION`; no sirve para medir desempeño.
