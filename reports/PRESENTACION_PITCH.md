# AccessGuard AI — Pitch ejecutivo (5 diapositivas)

> Estructura de la presentación. Cada diapositiva: título, mensaje clave, contenido, apoyo visual y guion breve. Cifras de `reports/REPORTE_TECNICO_FINAL.md`.

---

## Diapositiva 1 — El problema: aprobar accesos sin abrir la puerta equivocada

**Mensaje clave:** El equipo IAM revisa cada solicitud a mano; un acceso indebido concedido es el error caro.

- Una solicitud = un empleado/rol pidiendo un recurso. 94 % se aprueban, 6 % se deniegan.
- Error caro: conceder un acceso indebido (viola Menor Privilegio, abre movimiento lateral, hallazgo de auditoría).
- Error barato: demorar un acceso legítimo (visible y reversible).
- Meta: auto-aprobar solo lo rutinario y escalar a una persona lo dudoso (Zero Trust: nunca confiar, siempre verificar).

**Visual:** barra 94 % / 6 % y las dos columnas de error (caro / barato).
**Guion (20 s):** "Hoy todo pasa por una persona. Queremos liberar lo obvio sin conceder nunca lo que no corresponde."

---

## Diapositiva 2 — La solución: tres zonas y una persona siempre al mando

**Mensaje clave:** El modelo no decide; ordena y clasifica en verde, amarillo y rojo.

| Zona | Qué ocurre |
|---|---|
| 🟢 Verde | Auto-aprobación estricta, con registro de auditoría |
| 🟡 Amarilla | Cola de triaje, de más a menos sospechosa |
| 🔴 Roja | Revisión manual a fondo |

- **Nunca se deniega automáticamente.**
- Los umbrales se fijan con validación cruzada por gerente, no con la reserva.

**Visual:** semáforo con el flujo de cada zona.
**Guion (30 s):** "Tres carriles. El sistema solo acelera el verde; el resto lo ve un analista, priorizado."

---

## Diapositiva 3 — Resultados: honestos, con su margen de error

**Mensaje clave:** El valor está en los extremos y en ordenar la cola, no en automatizar mucho.

- Evaluado en 883 gerentes que el modelo nunca vio (6.554 solicitudes).
- **Zona verde:** 5,20 % de las solicitudes; 2 accesos indebidos de 341 (la tasa real podría llegar a 1,65 %).
- **Zona roja:** 10 % de las solicitudes con 3 veces más denegaciones que el promedio (17 % frente a 5,8 %).
- **Cola ordenada:** revisando el 10 % más sospechoso se halla el 30,61 % de las denegaciones (azar: 10 %).
- ROC-AUC 0,7009. Si se hubiera partido por fila habría parecido 0,82: una ilusión que evitamos.

**Visual:** tabla de zonas y curva de captura frente al azar.
**Guion (45 s):** "Somos transparentes: automatiza poco, pero prioriza bien, y no prometemos cero errores."

---

## Diapositiva 4 — Confianza: por qué decide lo que decide (SHAP)

**Mensaje clave:** Cada decisión se explica; el modelo se apoya en qué tan habitual es la combinación solicitada.

- 74 % del impacto viene de la frecuencia histórica de combinaciones: recurso × gerente, recurso × departamento, gerente × cargo.
- La app muestra, para cada solicitud, qué factores empujan hacia aprobar y cuáles hacia revisar.
- Riesgo a vigilar: una necesidad legítima pero inusual recibirá más revisión (más fricción).
- Probabilidades no calibradas: se leen como ranking, no como "98 % de certeza".

**Visual:** `reports/figures/shap_summary.png` y una explicación local de la app.
**Guion (30 s):** "No es una caja negra: cada caso trae su explicación para el auditor."

---

## Diapositiva 5 — Despliegue y siguientes pasos

**Mensaje clave:** Listo para un piloto controlado, con tres datos que faltan para escalar.

- **Arquitectura:** entrenamiento → `model.joblib` → registro en MLflow/Databricks (`AccessGuard_ZeroTrust_Model`, alias `champion`) → app Streamlit sin credenciales.
- **Piloto propuesto:** solo zona verde y roja en modo sombra, comparando con la decisión humana.
- **Falta medir:** tiempos reales de espera (SLA), criticidad de cada recurso (umbrales por recurso) y deriva con gerentes nuevos.
- **Salvaguarda:** si aparece un acceso indebido en la zona verde, se vuelve a revisión humana total.

**Visual:** diagrama de arquitectura de cuatro cajas y una línea de tiempo del piloto.
**Guion (30 s):** "Pedimos autorización para un piloto en modo sombra y acceso a los datos de tickets para medir el beneficio real."
