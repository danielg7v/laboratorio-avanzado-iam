# Especificación del proyecto — AccessGuard AI

> Claude la lee antes de generar código: lo que escriban aquí manda sobre cualquier otra suposición.

## 1. Grupo

| Integrante | Rol (datos / modelado / app / negocio) |
|---|---|
| danielg7v | datos / modelado (completar el resto del grupo) |
| | |

Nombre de la "startup": **AccessGuard AI**   Repositorio: https://github.com/danielg7v/laboratorio-avanzado-iam

## 2. Caso de negocio

- **Pregunta de negocio:** ¿Podemos **auto-aprobar con seguridad** las solicitudes rutinarias de acceso a recursos corporativos —sin conceder ningún acceso indebido— y canalizar a un analista IAM solo lo ambiguo o anómalo? Marco: **Identity Governance & Administration (IGA)** bajo **Zero Trust** y **Menor Privilegio**.
- **¿Quién usará el resultado y qué decisión tomará con él?** El equipo de Gobierno de Accesos (IAM) y Seguridad: auto-aprobar lo rutinario y seguro, y escalar a revisión humana (*human-in-the-loop*) lo ambiguo; las denegaciones son revisables y apelables.
- **¿Qué impacto tiene equivocarse?** (matriz de impacto cualitativa en `notebooks/01_caso_de_negocio.ipynb`, sin montos en dólares). El peor error es el **Falso Positivo = acceso indebido concedido**: viola Menor Privilegio, amplía la superficie de movimiento lateral, es un hallazgo de auditoría y es difícil de detectar. El **Falso Negativo = acceso legítimo demorado** daña la productividad, pero es visible y fácil de corregir. **Se abandonó el costo en USD** (el dataset no trae costos): los valores de la fase anterior eran supuestos arbitrarios.

## 3. Datos

- **Fuente:** Amazon Employee Access Challenge (Kaggle). Archivos entregados por el docente en `Data/`.
- **Filas / columnas:** `train.csv` 32.769 × 10 (con etiqueta); `test.csv` 58.921 × 10 (sin etiqueta, con `id`).
- **Variable objetivo:** `ACTION` (1 = aprobado 94,2 %; 0 = denegado 5,8 %).
- **Tipo de problema:** ☑ clasificación (binaria, muy desbalanceada) ☐ regresión ☐ clusterización
- **¿Una misma entidad aparece en varias filas?** ☑ sí → la partición será por: **`MGR_ID`** (4.243 gerentes, ≈ 7,7 solicitudes por gerente). `RESOURCE` también se repite.
- **Datos personales o confidenciales presentes:** ☑ no (solo códigos numéricos anónimos).
- **Licencia o permiso de uso de los datos:** términos de la competencia de Kaggle; revisar antes de publicar el repo.
- **⚠ Frente a `curso/evaluacion/criterios-dataset.md`:** solo hay 32.769 filas **con etiqueta** (< 50.000; con `test.csv` suman 91.690 pero sin etiqueta) y **todas las variables son categóricas** (no hay numéricas originales). Hay que plantearlo al instructor en la revisión de la ficha.

## 4. Métrica

- **Éxito del proyecto (3 pilares):**
  1. **Tasa de Auto-Aprobación Segura (AAR @ FPR = 0 % / confianza ≥ 98 %)**: % de solicitudes rutinarias de bajo riesgo auto-aprobadas **sin conceder accesos indebidos** (0 falsos positivos). Toda cifra de FPR = 0 % se acompaña de su cota superior al 95 % (regla de tres).
  2. **Reducción de fricción y SLA**: latencia de decisión de los accesos legítimos (de días a milisegundos). La latencia del modelo se mide; el tiempo de espera manual actual **no está en los datos** y debe medirse con tickets reales.
  3. **Triaje asistido (human-in-the-loop)**: lo ambiguo o anómalo va a analistas IAM; se mide la carga de revisión y el *lift* de la cola para prevenir la **fatiga de aprobación**.
- **Métricas técnicas de apoyo:** ROC-AUC; PR-AUC de la clase *denegar*; precisión en zonas de ultra-alta confianza. La exactitud nunca se usa sola.
- **Línea base** (OOF por gerente, solo entrenamiento): revisión manual 100 % (0 FP, 0 % auto-aprobado); regla de historial del recurso a p ≥ 0,98 (≈ 18 % auto-aprobado pero 161 accesos indebidos) y con umbral FPR = 0 % (0 % auto-aprobado). Ver `notebooks/01_caso_de_negocio.ipynb`.
- **Código:** `src/accessguard/security_metrics.py`; constantes en `config/settings.py` (`TARGET_FPR`, `AUTO_APPROVE_CONFIDENCE`).

## 5. Riesgos

- **Fuga de información posible:** partición por fila (se midió: PR-AUC(denegar) 0,42 por fila vs 0,16 por gerente); target encoding sin validación cruzada interna.
- **Sesgos o equidad:** `ACTION` es la decisión *humana* histórica, no necesariamente la correcta; el modelo hereda sus sesgos. No usar para sancionar personas; denegaciones automáticas apelables.
- **Datos faltantes o de mala calidad:** 0 vacíos y 0 duplicados; pero `RESOURCE = 0` (13 filas) por aclarar; deriva `train→test` en `MGR_ID` (PSI ≈ 0,28) y `ROLE_FAMILY_DESC` (≈ 0,18).
- **Límites de lo que el modelo puede decir:** variables anónimas (no se interpreta el "significado" del rol); sin criticidad de recursos ni SLA manual en los datos; `test.csv` sin etiqueta. Ante la duda, escalar a humano (Zero Trust).

## 6. Entregables y fechas

| Hito | Contenido | Fecha |
|---|---|---|
| H1 | Ficha aprobada, EDA y preprocesamiento reproducible | Cierre de la clase 2 (vie 30 oct) |
| H2 | Torneo, optimización con tracking, modelo registrado, repo modular, app local | Cierre de la clase 4 (jue 5 nov) |
| H3 | App desplegada y presentación (≤ 5 diapositivas) | Clase 5 (vie 6 nov) |
| H4 | Informe técnico final (hasta 8 días tras la última clase) | Domingo 15 nov |

## 7. Decisiones tomadas (agréguenlas a medida que avancen)

| Fecha | Decisión | Motivo |
|---|---|---|
| 2026-10-30 | Clase positiva = aprobar (`ACTION=1`); FP = concesión indebida | Alinea la matriz con el riesgo del negocio |
| 2026-10-30 | Métrica principal = costo esperado por solicitud; accuracy descartada | 94,2 % de aprobaciones |
| 2026-10-30 | Partición por `MGR_ID`, estratificada, reserva cerrada del 20 % | Evitar fuga (ver notebook 03) |
| 2026-10-30 | Eliminar `ROLE_CODE`; descartar provisionalmente `ROLE_ROLLUP_1` y `ROLE_FAMILY` | Redundancia jerárquica + ablación con CV por gerente |
| 2026-10-30 | `MGR_ID` se conserva como variable (caso límite) y como llave de grupo | Δ ROC-AUC ≈ −0,002 ± 0,008 al quitarlo; 97 % de `test.csv` tiene gerente conocido |
| 2026-10-31 | **Reorientación a Zero Trust / IGA**: el éxito se mide con Auto-Aprobación Segura (FPR = 0 %), reducción de fricción/SLA y triaje asistido; se abandona el costo en USD | El dataset no trae costos; Zero Trust prioriza no conceder accesos indebidos y escalar lo ambiguo a un analista |
| 2026-10-31 | Las constantes COST_* de `config/settings.py` quedan como LEGADO (solo las importa el notebook 06, pendiente de reorientar) | Evitar romper el 06 mientras se reorienta el resto |
