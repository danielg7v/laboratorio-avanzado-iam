"""Pruebas de las zonas de decisión y utilidades de explicabilidad."""
import numpy as np
import pandas as pd
import pytest

from accessguard.explain import (ZONE_GREEN, ZONE_RED, ZONE_YELLOW, assign_zone, compute_t_low,
                                 expected_calibration_error, impact_table, zone_summary)


def test_assign_zone_boundaries():
    z = assign_zone([0.99, 0.98, 0.50, 0.30, 0.10], t_low=0.30, t_auto=0.98)
    assert list(z) == [ZONE_GREEN, ZONE_YELLOW, ZONE_YELLOW, ZONE_YELLOW, ZONE_RED]


def test_assign_zone_rejects_inverted_thresholds():
    with pytest.raises(ValueError):
        assign_zone([0.5], t_low=0.9, t_auto=0.5)


def test_compute_t_low_fraction():
    p = np.linspace(0, 1, 1001)
    t = compute_t_low(p, 0.10)
    assert (p < t).mean() == pytest.approx(0.10, abs=0.01)
    with pytest.raises(ValueError):
        compute_t_low(p, 0)


def test_zone_summary_counts_add_up():
    rng = np.random.default_rng(0)
    p = rng.uniform(size=500)
    y = (rng.uniform(size=500) < p).astype(int)
    s = zone_summary(y, p, 0.2, 0.9)
    assert s["n"].sum() == 500 and s["accesos indebidos"].sum() == (y == 0).sum()


def test_calibration_perfect_and_bad():
    p = np.array([0.05] * 100 + [0.95] * 100)
    y_ok = np.array([0] * 5 + [1] * 95 + [1] * 95 + [0] * 5)[:200]
    assert expected_calibration_error(np.r_[np.zeros(95), np.ones(5), np.zeros(5), np.ones(95)], p) == pytest.approx(0.0, abs=1e-9)
    assert expected_calibration_error(1 - np.r_[np.zeros(95), np.ones(5), np.zeros(5), np.ones(95)], p) > 0.8


def test_impact_table_sorted():
    v = pd.DataFrame({"a": [1.0, -1.0], "b": [0.1, 0.1]})
    t = impact_table(v)
    assert list(t.index) == ["a", "b"] and t["share"].sum() == pytest.approx(1.0)
