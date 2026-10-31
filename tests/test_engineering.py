import numpy as np
import pandas as pd

from accessguard.engineering import BASE_COLS, IAMFeatureBuilder
from accessguard.modeling import best_threshold, expected_cost, metrics_at


def _toy(n=600, seed=0):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({c: rng.integers(0, 30, n) for c in BASE_COLS})
    df["MGR_ID"] = rng.integers(0, 80, n)
    y = (rng.random(n) < 0.9).astype(int)
    return df, y


def test_oof_target_encoding_does_not_see_own_label():
    # una categoría única por fila: con fuga, su TE sería igual a su etiqueta; fuera de pliegue vale el prior
    df, y = _toy()
    df["RESOURCE"] = np.arange(len(df))
    out = IAMFeatureBuilder().fit_transform(df, y)
    te = out["te__RESOURCE"].to_numpy()
    assert np.allclose(te, te[0], atol=0.05)           # todas ~ prior, ninguna copia su etiqueta
    assert abs(np.corrcoef(te, y)[0, 1]) < 0.2


def test_unseen_category_gets_zero_frequency_and_prior():
    df, y = _toy()
    fb = IAMFeatureBuilder().fit(df, y)
    new = df.head(3).copy()
    new["RESOURCE"] = 999_999
    out = fb.transform(new)
    assert (out["freq__RESOURCE"] == 0).all()
    assert np.allclose(out["te__RESOURCE"], fb.prior_)


def test_transform_has_same_columns_as_fit_transform():
    df, y = _toy()
    fb = IAMFeatureBuilder()
    a = fb.fit_transform(df, y)
    b = fb.transform(df)
    assert list(a.columns) == list(b.columns) and not a.isna().any().any()


def test_threshold_minimises_cost():
    y = np.array([1] * 90 + [0] * 10)
    p = np.r_[np.linspace(0.6, 0.99, 90), np.linspace(0.1, 0.7, 10)]
    t, c, _ = best_threshold(y, p, c_fp=2000, c_fn=40)
    assert c <= expected_cost(y, p, 0.5, 2000, 40)
    m = metrics_at(y, p, t)
    assert m["tn"] + m["fp"] + m["fn"] + m["tp"] == 100


def test_triage_cost_three_states():
    from accessguard.modeling import baseline_costs, triage_cost, triage_decision
    y = np.array([1, 1, 0, 0, 1, 0])
    p = np.array([0.99, 0.60, 0.95, 0.10, 0.05, 0.50])
    # t_low=0.2, t_high=0.9 -> aprobar: 0.99(TP), 0.95(FP); revisar: 0.60, 0.50; denegar: 0.10(TN), 0.05(FN)
    assert list(triage_decision(p, 0.2, 0.9)) == [2, 1, 2, 0, 0, 1]
    assert np.isclose(triage_cost(y, p, 0.2, 0.9, 500, 30, 6), (500 + 30 + 2 * 6) / 6)
    b = baseline_costs(y, 500, 30, 6)
    assert b["revisar todo"] == 6 and np.isclose(b["denegar todo"], 30 * 0.5)
    # con t_low=0 y t_high=1+ todo se revisa
    assert triage_cost(y, p, 0.0, 1.01, 500, 30, 6) == 6


def test_triage_grid_matches_triage_cost():
    from accessguard.modeling import triage_cost, triage_grid
    rng = np.random.default_rng(1)
    y = (rng.random(400) < 0.9).astype(int)
    p = np.clip(rng.normal(0.6 + 0.3 * y, 0.2), 0, 1)
    lows, highs = np.array([0.1, 0.3, 0.5]), np.array([0.6, 0.8, 0.95])
    g = triage_grid(y, p, 500, 30, 6, lows, highs)
    for i, lo in enumerate(lows):
        for j, hi in enumerate(highs):
            assert np.isclose(g[i, j], triage_cost(y, p, lo, hi, 500, 30, 6))


def test_security_metrics():
    from accessguard.security_metrics import (auto_approval_at_confidence, auto_approval_at_zero_fpr, fpr_upper_bound,
                                              precision_at_top, review_queue_stats)
    y = np.array([1] * 8 + [0] * 2)
    p = np.array([0.99, 0.97, 0.96, 0.9, 0.85, 0.6, 0.5, 0.4, 0.95, 0.3])
    z = auto_approval_at_zero_fpr(y, p)                 # mayor p entre los que había que denegar = 0.95
    assert z["threshold"] == 0.95 and z["n_approved"] == 3 and np.isclose(z["auto_approval_rate"], 0.3)
    c = auto_approval_at_confidence(y, p, 0.95)         # aprueba 0.99, 0.97, 0.96, 0.95 -> 1 FP
    assert c["n_approved"] == 4 and c["fp"] == 1 and np.isclose(c["precision"], 0.75)
    q = review_queue_stats(y, p, 0.95)
    assert np.isclose(q["review_rate"], 0.6) and np.isclose(q["share_of_denials_in_queue"], 0.5)
    assert precision_at_top(y, p, 0.2) == 1.0
    assert 0.0 < fpr_upper_bound(0, 1000) < 0.004       # regla de tres ≈ 0.003


def test_fp_budget_queue_and_predict_zero_trust():
    import pandas as pd
    from accessguard.security_metrics import auto_approval_at_fp_budget, auto_approval_at_zero_fpr, predict_zero_trust, queue_capture
    y = np.array([1] * 8 + [0] * 3)
    p = np.array([0.99, 0.97, 0.96, 0.9, 0.85, 0.6, 0.5, 0.4, 0.95, 0.3, 0.2])
    b0 = auto_approval_at_fp_budget(y, p, 0)
    assert b0["threshold"] == auto_approval_at_zero_fpr(y, p)["threshold"] == 0.95 and b0["fp"] == 0
    b1 = auto_approval_at_fp_budget(y, p, 1)           # tolera 1 FP: umbral = 2º indebido más alto (0.3)
    assert b1["threshold"] == 0.3 and b1["fp"] == 1 and b1["auto_approval_rate"] > b0["auto_approval_rate"]
    qc = queue_capture(y, p, 0.95, fractions=(0.5, 1.0))   # cola = 8 solicitudes; las denegaciones de p baja quedan primero
    assert qc["n_queue"] == 8 and qc["100%"] == 1.0 and abs(qc["50%"] - 2 / 3) < 1e-9

    class Dummy:                                        # pipeline mínimo con predict_proba
        def predict_proba(self, X):
            q = X["p"].to_numpy(); return np.c_[1 - q, q]
    X = pd.DataFrame({"p": p})
    out = predict_zero_trust({"pipeline": Dummy(), "t_auto_strict": 0.95}, X)
    assert (out["decision"] == "aprobar_auto").sum() == 3 and out["prioridad_revision"].dropna().min() == 1
