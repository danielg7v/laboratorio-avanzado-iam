# Ficha de caso — AccessGuard AI

> Estados: `borrador` → (`devuelta` → `borrador`)* → `aprobada`. Solo con la ficha **aprobada** se avanza al EDA.

- **case_id:** accessguard-iam
- **business_question:** El equipo de Gobierno de Accesos (IAM) debe aprobar o denegar solicitudes de acceso de empleados a recursos corporativos. Decide con el rol del empleado (departamento, título, familia de rol), su gerente y el recurso pedido. Queremos **auto-aprobar con seguridad lo rutinario** (marco Zero Trust / IGA, Menor Privilegio) sin conceder accesos indebidos, y canalizar a un analista IAM lo ambiguo o anómalo (*human-in-the-loop*).
- **dataset_source:** Amazon Employee Access Challenge (Kaggle); licencia: términos de la competencia (revisar antes de publicar).
- **dataset_rows:** `train.csv` 32.769 (con etiqueta); `test.csv` 58.921 (sin etiqueta). ⚠ Menos de las 50.000 filas etiquetadas que pide `criterios-dataset.md`.
- **dataset_columns:** 10 en `train.csv` (9 variables + `ACTION`); 10 en `test.csv` (9 variables + `id`). ⚠ Todas categóricas (códigos).
- **target:** `ACTION` (1 = aprobado, 0 = denegado)
- **problem_type:** clasificación binaria, desbalanceada (94,2 % / 5,8 %)
- **primary_metric:** **Tasa de Auto-Aprobación Segura** (% de solicitudes auto-aprobadas con FPR = 0 % / confianza ≥ 98 %), junto con reducción de fricción/SLA y triaje asistido (carga de revisión y *lift* de la cola). Apoyo: ROC-AUC, PR-AUC(denegar), precisión en zonas de ultra-alta confianza. La exactitud no sirve: aprobar todo ya da 94,2 %.
- **business_cost_note:** ya **no se usan costos en USD** (el dataset no los trae). FP (acceso indebido concedido) es el error crítico: viola Menor Privilegio, habilita movimiento lateral, es hallazgo de auditoría y es poco detectable. FN (acceso legítimo demorado): afecta la productividad pero es visible y reversible. Ver la matriz de impacto cualitativa en `notebooks/01_caso_de_negocio.ipynb`.
- **status:** borrador
- **reviewer_notes:** <!-- las llena el instructor -->
