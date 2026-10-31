# Contrato de etapas — ejemplo de referencia y hitos del grupo

Cada etapa consume los artefactos de la anterior y deja los suyos. Una etapa está **terminada**
solo si su comando de verificación corre sin errores desde un entorno limpio (D13).

| # | Etapa | Entra | Sale | Notebook | Hito | Clase |
|---|---|---|---|---|---|---|
| 1 | Caso de negocio | pregunta, dataset candidato | ficha de caso (`reports/00_caso.md`) | 01_caso_negocio | H1 | 1–2 |
| 2 | EDA | CSV crudo | hallazgos y decisiones (`reports/01_eda.md`), lista de problemas de datos | 02_eda | H1 | 2 |
| 3 | Preprocesamiento | CSV crudo + decisiones del EDA | `src/.../data` (limpieza, partición por grupo), `data/processed/` | 03_preprocesamiento | H1 | 2 |
| 4 | Feature engineering | datos limpios | `src/.../features`, tabla de variables y justificación | 04_features | H2 | 3 |
| 5 | Torneo de modelos | pipeline completo | tabla comparativa con CV por grupo (`reports/05_torneo.md`) | 05_torneo | H2 | 3 |
| 6 | Optimización con tracking | 1–2 finalistas | hiperparámetros elegidos y evidencia de mejora honesta; cada trial registrado en MLflow | 06_optimizacion | H2 | 3 |
| 7 | Validación e interpretación | modelo optimizado | métricas en prueba cerrada, calibración, SHAP, análisis de errores | 07_validacion_interpretacion | H2 | 4 |
| 8 | Registro del modelo | ejecuciones de la etapa 6 | modelo final registrado con versión y alias en Databricks | 08_registro_modelo | H2 | 4 |
| 9 | Módulos y pruebas | notebooks | `src/` completo + `pytest` verde; notebooks solo orquestan | — | H2 | 4 |
| 10 | Inferencia | modelo registrado | `models/model.joblib` + ficha de modelo + función `predict` | 09_inferencia | H2/H3 | 4–5 |
| 11 | App | función `predict` | `app/streamlit_app.py` local y luego desplegada | — | H3 | 4–5 |
| 12 | Informe técnico | secciones de cada hito | `reports/informe_tecnico.md` | — | H4 | 6 + hasta el 15 nov |
| 13 | Presentación | informe + app | `presentacion/ejecutiva.md` (≤ 5 diapositivas) | — | H3 | 5 |

## Criterios de aceptación por hito

- **H1 (cierre de la clase 2, viernes 30 de octubre)**: ficha aprobada; EDA con ≥ 5 decisiones justificadas; partición por la
  unidad correcta documentada; limpieza reproducible por script.
- **H2 (cierre de la clase 4, jueves 5 de noviembre)**: ≥ 3 modelos comparados con la misma validación; ≥ 1 experimento por
  candidato registrado; modelo final registrado con versión; `src/` con pruebas; app local que
  carga el modelo.
- **H3 (clase 5, viernes 6 de noviembre)**: app accesible por enlace público; presentación ≤ 5 diapositivas;
  ensayo de 10 minutos cronometrado.
- **H4 (domingo 15 de noviembre, 8 días tras la última clase)**: informe técnico completo con todas las secciones.

## Reglas transversales

- Ninguna etapa usa el conjunto de prueba para decidir; se abre una vez, en la etapa 7.
- Cada decisión de datos queda escrita con su motivo (no solo el código).
- Los cambios de datos y de unidad de análisis se documentan en el informe.
