# AccessGuard AI — Gobernanza y control de accesos IAM

**Problema:** decidir (aprobar / denegar / escalar) solicitudes de acceso a recursos corporativos con el dataset *Amazon Employee Access Challenge*, sin conceder accesos indebidos (FP, el error caro) ni bloquear a usuarios legítimos (FN).

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
- Los **costos en USD** (`config/settings.py`) son **supuestos**; el dataset no los trae.
- Solo 32.769 filas con etiqueta y todas las variables categóricas: puede no cumplir `curso/evaluacion/criterios-dataset.md`; consultar al instructor.
- `Data/test.csv` no tiene `ACTION`; no sirve para medir desempeño.
