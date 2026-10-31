import numpy as np
import pandas as pd

from accessguard.stats import cramers_v


def test_cramers_v_identical_is_high_and_independent_is_low():
    rng = np.random.default_rng(0)
    a = pd.Series(rng.integers(0, 5, 2000))
    assert cramers_v(a, a * 10) > 0.95
    b = pd.Series(rng.integers(0, 5, 2000))
    assert cramers_v(a, b) < 0.1


def test_cramers_v_constant_column_is_zero():
    assert cramers_v(pd.Series([1] * 10), pd.Series(range(10))) == 0.0
