import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional


DEFAULT_WEIGHTS = {
    "completeness": 0.35,
    "validity": 0.30,
    "uniqueness": 0.20,
    "consistency": 0.15
}


def calculate_completeness(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Measures the proportion of expected data cells that contain valid, non-missing values.
    Completeness = 100 * non_missing_cells / total_cells
    """
    total_cells = df.size
    if total_cells == 0 or len(df.columns) == 0:
        return {
            "score": None,
            "status": "unavailable",
            "reason": "Dataset has 0 cells or 0 columns",
            "checks_performed": ["non_missing_cell_ratio"],
            "checks_failed": [],
            "affected_cells": 0,
            "total_cells": 0,
            "missing_per_column": {},
            "recommendations": []
        }

    missing_series = df.isna().sum()
    missing_cells = int(missing_series.sum())
    non_missing_cells = total_cells - missing_cells
    score = round(float((non_missing_cells / total_cells) * 100), 2)

    affected_cols = missing_series[missing_series > 0].to_dict()
    checks_failed = ["contains_missing_values"] if missing_cells > 0 else []
    
    recommendations = []
    for col, count in affected_cols.items():
        pct = round(float((count / len(df)) * 100), 2)
        if pct == 100.0:
            recommendations.append(f"Column '{col}' is entirely empty (100% missing). Consider dropping it.")
        elif pd.api.types.is_numeric_dtype(df[col]):
            recommendations.append(f"Impute {count} ({pct}%) missing values in numerical column '{col}' with median or mean.")
        else:
            recommendations.append(f"Impute {count} ({pct}%) missing values in categorical column '{col}' with mode or 'Missing'.")

    return {
        "score": score,
        "status": "available",
        "reason": None,
        "checks_performed": ["non_missing_cell_ratio"],
        "checks_failed": checks_failed,
        "affected_cells": missing_cells,
        "total_cells": total_cells,
        "missing_per_column": {k: int(v) for k, v in affected_cols.items()},
        "recommendations": recommendations
    }


def calculate_validity(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Measures compliance with explicitly verifiable type/parsing validity.
    Checks:
    - Object/string columns that appear to be numerical or datetime but have parse failures or mixed types.
    - Infinite values in numerical columns.
    """
    total_cells = df.size
    if total_cells == 0 or len(df.columns) == 0:
        return {
            "score": None,
            "status": "unavailable",
            "reason": "Dataset has 0 cells or 0 columns",
            "checks_performed": ["type_convertibility", "infinite_values_check"],
            "checks_failed": [],
            "affected_cells": 0,
            "recommendations": []
        }

    checks_performed = ["type_convertibility", "infinite_values_check"]
    checks_failed = []
    affected_cells = 0
    recommendations = []

    # 1. Check for infinite values in numerical columns
    num_cols = df.select_dtypes(include=np.number).columns
    inf_cols = {}
    for col in num_cols:
        inf_count = int(np.isinf(df[col]).sum())
        if inf_count > 0:
            inf_cols[col] = inf_count
            affected_cells += inf_count
            checks_failed.append(f"infinite_values_in_{col}")
            recommendations.append(f"Column '{col}' contains {inf_count} infinite values. Cap or replace with NaN.")

    # 2. Check for object columns that are predominantly convertible to numeric or date
    obj_cols = df.select_dtypes(include=["object", "string", "str"]).columns
    for col in obj_cols:
        series_clean = df[col].dropna().astype(str).str.strip()
        if len(series_clean) == 0:
            continue
        
        # Test numeric convertibility
        numeric_converted = pd.to_numeric(series_clean, errors="coerce")
        num_valid = numeric_converted.notna().sum()
        num_invalid = len(series_clean) - num_valid
        
        # If >= 70% convertible to numeric and has invalid non-numeric entries, flag as validity issue
        if num_valid > 0 and (num_valid / len(series_clean)) >= 0.70 and num_invalid > 0:
            affected_cells += int(num_invalid)
            checks_failed.append(f"invalid_numeric_values_in_{col}")
            recommendations.append(
                f"Column '{col}' has {num_invalid} values ({round(num_invalid/len(df)*100, 1)}%) failing numeric format. Safe conversion or correction recommended."
            )

    # Score is proportion of valid cells out of total cells
    score = round(max(0.0, float(((total_cells - affected_cells) / total_cells) * 100)), 2)
    return {
        "score": score,
        "status": "available",
        "reason": None,
        "checks_performed": checks_performed,
        "checks_failed": checks_failed,
        "affected_cells": affected_cells,
        "recommendations": recommendations
    }


def calculate_uniqueness(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Measures exact duplicate rows.
    Uniqueness = 100 * (1 - duplicate_rows / total_rows)
    """
    total_rows = len(df)
    if total_rows == 0:
        return {
            "score": None,
            "status": "unavailable",
            "reason": "Dataset has 0 rows",
            "checks_performed": ["exact_duplicate_rows"],
            "checks_failed": [],
            "duplicate_rows": 0,
            "recommendations": []
        }

    duplicate_rows = int(df.duplicated().sum())
    score = round(float(((total_rows - duplicate_rows) / total_rows) * 100), 2)
    checks_failed = ["has_exact_duplicate_rows"] if duplicate_rows > 0 else []
    recommendations = []
    if duplicate_rows > 0:
        recommendations.append(f"Remove {duplicate_rows} exact duplicate rows to avoid data redundancy.")

    return {
        "score": score,
        "status": "available",
        "reason": None,
        "checks_performed": ["exact_duplicate_rows"],
        "checks_failed": checks_failed,
        "duplicate_rows": duplicate_rows,
        "recommendations": recommendations
    }


def calculate_consistency(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Measures detectable consistency violations:
    - Leading / trailing whitespace in string columns.
    - Casing inconsistencies (same trimmed string differing only in letter case).
    """
    total_rows = len(df)
    if total_rows == 0 or len(df.columns) == 0:
        return {
            "score": None,
            "status": "unavailable",
            "reason": "Dataset has 0 rows or 0 columns",
            "checks_performed": ["whitespace_inconsistency", "casing_inconsistency"],
            "checks_failed": [],
            "affected_cells": 0,
            "recommendations": []
        }

    checks_performed = ["whitespace_inconsistency", "casing_inconsistency"]
    checks_failed = []
    affected_cells = 0
    recommendations = []

    str_cols = df.select_dtypes(include=["object", "string", "str"]).columns
    total_eval_cells = 0

    for col in str_cols:
        series = df[col].dropna().astype(str)
        if len(series) == 0:
            continue
        total_eval_cells += len(series)

        # 1. Whitespace check
        has_whitespace = series.apply(lambda s: s != s.strip())
        whitespace_count = int(has_whitespace.sum())
        if whitespace_count > 0:
            affected_cells += whitespace_count
            checks_failed.append(f"whitespace_in_{col}")
            recommendations.append(f"Column '{col}' has {whitespace_count} values with leading/trailing whitespace. Normalize whitespace.")

        # 2. Casing check
        trimmed = series.str.strip()
        lower_counts = trimmed.str.lower().value_counts()
        # Find cases where a lower-cased value maps to multiple distinct original casings
        inconsistent_casing_values = 0
        for val_lower, freq in lower_counts.items():
            if freq > 1:
                original_variants = trimmed[trimmed.str.lower() == val_lower].unique()
                if len(original_variants) > 1:
                    # Mixed casing found (e.g. Pune vs pune)
                    inconsistent_casing_values += freq

        if inconsistent_casing_values > 0:
            affected_cells += inconsistent_casing_values
            checks_failed.append(f"casing_inconsistency_in_{col}")
            recommendations.append(f"Column '{col}' has {inconsistent_casing_values} values with inconsistent letter casing (e.g., Pune vs pune).")

    denom = max(1, total_eval_cells) if total_eval_cells > 0 else df.size
    score = round(max(0.0, float(((denom - min(denom, affected_cells)) / denom) * 100)), 2)

    return {
        "score": score,
        "status": "available",
        "reason": None,
        "checks_performed": checks_performed,
        "checks_failed": checks_failed,
        "affected_cells": affected_cells,
        "recommendations": recommendations
    }


def compute_quality_score(df: pd.DataFrame, custom_weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """
    Computes overall score from completeness, validity, uniqueness, and consistency dimensions.
    """
    weights = custom_weights or DEFAULT_WEIGHTS.copy()
    
    comp_res = calculate_completeness(df)
    valid_res = calculate_validity(df)
    uniq_res = calculate_uniqueness(df)
    cons_res = calculate_consistency(df)

    dimensions = {
        "completeness": comp_res,
        "validity": valid_res,
        "uniqueness": uniq_res,
        "consistency": cons_res
    }

    weighted_sum = 0.0
    sum_weights = 0.0

    for dim_name, dim_data in dimensions.items():
        weight = weights.get(dim_name, 0.0)
        if dim_data["status"] == "available" and dim_data["score"] is not None:
            weighted_sum += dim_data["score"] * weight
            sum_weights += weight

    if sum_weights > 0:
        overall_score = round(weighted_sum / sum_weights, 2)
    else:
        overall_score = None

    # Rating interpretation
    if overall_score is None:
        rating = "Unavailable"
        rating_color = "var(--text-muted)"
    elif overall_score >= 90:
        rating = "Excellent"
        rating_color = "var(--success-text)"
    elif overall_score >= 80:
        rating = "Good"
        rating_color = "var(--primary-color)"
    elif overall_score >= 60:
        rating = "Needs Improvement"
        rating_color = "var(--warning-text)"
    else:
        rating = "Poor"
        rating_color = "var(--danger-text)"

    # Consolidated key issues
    all_recommendations = []
    for dim_name, dim_data in dimensions.items():
        for rec in dim_data.get("recommendations", []):
            all_recommendations.append({
                "dimension": dim_name,
                "message": rec
            })

    return {
        "overall_score": overall_score,
        "rating": rating,
        "rating_color": rating_color,
        "weights": weights,
        "dimensions": dimensions,
        "key_recommendations": all_recommendations
    }
