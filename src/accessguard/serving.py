"""Empaquetado para MLflow: convierte `models/model.joblib` en un modelo `pyfunc` que devuelve p, zona y decisión."""
import joblib
import mlflow.pyfunc
import pandas as pd

from accessguard.explain import ZONE_LABELS, assign_zone


class AccessGuardZeroTrust(mlflow.pyfunc.PythonModel):
    """Entrada: columnas de la solicitud (códigos enteros). Salida: p_approve, zone y decision.

    Nunca auto-deniega: lo que no es verde se envía a un analista IAM (amarillo = cola priorizada, rojo = revisión manual).
    """

    def load_context(self, context):
        self.bundle = joblib.load(context.artifacts["bundle"])

    def predict(self, context, model_input, params=None):
        b = self.bundle
        X = pd.DataFrame(model_input)[list(b["input_columns"])]
        p = b["pipeline"].predict_proba(X)[:, 1]
        zone = assign_zone(p, b["t_low"], b["t_auto_strict"])
        return pd.DataFrame({"p_approve": p, "zone": zone, "decision": [ZONE_LABELS[z] for z in zone]}, index=X.index)
