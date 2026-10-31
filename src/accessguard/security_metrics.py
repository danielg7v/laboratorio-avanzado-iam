"""Métricas de éxito del marco Zero Trust / IGA: auto-aprobación segura y triaje asistido.

Convención: p = probabilidad de *aprobar* (clase positiva = 1). Un falso positivo (FP) es un acceso indebido concedido.
"""
import time

import numpy as np
from scipy.stats import beta


def fpr_upper_bound(fp: int, n_neg: int, alpha: float = 0.05) -> float:
    """Cota superior (Clopper-Pearson, una cola) de la tasa de falsos positivos verdadera.

    Con 0 FP observados sobre n negativos la cota es ≈ 3/n ("regla de tres"): observar 0 errores
    no prueba que la tasa real sea 0.
    """
    if n_neg <= 0 or fp >= n_neg:
        return 1.0
    return float(beta.ppf(1 - alpha, fp + 1, n_neg - fp))


def auto_approval_at_zero_fpr(y_true, p_approve) -> dict:
    """Auto-aprobación con FPR = 0 %: se aprueba solo lo que puntúa por encima de TODA solicitud que debía denegarse.

    Devuelve el umbral, la tasa de auto-aprobación (fracción de todas las solicitudes) y la cota superior del FPR real.
    """
    y, p = np.asarray(y_true), np.asarray(p_approve)
    neg = p[y == 0]
    t = float(neg.max()) if len(neg) else -np.inf
    approved = p > t
    return {"threshold": t, "auto_approval_rate": float(approved.mean()), "n_approved": int(approved.sum()), "fp": 0,
            "fpr_upper95": fpr_upper_bound(0, len(neg))}


def auto_approval_at_confidence(y_true, p_approve, confidence: float = 0.98) -> dict:
    """Auto-aprobación de lo que el modelo puntúa con confianza >= `confidence`; mide cuántos FP se cuelan."""
    y, p = np.asarray(y_true), np.asarray(p_approve)
    approved = p >= confidence
    n, n_neg = int(approved.sum()), int((y == 0).sum())
    fp = int((approved & (y == 0)).sum())
    return {"confidence": confidence, "auto_approval_rate": float(approved.mean()), "n_approved": n, "fp": fp,
            "precision": float(1 - fp / n) if n else float("nan"), "fpr": fp / n_neg if n_neg else float("nan"),
            "fpr_upper95": fpr_upper_bound(fp, n_neg)}


def review_queue_stats(y_true, p_approve, confidence: float = 0.98) -> dict:
    """Triaje asistido: lo no auto-aprobado va a un analista IAM. ¿Qué tan 'rica' es esa cola en denegaciones?

    `lift` = tasa de denegaciones en la cola / tasa de denegaciones global (1 = la cola no ayuda a priorizar).
    """
    y, p = np.asarray(y_true), np.asarray(p_approve)
    review = p < confidence
    base = float((y == 0).mean())
    rate_in = float((y[review] == 0).mean()) if review.any() else float("nan")
    return {"review_rate": float(review.mean()), "deny_rate_in_queue": rate_in, "lift": rate_in / base if base else float("nan"),
            "share_of_denials_in_queue": float(((y == 0) & review).sum() / max((y == 0).sum(), 1))}


def precision_at_top(y_true, p_approve, fraction: float) -> float:
    """Precisión de 'aprobar' entre la fracción de solicitudes con mayor probabilidad (zona de ultra-alta confianza)."""
    y, p = np.asarray(y_true), np.asarray(p_approve)
    k = max(int(round(fraction * len(p))), 1)
    top = np.argsort(-p, kind="stable")[:k]
    return float(y[top].mean())


def decision_latency_ms(pipeline, X, repeats: int = 100) -> dict:
    """Latencia medida de puntuar UNA solicitud (ms) y por lote de 1.000 (ms/solicitud) con un pipeline ya entrenado."""
    one = X.iloc[[0]]
    pipeline.predict_proba(one)  # calentamiento
    times = []
    for i in range(repeats):
        row = X.iloc[[i % len(X)]]
        t0 = time.perf_counter()
        pipeline.predict_proba(row)
        times.append((time.perf_counter() - t0) * 1000)
    batch = X.iloc[: min(1000, len(X))]
    t0 = time.perf_counter()
    pipeline.predict_proba(batch)
    per_req = (time.perf_counter() - t0) * 1000 / len(batch)
    return {"single_median_ms": float(np.median(times)), "single_p95_ms": float(np.percentile(times, 95)), "batch_ms_per_request": float(per_req)}


def auto_approval_at_fp_budget(y_true, p_approve, max_fp: int = 0) -> dict:
    """Auto-aprobación tolerando como máximo `max_fp` accesos indebidos (presupuesto de FP). max_fp=0 es el caso estricto."""
    y, p = np.asarray(y_true), np.asarray(p_approve)
    neg = np.sort(p[y == 0])[::-1]                     # puntuaciones de los indebidos, de mayor a menor
    t = float(neg[max_fp]) if len(neg) > max_fp else -np.inf   # se aprueba lo que supera al (max_fp+1)-ésimo indebido
    approved = p > t
    fp = int((approved & (y == 0)).sum())
    return {"max_fp": max_fp, "threshold": t, "auto_approval_rate": float(approved.mean()), "n_approved": int(approved.sum()),
            "fp": fp, "fpr": fp / max(len(neg), 1), "fpr_upper95": fpr_upper_bound(fp, len(neg))}


def queue_capture(y_true, p_approve, threshold: float, fractions=(0.05, 0.10, 0.20, 0.50)) -> dict:
    """Valor de ordenar la cola del analista: la cola es todo lo que NO supera `threshold`, ordenada de más sospechoso
    (p más baja) a menos. Devuelve qué fracción de las denegaciones se encuentra revisando solo el primer X % de la cola."""
    y, p = np.asarray(y_true), np.asarray(p_approve)
    q = np.flatnonzero(~(p > threshold))
    q = q[np.argsort(p[q], kind="stable")]             # más sospechoso primero
    n_deny_total = max(int((y == 0).sum()), 1)
    out = {}
    for f in fractions:
        k = max(int(round(f * len(q))), 1) if len(q) else 0
        out[f"{int(f * 100)}%"] = float((y[q[:k]] == 0).sum() / n_deny_total) if k else 0.0
    out["n_queue"] = int(len(q))
    return out


def predict_zero_trust(bundle: dict, X) -> "pd.DataFrame":
    """Aplica un paquete exportado: auto-aprobar si p > t_auto (umbral estricto); en otro caso, revisión humana (nunca auto-deniega).

    Devuelve p_approve, la decisión y la prioridad en la cola (1 = revisar primero, la más sospechosa).
    """
    import pandas as pd
    p = bundle["pipeline"].predict_proba(X)[:, 1]
    auto = p > bundle["t_auto_strict"]
    out = pd.DataFrame({"p_approve": p, "decision": np.where(auto, "aprobar_auto", "revisar")}, index=X.index)
    rev = ~auto
    out["prioridad_revision"] = np.nan
    out.loc[rev, "prioridad_revision"] = pd.Series(p[rev], index=X.index[rev]).rank(method="first").to_numpy()
    return out
