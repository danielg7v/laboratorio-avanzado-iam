# Evaluación final en la reserva (holdout) — política de 3 estados

- Modelo: **Random Forest** · reserva: 6,554 solicitudes de 883 gerentes que el entrenamiento nunca vio.
- Evaluada **una sola vez** el 2026-10-31T11:34:10. Umbrales fijados antes en validación cruzada: T_low = 0.148, T_high = 0.983.
- Costos supuestos (USD, **no medidos**): FP = 500 · FN = 30 · revisión = 6.
- ROC-AUC = 0.713 · PR-AUC de denegar = 0.189 (azar = 0.058).
- Reparto: aprobar 3.4% · revisar 96.6% · denegar 0.0%; 3 accesos indebidos aprobados y 0 legítimos denegados automáticamente.
- Ahorro frente a la mejor política trivial (**revisar todo**): -0.027 USD por solicitud (-0.5 %); IC 95 % por gerentes [-0.290, 0.183].

| Política | Costo por solicitud (USD) | Ahorro vs mejor trivial (USD) | Ahorro (%) |
|---|---|---|---|
| aprobar todo | 28.914 | -22.914 | -381.9 |
| denegar todo | 28.265 | -22.265 | -371.1 |
| revisar todo | 6.000 | 0.000 | 0.0 |
| modelo, 2 estados (umbral 0.895) | 19.698 | -13.698 | -228.3 |
| modelo, 3 estados (0.148/0.983) | 6.027 | -0.027 | -0.5 |

**Conclusión:** el intervalo incluye 0: con estos costos NO se puede afirmar que el modelo mejore a la mejor política trivial.