# AccessGuard AI — Reporte técnico final

Memoria técnica del proyecto de gobierno de accesos (IAM) bajo el marco Zero Trust / IGA. Todas las cifras provienen de los reportes y notebooks del repositorio (`reports/`, notebooks 01–09); no se ha inventado ninguna. Donde un dato no existe, se dice.

## 1. Resumen ejecutivo

- **Problema.** El equipo IAM decide si aprueba o deniega solicitudes de acceso a recursos corporativos. Se busca **auto-aprobar con seguridad lo rutinario** y canalizar a un analista lo ambiguo o sospechoso.
- **Solución.** Un modelo que estima la probabilidad de aprobar y asigna cada solicitud a una de tres zonas: **verde** (auto-aprobación estricta), **amarilla** (cola de triaje priorizada) y **roja** (revisión manual). El sistema **nunca deniega por sí solo**.
- **Resultado honesto.** La señal del dataset es moderada (ROC-AUC ≈ 0,70 en gerentes no vistos). El modelo auto-aprueba una fracción pequeña (≈ 5 % en la reserva) y su zona roja concentra unas 3 veces más denegaciones que el promedio. El umbral estricto que en validación cruzada tenía cero accesos indebidos dejó pasar **2 de 341** en la reserva: la cifra "0 errores" no es una garantía.
- **Valor real.** Ordenar la cola: revisando solo el 10 % más sospechoso de lo no auto-aprobado se encuentra el 31 % de las denegaciones (el azar daría 10 %).

## 2. Caso de negocio

**Pregunta.** ¿Qué solicitudes de acceso pueden aprobarse automáticamente sin violar el principio de Menor Privilegio, y cuáles requieren a una persona?

**Unidad y objetivo.** Cada fila es una solicitud (empleado/rol hacia un recurso). El objetivo es aprobada (94,2 %) o denegada (5,8 %). La clase positiva es *aprobar*.

**Asimetría del error.** Un falso positivo (conceder un acceso indebido) viola Menor Privilegio, habilita movimiento lateral, es hallazgo de auditoría y es difícil de detectar. Un falso negativo (demorar un acceso legítimo) afecta la productividad, pero es visible y reversible. Por eso la métrica principal es la **Tasa de Auto-Aprobación Segura**, acompañada de su cota superior de tasa de falsos positivos al 95 %.

**Qué no se mide.** El conjunto de datos no trae costos, por lo que el éxito no se expresa en dólares (el enfoque monetario anterior se archivó en `reports/legacy_costos/`). Tampoco trae tiempos de espera reales ni la criticidad de cada recurso: ambos deben medirse con los tickets y el inventario del área IAM antes de cuantificar la reducción de fricción.

## 3. Exploración y preprocesamiento

**Datos.** 32.769 solicitudes etiquetadas y 58.921 sin etiqueta (la prueba de la competencia, que no sirve para medir). Nueve variables, todas **códigos categóricos anónimos** guardados como enteros: su magnitud no significa nada. No hay vacíos, duplicados ni datos personales. Hay 4.243 gerentes (unas 7,7 solicitudes cada uno) y 7.518 recursos. Entre entrenamiento y prueba hay deriva en el gerente (PSI ≈ 0,28) y en la descripción de familia de rol (≈ 0,18): en producción aparecerán gerentes nuevos.

**Decisiones principales, cada una con su motivo:**

| Decisión | Motivo |
|---|---|
| Tratar todos los códigos como categorías, no como números | Su tamaño carece de significado |
| Eliminar `ROLE_CODE` | Equivale uno a uno a `ROLE_TITLE` (343 = 343) |
| Descartar `ROLE_ROLLUP_1` y `ROLE_FAMILY` | La ablación con validación cruzada por gerente no mostró pérdida (ROC-AUC 0,702 con y sin ellas) |
| Codificar las categorías de alta cardinalidad con frecuencias y tasas históricas de aprobación suavizadas, calculadas fuera de pliegue | Evita miles de columnas casi vacías y la fuga de la etiqueta |
| Todo lo que aprende de los datos vive dentro de un *pipeline* ajustado solo con entrenamiento | Evita fuga de información |
| Reserva cerrada del 20 % (6.554 solicitudes, 883 gerentes) | Medir en gerentes que el modelo nunca vio |

**Variables finales.** El constructor genera 29 variables: frecuencias de cada código y de sus combinaciones, número de valores distintos por grupo y tasas históricas de aprobación. Una ablación mostró que las frecuencias solas rinden 0,64 de ROC-AUC y que las tasas históricas solas llegan a 0,71.

## 4. Estrategia de validación: StratifiedGroupKFold por gerente

**Por qué no por fila.** Un mismo gerente aparece en promedio unas ocho veces y decide de forma correlacionada. Si sus solicitudes quedan repartidas entre entrenamiento y validación, el modelo "reconoce" al gerente y el resultado se infla. Se comprobó: partiendo por fila, el ROC-AUC sube a 0,82 y el PR-AUC de *denegar* a 0,42 (con 1.866 gerentes compartidos); partiendo por gerente, quedan en 0,71 y 0,16. **La cifra honesta es la segunda.**

**Cómo se hace.** Cinco pliegues, estratificados por la etiqueta y agrupados por `MGR_ID` (ningún gerente aparece en dos pliegues), con semilla fija. El mismo esquema se usa dentro del constructor de variables para calcular las tasas históricas sin que cada fila vea su propia etiqueta. Una prueba automática verifica que ningún gerente cruce la partición.

## 5. Torneo de modelos y optimización

Se compararon seis modelos con el mismo esquema de validación:

| Modelo | ROC-AUC | Auto-aprobación con 0 FP |
|---|---|---|
| Regresión logística ElasticNet | 0,733 | 2,04 % |
| Regresión logística L2 (referencia) | 0,733 | 2,03 % |
| Random Forest | 0,726 | 0,71 % |
| LightGBM | 0,723 | 0,77 % |
| XGBoost | 0,720 | 1,85 % |
| CatBoost | 0,719 | 0,69 % |

Los modelos de árboles, aun regularizados, **no superaron** a los lineales: la señal es modesta y los modelos más flexibles memorizan. Se eligió la regresión logística ElasticNet (la más simple entre las mejores, además muy rápida: unos 10 ms por solicitud individual y 0,02 ms por solicitud en lote).

**Optimización.** Con 50 ensayos de Optuna la auto-aprobación estricta en validación cruzada subió a 3,4 %. Sin embargo, al repetir con tres semillas distintas, **la mejora no se distingue del ruido** frente al modelo por defecto. Se conservan los hiperparámetros optimizados por trazabilidad, pero la conclusión es que afinar no aporta aquí.

## 6. Zonas de decisión y desempeño

Las zonas se fijan **solo con predicciones fuera de pliegue del entrenamiento**:

- **Verde:** probabilidad por encima del umbral estricto (0,981), el menor que en validación cruzada no dejó pasar ninguna denegación. Auto-aprobación.
- **Amarilla:** zona intermedia. Cola de triaje ordenada de más a menos sospechosa.
- **Roja:** el 10 % más sospechoso (probabilidad menor a 0,745). Revisión manual a fondo. Es un parámetro de capacidad del equipo, ajustable sin reentrenar.

**Resultados en la reserva (6.554 solicitudes, 379 indebidas = 5,8 %):**

| Zona | Solicitudes | % del total | Accesos indebidos | % indebidos en la zona | Frente al promedio |
|---|---|---|---|---|---|
| Verde | 341 | 5,2 % | 2 | 0,6 % | 0,10 × |
| Amarilla | 5.546 | 84,6 % | 261 | 4,7 % | 0,81 × |
| Roja | 667 | 10,2 % | 116 | 17,4 % | 3,0 × |

- ROC-AUC 0,701 y PR-AUC de *denegar* 0,199 (el azar daría 0,058).
- Zona verde: 2 accesos indebidos sobre 341; la tasa real de falsos positivos podría ser de hasta 1,65 % (95 % de confianza). Que la validación cruzada mostrara cero **no** probó que la tasa real fuera cero.
- Captura en la cola: revisando el primer 5 %, 10 % y 20 % de lo no auto-aprobado se encuentra el 21 %, 31 % y 42 % de las denegaciones.
- **Limitación importante:** la zona amarilla, que es la más grande, tiene menos denegaciones que el promedio; el valor está en los extremos (verde segura y roja sospechosa), no en separar el centro.

**Advertencia de método.** La reserva se abrió tres veces (enfoque monetario, enfoque Zero Trust y este análisis). Las dos últimas fueron de solo lectura y los umbrales no se tocaron tras verla. Aun así, está "gastada": la verdadera prueba de producción debe hacerse con datos nuevos etiquetados.

**Calibración.** La probabilidad no está bien calibrada: el error de calibración esperado es 0,081 en validación cruzada y 0,079 en la reserva (Brier 0,061). La regularización fuerte comprime las probabilidades. Por eso los umbrales se leen como **puntos de corte de un ranking**, no como "98 % de certeza". No se recalibró para no mover los umbrales ya fijados.

## 7. Explicabilidad con SHAP

Se calcularon valores SHAP del modelo final sobre la reserva (espacio de log-odds de aprobar; la suma de contribuciones reconstruye exactamente la decisión). El gráfico está en `reports/figures/shap_summary.png` y el detalle en `reports/07_shap_analysis.json`.

**Hallazgos:**

- Las **variables de frecuencia** explican el 74 % del impacto; las tasas históricas de aprobación, el 19 %; el número de valores distintos por grupo, el 6 %.
- Las tres variables que más pesan son la frecuencia de la combinación recurso × gerente (26 %), recurso × departamento (19 %) y gerente × cargo (14 %).
- Interpretación: el modelo decide sobre todo según **qué tan habitual es la combinación** en el historial. Solicitudes rutinarias reciben más probabilidad de aprobación; combinaciones raras, menos.

**Qué no dicen los valores SHAP.** Explican cómo decide el modelo, no por qué un gerente aprueba o niega: los códigos son anónimos. Además, depender de la rareza implica que un empleado legítimo con una necesidad inusual recibirá más revisión humana (más fricción), y una solicitud indebida pero habitual podría pasar. Es un riesgo que debe vigilarse.

## 8. Arquitectura de despliegue

1. **Entrenamiento y artefacto.** El notebook 06 optimiza; el 07 reconstruye el modelo con los hiperparámetros elegidos, fija las zonas y congela `models/model.joblib`. Este paquete contiene el *pipeline* completo, los umbrales, las métricas y un fondo de referencia para SHAP.
2. **Seguimiento y registro (Databricks / MLflow).** El notebook 08, pensado para cómputo Serverless, abre la corrida `AccessGuard_ZeroTrust_Experiment`, registra hiperparámetros, métricas Zero Trust (ROC-AUC, tasa de auto-aprobación estricta y captura en la cola de triaje), empaqueta el modelo con firma de entrada y salida y lo registra como `AccessGuard_ZeroTrust_Model` con el alias `champion`. Se probó el mismo flujo en local con una base SQLite; **no se ha ejecutado aún en un espacio de trabajo real de Databricks**, donde habrá que ajustar catálogo y esquema de Unity Catalog.
3. **Aplicación (Streamlit).** La app carga `models/model.joblib` directamente, sin credenciales ni consulta a la nube. Recibe los seis códigos de la solicitud, muestra la zona con color (verde, amarillo, rojo), la probabilidad y la explicación SHAP local, y avisa cuando un código nunca se vio en el entrenamiento.
4. **Flujo operativo propuesto.** Verde: aprobación automática con registro de auditoría. Amarillo: cola del analista, ordenada por sospecha. Rojo: revisión manual obligatoria. Nunca se deniega automáticamente.

**Controles que faltan antes de producción:**

- Medir los tiempos de espera reales (SLA) y la criticidad de cada recurso, para fijar umbrales por recurso (más estrictos en recursos críticos).
- Detección de anomalías y recertificación periódica de accesos.
- Monitoreo de deriva (aparecen gerentes y roles nuevos) y de la tasa de accesos indebidos en la zona verde; si sube, volver a revisión humana total.
- Revisar los términos de licencia del dataset antes de publicar el repositorio.

## 9. Conclusiones y límites

1. El modelo aporta poco como automatizador (≈ 5 % de auto-aprobación con un error residual) y algo más como **priorizador** de la cola de revisión.
2. La partición por gerente es la decisión metodológica más importante: evita una ilusión de rendimiento de 0,82 frente a 0,70.
3. Optimizar hiperparámetros y usar modelos de árboles no mejoró el resultado: con esta señal, la sencillez gana.
4. Toda cifra con cero errores observados debe leerse con su cota superior.
5. Lo que no se evaluó: estabilidad en el tiempo, otros grupos de empleados, deriva real y el efecto sobre el SLA.
