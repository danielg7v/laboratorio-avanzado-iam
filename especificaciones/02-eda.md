# Especificación · Etapa 2 · EDA — AccessGuard AI

> Guía: `curso/kit-estudiante/guia-eda-y-preprocesamiento.md` · Notebook: `notebooks/02_eda.ipynb` · Resultado: `reports/01_eda.md`.

**Grupo:** AccessGuard AI   **Fecha:** 2026-10-30   **Estado:** ☐ borrador  ☑ cerrada (pendiente de revisión del grupo)

## 1. Qué esperamos encontrar

> Nota de honestidad: estas hipótesis se redactaron tras una primera mirada a las cabeceras y al tamaño de los archivos, no a ciegas; lo contrastado quedó en la columna derecha.

| Pregunta | Lo que creemos | ¿Se cumplió? |
|---|---|---|
| ¿Qué representa una fila? | Una solicitud de acceso (empleado/rol → recurso) | Sí |
| ¿Alguna entidad se repite en varias filas? | Sí: gerentes y recursos | Sí: 4.243 gerentes para 32.769 filas; 7.518 recursos |
| ¿Qué variable **debería** ser estable y no cambiar? | La jerarquía de rol (título → familia) | Sí: `ROLE_TITLE` determina `ROLE_FAMILY` al 100 % |
| ¿Qué significaría un vacío en nuestras columnas clave? | "No se registró el atributo" | No hay vacíos (0 en train y test) |
| ¿Qué columna solo se conoce **después** de la decisión? | Ninguna (todas son atributos de la solicitud) | Sí, ninguna |

## 2. Qué vamos a medir

| Chequeo (guía, sección 3) | ¿Aplica? | Columnas a revisar |
|---|---|---|
| 3.1 Números guardados como texto | ☑ no: son enteros; el problema inverso es que **son códigos, no cantidades** | las 9 |
| 3.2 Valores centinela (`-1`, `9999`, `?`) | ☑ sí | todas; solo `RESOURCE = 0` (13 filas) es sospechoso |
| 3.3 Valores imposibles | ☑ no aplica a códigos; se revisó mín./máx. | todas |
| 3.4 Constancia por entidad | ☑ sí (jerarquía de roles, dependencias funcionales) | `ROLE_*` |
| 3.5 Vacíos que significan algo | ☑ sí (se midió: 0) | todas |
| 3.6 Duplicados | ☑ sí | filas completas y conflictos de etiqueta |
| 3.7 Fechas y orden temporal | ☑ no: no hay columna de fecha; `id` de test solo numera filas | — |
| 3.8 Categorías raras / alta cardinalidad | ☑ sí | `RESOURCE`, `MGR_ID`, `ROLE_FAMILY_DESC` |
| 3.9 Identidad y datos personales | ☑ no: códigos anónimos | — |

## 3. Lo que medimos

- **Filas × columnas:** train 32.769 × 10; test 58.921 × 10.
- **Unidad de análisis:** una solicitud de acceso de un empleado (con su rol y gerente) a un recurso.
- **`ID_COL` (entidad que se repite):** `MGR_ID`. **¿Se repite?** ☑ sí, ≈ 7,7 filas por gerente (mediana 4, máx. 152).
- **Objetivo (`TARGET`):** `ACTION`. **Distribución:** 94,21 % aprobadas (1), 5,79 % denegadas (0).
- **Línea base:** aprobar siempre = 94,2 % de exactitud (inútil); en costo, la revisión manual ≈ USD 6/solicitud supera a las reglas simples (notebook 01).
- **Vacíos en el objetivo:** 0. **Qué haremos con esas filas:** nada que hacer.
- **Datos personales encontrados:** ninguno.
- **Columnas sospechosas de fuga:** ninguna directa; `MGR_ID`/`RESOURCE` filtran por partición por fila (se mide en la etapa 3). `ROLE_CODE` duplica a `ROLE_TITLE`.

## 4. Decisiones (mínimo 5)

Las 9 decisiones con cifra, motivo y función están en `reports/01_eda.md` y en la sección 11 de `notebooks/02_eda.ipynb`.

## 5. Criterios de cierre

- ☑ `notebooks/02_eda.ipynb` corre de principio a fin sin errores.
- ☑ Unidad de análisis y `ID_COL` declarados por escrito.
- ☑ Al menos **5 decisiones** con cifra, acción y motivo (hay 9).
- ☑ Datos personales: ninguno; no hay nada que eliminar.
- ☑ Centinelas y vacíos revisados.
- ☑ Fuga sospechada: lista escrita (sección 3).
- ☑ `reports/01_eda.md` completado.
- ☐ Quien **no** escribió una decisión sabe explicar por qué se tomó.
