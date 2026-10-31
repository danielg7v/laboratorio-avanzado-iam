import pandas as pd

from accessguard.data import split_by_group


def _toy():
    rows = [{"MGR_ID": m, "ACTION": int((i + m) % 7 != 0)} for m in range(60) for i in range(5)]
    return pd.DataFrame(rows)


def test_no_group_in_both_partitions_and_no_row_lost():
    df = _toy()
    tr, ho = split_by_group(df, "MGR_ID", "ACTION", test_size=0.2, seed=42)
    assert set(tr.MGR_ID).isdisjoint(set(ho.MGR_ID))
    assert len(tr) + len(ho) == len(df)
    assert sorted(tr.index.tolist() + ho.index.tolist()) == sorted(df.index.tolist())


def test_split_is_reproducible():
    df = _toy()
    a = split_by_group(df, "MGR_ID", "ACTION", seed=7)[1].index
    b = split_by_group(df, "MGR_ID", "ACTION", seed=7)[1].index
    assert list(a) == list(b)


def test_row_split_would_leak():
    """Contraste: una partición por fila SÍ comparte gerentes (por eso existe la prueba de arriba)."""
    df = _toy()
    ho = df.sample(frac=0.2, random_state=0)
    tr = df.drop(ho.index)
    assert not set(tr.MGR_ID).isdisjoint(set(ho.MGR_ID))
