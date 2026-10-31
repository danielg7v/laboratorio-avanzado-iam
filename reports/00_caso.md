# Ficha de caso — AccessGuard AI

> Estados: `borrador` → (`devuelta` → `borrador`)* → `aprobada`. Solo con la ficha **aprobada** se avanza al EDA.

- **case_id:** accessguard-iam
- **business_question:** El equipo de Gobierno de Accesos (IAM) debe aprobar o denegar solicitudes de acceso de empleados a recursos corporativos. Decide con el rol del empleado (departamento, título, familia de rol), su gerente y el recurso pedido. Queremos automatizar la decisión sin conceder accesos indebidos y sin bloquear a usuarios legítimos.
- **dataset_source:** Amazon Employee Access Challenge (Kaggle); licencia: términos de la competencia (revisar antes de publicar).
- **dataset_rows:** `train.csv` 32.769 (con etiqueta); `test.csv` 58.921 (sin etiqueta). ⚠ Menos de las 50.000 filas etiquetadas que pide `criterios-dataset.md`.
- **dataset_columns:** 10 en `train.csv` (9 variables + `ACTION`); 10 en `test.csv` (9 variables + `id`). ⚠ Todas categóricas (códigos).
- **target:** `ACTION` (1 = aprobado, 0 = denegado)
- **problem_type:** clasificación binaria, desbalanceada (94,2 % / 5,8 %)
- **primary_metric:** costo esperado por solicitud con matriz asimétrica; secundarias ROC-AUC, PR-AUC(denegar), recall(denegar). La exactitud no sirve: aprobar todo ya da 94,2 %.
- **business_cost_note:** FP (concesión indebida) es el error caro: riesgo de fuga, fraude e incumplimiento; supuesto USD 2.000. FN (bloqueo legítimo): ticket y horas perdidas; supuesto USD 40. Revisión manual: USD 6 por solicitud. **Los tres valores son supuestos a validar**; ver sensibilidad en `notebooks/01_caso_de_negocio.ipynb`.
- **status:** borrador
- **reviewer_notes:** <!-- las llena el instructor -->
