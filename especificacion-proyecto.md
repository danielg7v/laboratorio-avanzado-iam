# Especificación del proyecto — AccessGuard AI

> Claude la lee antes de generar código: lo que escriban aquí manda sobre cualquier otra suposición.

## 1. Grupo

| Integrante | Rol (datos / modelado / app / negocio) |
|---|---|
| danielg7v | datos / modelado (completar el resto del grupo) |
| Carlos Mario Trujillo Murillo (trujillo8009) | negocio / presentación |
| | |

Nombre de la "startup": **AccessGuard AI**   Repositorio: https://github.com/danielg7v/laboratorio-avanzado-iam

## 2. Caso de negocio

- **Pregunta de negocio:** ¿Podemos aprobar o denegar automáticamente una solicitud de acceso a un recurso corporativo, usando el rol del empleado y el recurso pedido, sin conceder accesos indebidos y sin bloquear a quien sí debe trabajar?
- **¿Quién usará el resultado y qué decisión tomará con él?** El equipo de Gobierno de Accesos (IAM) y Seguridad: aprobar, denegar o escalar a revisión humana cada solicitud.
- **¿Qué cuesta equivocarse?** El peor error es el **Falso Positivo = concesión indebida** (riesgo de fuga de datos, fraude, incumplimiento). El **Falso Negativo = bloqueo legítimo** cuesta un ticket y horas perdidas. Supuesto de trabajo: un FP cuesta 50 veces un FN (USD 2.000 vs 40; **a validar** con Seguridad/Riesgos, ver `config/settings.py`).

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

- **Métrica principal:** **costo esperado por solicitud** (matriz asimétrica FP/FN al umbral elegido en validación). Porque el 94 % se aprueba y un FP no cuesta lo mismo que un FN.
- **Métricas secundarias:** ROC-AUC; PR-AUC de la clase *denegar*; recall de *denegar*; % de solicitudes resueltas sin humano.
- **Línea base** (reserva por gerente, costos supuestos): aprobar todo ≈ USD 116/solicitud; denegar todo ≈ 38; regla de historial del recurso ≈ 34; **revisión manual 100 % ≈ 6** (la cifra a vencer). Ver `notebooks/01_caso_de_negocio.ipynb`.

## 5. Riesgos

- **Fuga de información posible:** partición por fila (se midió: PR-AUC(denegar) 0,42 por fila vs 0,16 por gerente); target encoding sin validación cruzada interna.
- **Sesgos o equidad:** `ACTION` es la decisión *humana* histórica, no necesariamente la correcta; el modelo hereda sus sesgos. No usar para sancionar personas; denegaciones automáticas apelables.
- **Datos faltantes o de mala calidad:** 0 vacíos y 0 duplicados; pero `RESOURCE = 0` (13 filas) por aclarar; deriva `train→test` en `MGR_ID` (PSI ≈ 0,28) y `ROLE_FAMILY_DESC` (≈ 0,18).
- **Límites de lo que el modelo puede decir:** variables anónimas (no se interpreta el "significado" del rol); costos supuestos; `test.csv` sin etiqueta.

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
