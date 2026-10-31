import pandas as pd

from accessguard.data import check_schema, drop_redundant, find_redundant_pairs


def test_redundant_pair_detected_and_dropped():
    df = pd.DataFrame({"ROLE_TITLE": [1, 1, 2, 3], "ROLE_CODE": [10, 10, 20, 30], "X": [1, 2, 3, 4]})
    assert ("ROLE_TITLE", "ROLE_CODE") in find_redundant_pairs(df, ["ROLE_TITLE", "ROLE_CODE", "X"])
    out = drop_redundant(df)
    assert "ROLE_CODE" not in out.columns and "ROLE_CODE" in df.columns


def test_non_redundant_pair_not_flagged():
    df = pd.DataFrame({"A": [1, 1, 2], "B": [1, 2, 3]})
    assert find_redundant_pairs(df, ["A", "B"]) == []


def test_check_schema_reports_missing():
    assert check_schema(pd.DataFrame({"A": [1]}), ["A", "B"]) == ["B"]
