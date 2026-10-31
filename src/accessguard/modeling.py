"""Utilidades de modelado: candidatos del torneo, validación por gerente, métricas y umbral de decisión.

Convención: clase positiva = 1 = aprobar. FP = acceso concedido indebidamente (caro); FN = usuario legítimo bloqueado.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score, confusion_matrix, f1_score, precision_recall_curve, recall_score, roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold

from accessguard.engineering import IAMFeatureBuilder


def make_cv(n_splits: int = 5, seed: int = 42) -> StratifiedGroupKFold:
    """Validación cruzada estratificada por ACTION y agrupada por gerente (ningún gerente en dos pliegues)."""
    return StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)


def fold_matrices(X: pd.DataFrame, y: np.ndarray, groups, cv, seed: int = 42):
    """Calcula UNA vez las variables de cada pliegue (ajustadas solo con su entrenamiento).

    Es equivalente a meter el constructor dentro de un Pipeline por pliegue, pero evita repetirlo
    en cada ensayo de Optuna. Devuelve una lista de (X_tr, y_tr, X_va, y_va, idx_va).
    """
    folds = []
    for tr, va in cv.split(X, y, groups=groups):
        fb = IAMFeatureBuilder(seed=seed)
        X_tr = fb.fit_transform(X.iloc[tr], y[tr])
        X_va = fb.transform(X.iloc[va])
        folds.append((X_tr, y[tr], X_va, y[va], va))
    return folds


def expected_cost(y_true, p_approve, threshold: float, c_fp: float, c_fn: float) -> float:
    """Costo medio por solicitud. Se aprueba si p >= umbral."""
    pred = (np.asarray(p_approve) >= threshold).astype(int)
    y_true = np.asarray(y_true)
    fp = ((pred == 1) & (y_true == 0)).sum()
    fn = ((pred == 0) & (y_true == 1)).sum()
    return float((c_fp * fp + c_fn * fn) / len(y_true))


def best_threshold(y_true, p_approve, c_fp: float, c_fn: float, grid=None):
    """Umbral que minimiza el costo esperado. Devuelve (umbral, costo, tabla completa)."""
    grid = np.linspace(0.01, 0.99, 197) if grid is None else grid
    costs = np.array([expected_cost(y_true, p_approve, t, c_fp, c_fn) for t in grid])
    i = int(np.argmin(costs))
    return float(grid[i]), float(costs[i]), pd.DataFrame({"threshold": grid, "cost": costs})


def metrics_at(y_true, p_approve, threshold: float = 0.5) -> dict:
    """ROC-AUC, PR-AUC (ambas clases), F1 y recall por clase y matriz de confusión.

    La clase *denegar* (0) es la minoritaria (5,8 %): su PR-AUC es la métrica exigente.
    """
    y_true = np.asarray(y_true)
    p = np.asarray(p_approve)
    pred = (p >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    return {
        "roc_auc": roc_auc_score(y_true, p),
        "pr_auc_deny": average_precision_score(1 - y_true, 1 - p),
        "pr_auc_approve": average_precision_score(y_true, p),
        "f1_deny": f1_score(y_true, pred, pos_label=0, zero_division=0),
        "f1_approve": f1_score(y_true, pred, pos_label=1, zero_division=0),
        "recall_deny": recall_score(y_true, pred, pos_label=0, zero_division=0),
        "recall_approve": recall_score(y_true, pred, pos_label=1, zero_division=0),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def f1_curve(y_true, p_approve):
    """Curva precisión-recall de la clase *denegar* y el F1 en cada umbral (sobre p de aprobar)."""
    prec, rec, thr = precision_recall_curve(1 - np.asarray(y_true), 1 - np.asarray(p_approve))
    f1 = 2 * prec * rec / np.clip(prec + rec, 1e-12, None)
    return prec, rec, f1, thr


# --- Modelos candidatos y espacios de búsqueda ---------------------------------------------------
from catboost import CatBoostClassifier  # noqa: E402
from lightgbm import LGBMClassifier  # noqa: E402
from sklearn.ensemble import RandomForestClassifier  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402
from xgboost import XGBClassifier  # noqa: E402

MODEL_NAMES = ["LogReg L2 (baseline)", "LogReg ElasticNet", "Random Forest", "XGBoost", "LightGBM", "CatBoost"]


def build_model(name: str, params: dict | None = None, seed: int = 42):
    """Devuelve un estimador que recibe la matriz numérica de `IAMFeatureBuilder`."""
    p = dict(params or {})
    if name == "LogReg L2 (baseline)":
        return Pipeline([("scale", StandardScaler()), ("clf", LogisticRegression(
            C=p.get("C", 1.0), max_iter=2000, random_state=seed))])
    if name == "LogReg ElasticNet":
        return Pipeline([("scale", StandardScaler()), ("clf", LogisticRegression(
            solver="saga", l1_ratio=p.get("l1_ratio", 0.5), C=p.get("C", 1.0),
            max_iter=3000, random_state=seed))])
    if name == "Random Forest":
        return RandomForestClassifier(
            n_estimators=p.get("n_estimators", 300), max_depth=p.get("max_depth"),
            min_samples_leaf=p.get("min_samples_leaf", 5), max_features=p.get("max_features", "sqrt"),
            n_jobs=-1, random_state=seed)
    # Árboles con regularización estricta (valores por defecto del torneo): poca profundidad, tasa de
    # aprendizaje baja, submuestreo 0.7 y penalización L2 / mínimo de peso por hoja.
    if name == "XGBoost":
        return XGBClassifier(
            n_estimators=p.get("n_estimators", 400), learning_rate=p.get("learning_rate", 0.03),
            max_depth=p.get("max_depth", 4), subsample=p.get("subsample", 0.7),
            colsample_bytree=p.get("colsample_bytree", 0.7), min_child_weight=p.get("min_child_weight", 10),
            reg_lambda=p.get("reg_lambda", 10.0), tree_method="hist", n_jobs=-1, random_state=seed, verbosity=0)
    if name == "LightGBM":
        return LGBMClassifier(
            n_estimators=p.get("n_estimators", 400), learning_rate=p.get("learning_rate", 0.03),
            max_depth=p.get("max_depth", 4), num_leaves=p.get("num_leaves", 15),
            min_child_weight=p.get("min_child_weight", 5.0), min_child_samples=p.get("min_child_samples", 50),
            subsample=p.get("subsample", 0.7), subsample_freq=1, colsample_bytree=p.get("colsample_bytree", 0.7),
            reg_lambda=p.get("reg_lambda", 10.0), n_jobs=-1, random_state=seed, verbose=-1)
    if name == "CatBoost":
        return CatBoostClassifier(
            iterations=p.get("iterations", 500), learning_rate=p.get("learning_rate", 0.03),
            depth=p.get("depth", 4), l2_leaf_reg=p.get("l2_leaf_reg", 10.0),
            bootstrap_type="Bernoulli", subsample=p.get("subsample", 0.7), min_data_in_leaf=p.get("min_data_in_leaf", 20),
            random_strength=p.get("random_strength", 1.0), random_seed=seed, verbose=0, thread_count=-1,
            allow_writing_files=False)
    raise ValueError(f"modelo desconocido: {name}")


def suggest_params(trial, name: str) -> dict:
    """Espacio de búsqueda de Optuna: rangos acotados por conocimiento de cada algoritmo."""
    if name in ("LogReg L2 (baseline)", "LogReg ElasticNet"):
        p = {"C": trial.suggest_float("C", 1e-3, 10, log=True)}
        if name == "LogReg ElasticNet":
            p["l1_ratio"] = trial.suggest_float("l1_ratio", 0.05, 0.95)
        return p
    if name == "Random Forest":
        return {"n_estimators": trial.suggest_int("n_estimators", 200, 600, step=100),
                "max_depth": trial.suggest_int("max_depth", 6, 30),
                "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 30),
                "max_features": trial.suggest_float("max_features", 0.2, 0.9)}
    # Árboles regularizados: profundidad 3-5, tasa de aprendizaje 0.01-0.05, submuestreo fijo en 0.7
    if name == "XGBoost":
        return {"n_estimators": trial.suggest_int("n_estimators", 200, 800, step=100),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.05, log=True),
                "max_depth": trial.suggest_int("max_depth", 3, 5),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
                "min_child_weight": trial.suggest_int("min_child_weight", 5, 40),
                "reg_lambda": trial.suggest_float("reg_lambda", 1.0, 50, log=True)}
    if name == "LightGBM":
        return {"n_estimators": trial.suggest_int("n_estimators", 200, 800, step=100),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.05, log=True),
                "max_depth": trial.suggest_int("max_depth", 3, 5),
                "num_leaves": trial.suggest_int("num_leaves", 6, 24),
                "min_child_samples": trial.suggest_int("min_child_samples", 20, 150),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
                "reg_lambda": trial.suggest_float("reg_lambda", 1.0, 50, log=True)}
    if name == "CatBoost":
        return {"iterations": trial.suggest_int("iterations", 200, 800, step=100),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.05, log=True),
                "depth": trial.suggest_int("depth", 3, 5),
                "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 3.0, 50.0, log=True),
                "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 10, 100)}
    raise ValueError(name)


def build_pipeline(name: str, params: dict | None = None, seed: int = 42) -> Pipeline:
    """Pipeline completo (variables + modelo) para entrenar con el conjunto final y exportar."""
    return Pipeline([("features", IAMFeatureBuilder(seed=seed)), ("model", build_model(name, params, seed))])


# --- Política de triaje de 3 estados ---------------------------------------------------------------
def triage_decision(p_approve, t_low: float, t_high: float) -> np.ndarray:
    """2 = aprobar (p >= t_high), 1 = revisar (t_low <= p < t_high), 0 = denegar (p < t_low)."""
    p = np.asarray(p_approve)
    return np.where(p >= t_high, 2, np.where(p >= t_low, 1, 0))


def triage_cost(y_true, p_approve, t_low: float, t_high: float, c_fp: float, c_fn: float, c_review: float) -> float:
    """Costo operativo medio por solicitud.

    Aprobar: c_fp si era un acceso a denegar (FP), 0 si era legítimo. Revisar: c_review por caso (el analista
    resuelve bien). Denegar: c_fn si era un usuario legítimo (FN), 0 si era correcto.
    """
    y_true = np.asarray(y_true)
    d = triage_decision(p_approve, t_low, t_high)
    fp = ((d == 2) & (y_true == 0)).sum()
    fn = ((d == 0) & (y_true == 1)).sum()
    rev = (d == 1).sum()
    return float((c_fp * fp + c_fn * fn + c_review * rev) / len(y_true))


def triage_summary(y_true, p_approve, t_low: float, t_high: float, c_fp: float, c_fn: float, c_review: float) -> dict:
    """Costo y conteos de la política de 3 estados."""
    y_true = np.asarray(y_true)
    d = triage_decision(p_approve, t_low, t_high)
    return {
        "cost": triage_cost(y_true, p_approve, t_low, t_high, c_fp, c_fn, c_review),
        "pct_approve": float((d == 2).mean()), "pct_review": float((d == 1).mean()), "pct_deny": float((d == 0).mean()),
        "fp_auto_approve": int(((d == 2) & (y_true == 0)).sum()), "fn_auto_deny": int(((d == 0) & (y_true == 1)).sum()),
        "n_review": int((d == 1).sum()), "n": int(len(y_true)),
    }


def baseline_costs(y_true, c_fp: float, c_fn: float, c_review: float) -> dict:
    """Costo por solicitud de las políticas triviales (sin modelo)."""
    y_true = np.asarray(y_true)
    return {"aprobar todo": float(c_fp * (y_true == 0).mean()), "denegar todo": float(c_fn * (y_true == 1).mean()),
            "revisar todo": float(c_review)}


def triage_grid(y_true, p_approve, c_fp: float, c_fn: float, c_review: float, lows, highs) -> np.ndarray:
    """Costo por solicitud para todas las parejas (t_low, t_high) a la vez. Devuelve matriz [len(lows), len(highs)].

    Usa conteos acumulados sobre las probabilidades ordenadas, así que es rápido aunque la rejilla sea grande.
    Las parejas con t_low >= t_high quedan en NaN.
    """
    y_true = np.asarray(y_true)
    p = np.asarray(p_approve)
    p0 = np.sort(p[y_true == 0])   # probabilidades de los que había que denegar
    p1 = np.sort(p[y_true == 1])   # probabilidades de los legítimos
    n = len(y_true)
    lows, highs = np.asarray(lows), np.asarray(highs)
    fp = len(p0) - np.searchsorted(p0, highs, side="left")        # denegables con p >= t_high (se aprueban)
    fn = np.searchsorted(p1, lows, side="left")                    # legítimos con p < t_low (se deniegan)
    n_ge = lambda t: n - np.searchsorted(np.sort(p), t, side="left")
    review = n_ge(lows)[:, None] - n_ge(highs)[None, :]
    cost = (c_fp * fp[None, :] + c_fn * fn[:, None] + c_review * review) / n
    cost = np.where(lows[:, None] < highs[None, :], cost, np.nan)
    return cost


def predict_triage(bundle: dict, X: pd.DataFrame) -> pd.DataFrame:
    """Aplica un paquete exportado (pipeline + umbrales) y devuelve p_approve y la decisión de 3 estados."""
    p = bundle["pipeline"].predict_proba(X)[:, 1]
    labels = np.array(["denegar", "revisar", "aprobar"])
    return pd.DataFrame({"p_approve": p, "decision": labels[triage_decision(p, bundle["t_low"], bundle["t_high"])]}, index=X.index)
