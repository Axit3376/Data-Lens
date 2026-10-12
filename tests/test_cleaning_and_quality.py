import pytest
import pandas as pd
import numpy as np

from services.quality_score_service import (
    calculate_completeness,
    calculate_validity,
    calculate_uniqueness,
    calculate_consistency,
    compute_quality_score,
    DEFAULT_WEIGHTS
)
from services.cleaning_service import (
    detect_cleaning_recommendations,
    execute_cleaning_plan
)


def test_quality_score_perfect_dataset():
    df = pd.DataFrame({
        "age": [20, 25, 30, 35],
        "name": ["Alice", "Bob", "Charlie", "David"],
        "salary": [50000.0, 60000.0, 70000.0, 80000.0]
    })
    result = compute_quality_score(df)
    assert result["overall_score"] == 100.0
    assert result["rating"] == "Excellent"
    assert result["dimensions"]["completeness"]["score"] == 100.0
    assert result["dimensions"]["validity"]["score"] == 100.0
    assert result["dimensions"]["uniqueness"]["score"] == 100.0
    assert result["dimensions"]["consistency"]["score"] == 100.0


def test_quality_score_missing_values():
    df = pd.DataFrame({
        "a": [1, np.nan, 3, 4],
        "b": [1, 2, np.nan, np.nan]
    })
    # Total cells: 8. Missing: 3. Non-missing: 5. 5/8 = 62.5%
    comp = calculate_completeness(df)
    assert comp["score"] == 62.5
    assert comp["affected_cells"] == 3
    assert "contains_missing_values" in comp["checks_failed"]


def test_quality_score_duplicates():
    df = pd.DataFrame({
        "a": [1, 1, 2, 3],
        "b": [10, 10, 20, 30]
    })
    uniq = calculate_uniqueness(df)
    assert uniq["duplicate_rows"] == 1
    assert uniq["score"] == 75.0


def test_quality_score_empty_dataset():
    df = pd.DataFrame()
    result = compute_quality_score(df)
    assert result["overall_score"] is None
    assert result["rating"] == "Unavailable"
    assert result["dimensions"]["completeness"]["status"] == "unavailable"


def test_consistency_whitespace_and_casing():
    df = pd.DataFrame({
        "city": ["Pune ", "pune", "Mumbai", "delhi", "Delhi"]
    })
    cons = calculate_consistency(df)
    assert "whitespace_in_city" in cons["checks_failed"]
    assert "casing_inconsistency_in_city" in cons["checks_failed"]
    assert cons["score"] < 100.0


def test_cleaning_recommendations_generation():
    df = pd.DataFrame({
        "age": [25.0, np.nan, 30.0, 150.0, 28.0, 29.0, 31.0],  # missing and potential outlier
        "city": [" Pune", "pune", "Delhi", "Delhi", "Mumbai", "Goa", "Pune"],
        "mixed_num": ["10", "20", "invalid", "40", "50", "60", "70"]
    })
    recs = detect_cleaning_recommendations(df)
    rec_types = [r["issue_type"] for r in recs]
    assert "missing_values" in rec_types
    assert "whitespace" in rec_types
    assert "casing_inconsistency" in rec_types


def test_execute_cleaning_plan_imputation():
    df = pd.DataFrame({
        "num": [10.0, np.nan, 30.0],
        "cat": ["A", np.nan, "A"]
    })
    df_orig = df.copy()
    
    operations = [
        {"action": "impute_median", "column": "num"},
        {"action": "impute_mode", "column": "cat"}
    ]
    df_cleaned, summary = execute_cleaning_plan(df, operations)

    # Verify original is not mutated
    assert df_orig["num"].isna().sum() == 1
    assert df_orig["cat"].isna().sum() == 1

    # Verify cleaned results
    assert df_cleaned["num"].isna().sum() == 0
    assert df_cleaned["num"].iloc[1] == 20.0  # median of 10 and 30
    assert df_cleaned["cat"].iloc[1] == "A"
    assert summary["changed_cells"] == 2


def test_execute_cleaning_plan_duplicates_and_clipping():
    df = pd.DataFrame({
        "val": [1, 2, 2, 100]
    })
    operations = [
        {"action": "remove_duplicates"},
        {"action": "cap_outliers", "column": "val", "parameters": {"lower_bound": 0, "upper_bound": 10}}
    ]
    df_cleaned, summary = execute_cleaning_plan(df, operations)
    assert len(df_cleaned) == 3
    assert df_cleaned["val"].max() == 10
    assert summary["rows_removed"] == 1


def test_execute_cleaning_plan_whitespace_and_casing():
    df = pd.DataFrame({
        "city": [" New York ", "chicago", "CHICAGO"]
    })
    operations = [
        {"action": "trim_whitespace", "column": "city"},
        {"action": "standardize_casing", "column": "city", "parameters": {"case_style": "title"}}
    ]
    df_cleaned, summary = execute_cleaning_plan(df, operations)
    assert df_cleaned["city"].tolist() == ["New York", "Chicago", "Chicago"]
