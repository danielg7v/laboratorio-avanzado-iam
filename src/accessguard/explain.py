"""Explicabilidad (SHAP) y zonas de decisión Zero Trust.

Convención: p = probabilidad de *aprobar*. Las zonas se definen con dos umbrales fijados SOLO con
predicciones fuera de pliegue (OOF) del entrenamiento; la reserva nunca decide un umbral.

- Verde    (p > t_auto)            : auto-aprobación estricta.
- Amarillo (t_low <= p <= t_auto)  : cola de triaje priorizada (un analista IAM la revisa, de más sospechosa a menos).
- Rojo     (p < t_low)             : revisión manual obligatoria (sospecha alta). Nunca se auto-deniega.
"""
import numpy as np
import pandas as pd

ZONE_GREEN, ZONE_YELLOW, ZONE_RED = "verde", "amarillo", "rojo"
ZONE_LABELS = {
    ZONE_GREEN: "Auto-aprobación estricta",
    ZONE_YELLOW: "Cola de triaje priorizada",
    ZONE_RED: "Revisión manual",
}


def compute_t_low(p_oof, red_fraction: float = 0.10) -> float:
    """Umbral inferior: la fracción `red_fraction` de solicitudes con menor p (más sospechosas) cae en rojo.

    Es una decisión de capacidad del equipo IAM (cuántos casos puede revisar a fondo), no del modelo.
    """
    if not 0 < red_fraction < 1:
        raise ValueError("red_fraction debe estar entre 0 y 1")
    return float(np.quantile(np.asarray(p_oof), red_fraction))


def assign_zone(p_approve, t_low: float, t_auto: float) -> np.ndarray:
    """Zona de cada solicitud: verde si p > t_auto, rojo si p < t_low, amarillo en medio."""
    if t_low > t_auto:
        raise ValueError("t_low no puede superar a t_auto")
    p = np.asarray(p_approve, dtype=float)
    return np.where(p > t_auto, ZONE_GREEN, np.where(p < t_low, ZONE_RED, ZONE_YELLOW))


def zone_summary(y_true, p_approve, t_low: float, t_auto: float) -> pd.DataFrame:
    """Tabla por zona: volumen, accesos indebidos (y = 0) y tasa de denegación dentro de la zona."""
    y = np.asarray(y_true)
    zone = assign_zone(p_approve, t_low, t_auto)
    base = float((y == 0).mean())
    rows = []
    for z in (ZONE_GREEN, ZONE_YELLOW, ZONE_RED):
        m = zone == z
        n = int(m.sum())
        n_bad = int((y[m] == 0).sum())
        rate = n_bad / n if n else float("nan")
        rows.append({"zona": z, "decisión": ZONE_LABELS[z], "n": n, "% del total": n / len(y),
                     "accesos indebidos": n_bad, "% indebidos en la zona": rate,
                     "lift vs base": rate / base if base and n else float("nan")})
    return pd.DataFrame(rows).set_index("zona")


def split_pipeline(pipeline):
    """Separa un pipeline entrenado en (constructor de variables, modelo final)."""
    return pipeline.named_steps["features"], pipeline.named_steps["model"]


def _linear_parts(model):
    """Si el modelo es 'escalador + regresión logística' devuelve (escalador, clasificador); si no, (None, model)."""
    steps = getattr(model, "named_steps", None)
    if steps and "scale" in steps and "clf" in steps:
        return steps["scale"], steps["clf"]
    return None, model


def make_explainer(pipeline, background: pd.DataFrame):
    """Explicador SHAP del modelo final sobre las variables ya construidas (espacio log-odds de aprobar)."""
    import shap
    _, model = split_pipeline(pipeline)
    scaler, est = _linear_parts(model)
    if scaler is not None:
        return shap.LinearExplainer(est, scaler.transform(background[list(background.columns)]))
    return shap.TreeExplainer(est, data=background, feature_perturbation="interventional")


def shap_values(pipeline, explainer, X_features: pd.DataFrame) -> pd.DataFrame:
    """Valores SHAP (log-odds de aprobar) por variable; positivo = empuja hacia aprobar."""
    _, model = split_pipeline(pipeline)
    scaler, _ = _linear_parts(model)
    data = scaler.transform(X_features) if scaler is not None else X_features
    values = explainer.shap_values(data)
    if isinstance(values, list):          # algunos árboles devuelven una matriz por clase
        values = values[-1]
    values = np.asarray(values)
    if values.ndim == 3:
        values = values[..., -1]
    return pd.DataFrame(values, columns=list(X_features.columns), index=X_features.index)


def scaled_for_plot(pipeline, X_features: pd.DataFrame):
    """Matriz que corresponde a los valores SHAP en los gráficos (la escalada si el modelo es lineal)."""
    _, model = split_pipeline(pipeline)
    scaler, _ = _linear_parts(model)
    return scaler.transform(X_features) if scaler is not None else X_features


def impact_table(values: pd.DataFrame) -> pd.DataFrame:
    """Impacto global: media del valor absoluto y signo medio del efecto de cada variable."""
    out = pd.DataFrame({"mean_abs_shap": values.abs().mean(), "mean_shap": values.mean()})
    total = out["mean_abs_shap"].sum()
    out["share"] = out["mean_abs_shap"] / total if total else 0.0
    return out.sort_values("mean_abs_shap", ascending=False)


def explain_request(pipeline, explainer, X_raw: pd.DataFrame, top: int = 8) -> dict:
    """Explicación local de UNA solicitud: p(aprobar), base, y las variables que más empujan en cada sentido."""
    fb, model = split_pipeline(pipeline)
    feats = fb.transform(X_raw.iloc[[0]])
    p = float(pipeline.predict_proba(X_raw.iloc[[0]])[:, 1][0])
    sv = shap_values(pipeline, explainer, feats).iloc[0]
    base = float(np.ravel(explainer.expected_value)[-1])
    contrib = sv.reindex(sv.abs().sort_values(ascending=False).index)
    return {"p_approve": p, "base_value": base, "logit": float(base + sv.sum()),
            "top": [{"feature": k, "shap": float(v), "value": float(feats.iloc[0][k])} for k, v in contrib.head(top).items()]}


def expected_calibration_error(y_true, p, bins: int = 10) -> float:
    """ECE con casillas de igual ancho: promedio ponderado de |frecuencia observada − probabilidad media|."""
    y, p = np.asarray(y_true, dtype=float), np.asarray(p, dtype=float)
    idx = np.clip((p * bins).astype(int), 0, bins - 1)
    ece = 0.0
    for b in range(bins):
        m = idx == b
        if m.any():
            ece += m.mean() * abs(y[m].mean() - p[m].mean())
    return float(ece)


def unseen_codes(pipeline, X_raw: pd.DataFrame) -> list:
    """Columnas cuyo código la primera fila nunca apareció en el entrenamiento (el modelo no tiene historial de él)."""
    fb, _ = split_pipeline(pipeline)
    row = X_raw.iloc[0]
    out = []
    for col, counts in fb.counts_.items():
        if "|" in str(counts.index[0]) or col not in X_raw.columns:
            continue
        if str(int(row[col])) not in set(counts.index):
            out.append(col)
    return out


FEATURE_HELP = {
    "freq": "qué tan frecuente es la combinación en el historial",
    "te": "tasa histórica de aprobación de ese código",
    "nuniq": "variedad de recursos/códigos asociados",
}


def describe_feature(name: str) -> str:
    """Nombre legible en español de una variable construida (freq__/te__/nuniq__)."""
    kind, _, rest = name.partition("__")
    rest = rest.replace("_x_", " × ").replace("_por_", " por ")
    return {"freq": f"Frecuencia de {rest}", "te": f"Aprobación histórica de {rest}",
            "nuniq": f"Nº de distintos: {rest}"}.get(kind, name)
