# Evaluación en la reserva (holdout) — política Zero Trust de auto-aprobación

- Modelo: **LogReg ElasticNet** · reserva: 6,554 solicitudes de 883 gerentes que el entrenamiento nunca vio (379 indebidas, 5.8%).
- Evaluada el 2026-11-03T18:08:29. **Nota:** la reserva ya se había abierto una vez con el enfoque monetario anterior.
- Ranking: ROC-AUC = 0.701 · PR-AUC de denegar = 0.199 (azar = 0.058).

| Política | % auto-aprobado | Accesos indebidos concedidos | FPR (real ≤ 95 %) | % a revisión humana |
|---|---|---|---|---|
| Revisar todo (referencia) | 0,00 % | 0 | 0 % | 100 % |
| Aprobar todo (referencia) | 100 % | 379 | 100 % | 0 % |
| **Estricto** (T_auto = 0.9809, fijado en validación cruzada) | 5.20% | 2 | 0.53% (≤ 1.65%) | 94.8% |
| Práctico (p ≥ 0.98) | 5.72% | 3.0 | 0.79% (≤ 2.03%) | 94.3% |

- Cola de revisión: 6,213 solicitudes; lift = 1.05. Denegaciones encontradas revisando solo el primer 10 % de la cola: 30.6%; el primer 20 %: 41.7% (al azar: 10 % y 20 %).

**Conclusión:** el umbral estricto NO se sostuvo (2 accesos indebidos auto-aprobados en la reserva). El FPR = 0 % de la validación cruzada no se generalizó; hace falta un margen de seguridad más amplio (umbral más alto) o un control adicional antes de auto-aprobar.