import numpy as np
import pandas as pd

from accessguard.features import FrequencyEncoder, build_preprocessor


def test_frequency_encoder_unseen_is_zero():
    enc = FrequencyEncoder().fit(pd.DataFrame({"A": [1, 1, 2]}))
    out = enc.transform(pd.DataFrame({"A": [1, 2, 99]}))
    assert out[2, 0] == 0 and out[0, 0] > out[1, 0]


def test_preprocessor_handles_unseen_and_nulls():
    rng = np.random.default_rng(0)
    X = pd.DataFrame({"RESOURCE": rng.integers(0, 5, 200), "ROLE_TITLE": rng.integers(0, 3, 200)})
    y = pd.Series(rng.integers(0, 2, 200))
    pre = build_preprocessor(low_card=["ROLE_TITLE"], high_card=["RESOURCE"]).fit(X, y)
    new = pd.DataFrame({"RESOURCE": [999, np.nan], "ROLE_TITLE": [77, np.nan]})
    out = pre.transform(new)
    assert out.shape[0] == 2 and np.isfinite(np.asarray(out)).all()


def test_nan_in_batch_does_not_change_other_rows():
    """Un vacío vuelve float a toda la columna; los códigos de las demás filas deben seguir reconociéndose."""
    rng = np.random.default_rng(1)
    X = pd.DataFrame({"RESOURCE": rng.integers(0, 5, 300), "ROLE_TITLE": rng.integers(0, 3, 300)})
    y = pd.Series(rng.integers(0, 2, 300))
    pre = build_preprocessor(low_card=["ROLE_TITLE"], high_card=["RESOURCE"]).fit(X, y)
    clean = X.head(4).copy()
    dirty = clean.copy().astype(float)
    dirty.iloc[0, :] = np.nan
    a, b = np.asarray(pre.transform(clean)), np.asarray(pre.transform(dirty))
    assert np.allclose(a[1:], b[1:])
