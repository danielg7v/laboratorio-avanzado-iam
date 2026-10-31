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
