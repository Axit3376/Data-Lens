import uuid
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

from services.quality_service import (
    get_missing_values,
    get_duplicate_rows,
    get_constant_columns,
    outlier_detection,
    get_high_cardinality_columns,
    analyze_quality
)
from services.quality_score_service import compute_quality_score


# -------------------------------------------------------------------------
# 1. ISSUE DETECTION & RECOMMENDATION ENGINE
# -------------------------------------------------------------------------

def detect_cleaning_recommendations(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Deterministic rule-based recommendation engine for cleaning opportunities.
    Returns structured recommendations with unique IDs, affected rows/cells,
    severity, suggested actions, rationale, parameters, and loss warnings.
    """
    recommendations = []
    total_rows = len(df)
    
    # ------------------ A. Missing Values ------------------
    if total_rows > 0:
        missing_counts = df.isnull().sum()
        for col in df.columns:
            m_count = int(missing_counts[col])
            if m_count > 0:
                pct = round(float((m_count / total_rows) * 100), 2)
                is_num = pd.api.types.is_numeric_dtype(df[col])
                
                if pct == 100.0:
                    severity = "high"
                    action = "drop_column"
                    strategy = "drop_column"
                    rationale = f"Column '{col}' has 100% missing values and carries no useful information."
                    loss_warning = "Dropping this column will completely remove it from the dataset."
                elif is_num:
                    severity = "high" if pct > 40 else ("medium" if pct > 10 else "low")
                    action = "impute_median"
                    strategy = "median"
                    rationale = f"Numerical column '{col}' has {m_count} missing entries ({pct}%). Median imputation preserves distribution without sensitivity to outliers."
                    loss_warning = "Imputation substitutes synthetic estimates for absent observations."
                else:
                    severity = "high" if pct > 40 else ("medium" if pct > 10 else "low")
                    action = "impute_mode"
                    strategy = "mode"
                    rationale = f"Categorical column '{col}' has {m_count} missing entries ({pct}%). Mode imputation fills with the most frequent value."
                    loss_warning = "Mode imputation may artificially inflate the prominence of the dominant category."

                recommendations.append({
                    "id": f"rec_missing_{col}",
                    "issue_type": "missing_values",
                    "column": col,
                    "severity": severity,
                    "affected_count": m_count,
                    "affected_percent": pct,
                    "proposed_action": action,
                    "rationale": rationale,
                    "parameters": {
                        "strategy": strategy,
                        "fill_value": None
                    },
                    "warning": loss_warning,
                    "allowed_actions": [
                        {"action": "impute_median", "label": "Impute with Median (Numerical)"} if is_num else {"action": "impute_mode", "label": "Impute with Mode (Most Frequent)"},
                        {"action": "impute_mean", "label": "Impute with Mean (Numerical)"} if is_num else {"action": "impute_constant", "label": "Replace with 'Missing' category"},
                        {"action": "drop_rows_missing", "label": "Drop Rows with Missing in this Column"},
                        {"action": "drop_column", "label": "Drop Column"}
                    ]
                })

    # ------------------ B. Duplicate Rows ------------------
    if total_rows > 0:
        dup_count = int(df.duplicated().sum())
        if dup_count > 0:
            dup_pct = round(float((dup_count / total_rows) * 100), 2)
            recommendations.append({
                "id": "rec_duplicate_rows",
                "issue_type": "duplicate_rows",
                "column": None,
                "severity": "high" if dup_pct > 5 else "medium",
                "affected_count": dup_count,
                "affected_percent": dup_pct,
                "proposed_action": "remove_duplicates",
                "rationale": f"Dataset contains {dup_count} exact duplicate records ({dup_pct}%). Removing duplicates avoids biased statistical weightings.",
                "parameters": {"keep": "first"},
                "warning": f"Will permanently remove {dup_count} duplicate rows, leaving {total_rows - dup_count} rows.",
                "allowed_actions": [
                    {"action": "remove_duplicates", "label": "Remove Exact Duplicate Rows"},
                    {"action": "keep_duplicates", "label": "Keep Duplicates (No Action)"}
                ]
            })

    # ------------------ C. Outliers (IQR Method) ------------------
    if total_rows > 3:
        num_cols = df.select_dtypes(include=np.number).columns
        for col in num_cols:
            series = df[col].dropna()
            if len(series) < 4 or series.nunique() <= 2:
                continue
            
            q1 = float(series.quantile(0.25))
            q3 = float(series.quantile(0.75))
            iqr = q3 - q1
            if iqr <= 0:
                continue
                
            lower_bound = round(q1 - 1.5 * iqr, 4)
            upper_bound = round(q3 + 1.5 * iqr, 4)
            outliers_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
            outlier_count = int(outliers_mask.sum())
            
            if outlier_count > 0:
                pct = round(float((outlier_count / total_rows) * 100), 2)
                severity = "high" if pct > 15 else ("medium" if pct > 5 else "low")
                recommendations.append({
                    "id": f"rec_outliers_{col}",
                    "issue_type": "outliers",
                    "column": col,
                    "severity": severity,
                    "affected_count": outlier_count,
                    "affected_percent": pct,
                    "proposed_action": "cap_outliers",
                    "rationale": f"Column '{col}' has {outlier_count} values outside IQR bounds [{lower_bound}, {upper_bound}]. Capping preserves sample size without extreme skew.",
                    "parameters": {
                        "lower_bound": lower_bound,
                        "upper_bound": upper_bound,
                        "method": "iqr"
                    },
                    "warning": "Capping compresses extremes to the lower/upper thresholds.",
                    "allowed_actions": [
                        {"action": "cap_outliers", "label": f"Cap Values to [{lower_bound}, {upper_bound}]"},
                        {"action": "drop_outlier_rows", "label": f"Drop {outlier_count} Outlier Rows"},
                        {"action": "keep_outliers", "label": "Keep Outliers Unchanged"}
                    ]
                })

    # ------------------ D. Inconsistent Categorical Values ------------------
    str_cols = df.select_dtypes(include=["object", "string", "str"]).columns
    for col in str_cols:
        series = df[col].dropna().astype(str)
        if len(series) == 0:
            continue
            
        # Whitespace check
        has_ws = series.apply(lambda s: s != s.strip())
        ws_count = int(has_ws.sum())
        if ws_count > 0:
            ws_pct = round(float((ws_count / total_rows) * 100), 2)
            recommendations.append({
                "id": f"rec_whitespace_{col}",
                "issue_type": "whitespace",
                "column": col,
                "severity": "low",
                "affected_count": ws_count,
                "affected_percent": ws_pct,
                "proposed_action": "trim_whitespace",
                "rationale": f"Column '{col}' has {ws_count} values with leading or trailing whitespace.",
                "parameters": {"strip": True},
                "warning": "None. Pure string cleanup.",
                "allowed_actions": [
                    {"action": "trim_whitespace", "label": "Trim Leading and Trailing Whitespace"}
                ]
            })

        # Casing inconsistency check
        trimmed = series.str.strip()
        lower_map = {}
        for original in trimmed.unique():
            low = original.lower()
            if low not in lower_map:
                lower_map[low] = set()
            lower_map[low].add(original)
            
        inconsistent_groups = {k: sorted(list(v)) for k, v in lower_map.items() if len(v) > 1}
        if inconsistent_groups:
            affected_casing_count = int(trimmed.apply(lambda s: s.lower() in inconsistent_groups).sum())
            recommendations.append({
                "id": f"rec_casing_{col}",
                "issue_type": "casing_inconsistency",
                "column": col,
                "severity": "medium",
                "affected_count": affected_casing_count,
                "affected_percent": round(float((affected_casing_count / total_rows) * 100), 2),
                "proposed_action": "standardize_casing",
                "rationale": f"Column '{col}' has mixed casing for identical values (e.g. {list(inconsistent_groups.values())[0]}).",
                "parameters": {
                    "case_style": "title",  # title, lower, upper
                    "groups": inconsistent_groups
                },
                "warning": "Normalizing casing changes text representations across the column.",
                "allowed_actions": [
                    {"action": "standardize_casing", "label": "Convert to Title Case"},
                    {"action": "standardize_lowercase", "label": "Convert to Lowercase"},
                    {"action": "standardize_uppercase", "label": "Convert to Uppercase"}
                ]
            })

    # ------------------ E. Data Type Issues ------------------
    for col in str_cols:
        series_clean = df[col].dropna().astype(str).str.strip()
        if len(series_clean) == 0:
            continue
        
        # Test numeric conversion
        num_conv = pd.to_numeric(series_clean, errors="coerce")
        num_valid = num_conv.notna().sum()
        num_invalid = len(series_clean) - num_valid
        
        # If high proportion convertible but currently stored as object
        if num_valid > 0 and (num_valid / len(series_clean)) >= 0.80 and num_invalid > 0:
            recommendations.append({
                "id": f"rec_type_num_{col}",
                "issue_type": "type_conversion",
                "column": col,
                "severity": "medium",
                "affected_count": int(num_invalid),
                "affected_percent": round(float((num_invalid / total_rows) * 100), 2),
                "proposed_action": "convert_to_numeric",
                "rationale": f"Column '{col}' is {round(num_valid/len(series_clean)*100, 1)}% numeric but formatted as text, with {num_invalid} unparseable entries.",
                "parameters": {"target_type": "numeric", "errors": "coerce"},
                "warning": f"Converting will coerce {num_invalid} invalid text values into NaN.",
                "allowed_actions": [
                    {"action": "convert_to_numeric", "label": "Convert to Numeric (Coerce invalid to NaN)"}
                ]
            })
            
    return recommendations


# -------------------------------------------------------------------------
# 2. CLEANING OPERATIONS EXECUTION ENGINE
# -------------------------------------------------------------------------

def execute_cleaning_plan(df_original: pd.DataFrame, operations: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Executes a list of operations on a copy of df_original.
    Returns:
        (df_cleaned, execution_summary)
    Does NOT mutate df_original.
    """
    df = df_original.copy(deep=True)
    initial_rows = len(df)
    initial_cols = len(df.columns)
    initial_missing = int(df.isna().sum().sum())
    initial_duplicates = int(df.duplicated().sum())

    changed_cells_count = 0
    rows_removed_total = 0
    operations_executed = []
    skipped_operations = []
    representative_samples = []

    for op in operations:
        action = op.get("action")
        col = op.get("column")
        params = op.get("parameters", {})

        # Validation
        if col and col not in df.columns and action not in ["remove_duplicates", "keep_duplicates"]:
            skipped_operations.append({
                "operation": op,
                "reason": f"Column '{col}' does not exist in dataset."
            })
            continue

        try:
            if action == "impute_median":
                if not pd.api.types.is_numeric_dtype(df[col]):
                    raise ValueError(f"Median imputation requires numeric column, got {df[col].dtype}")
                median_val = float(df[col].median()) if not df[col].dropna().empty else 0.0
                mask = df[col].isna()
                affected = int(mask.sum())
                if affected > 0:
                    sample_indices = df[mask].index[:5].tolist()
                    df[col] = df[col].fillna(median_val)
                    changed_cells_count += affected
                    operations_executed.append(f"Imputed {affected} missing values in '{col}' with median ({median_val})")
                    representative_samples.append({
                        "column": col,
                        "change_type": "imputation",
                        "indices": sample_indices,
                        "original_val": "NaN",
                        "new_val": median_val,
                        "count": affected
                    })

            elif action == "impute_mean":
                if not pd.api.types.is_numeric_dtype(df[col]):
                    raise ValueError(f"Mean imputation requires numeric column, got {df[col].dtype}")
                mean_val = float(round(df[col].mean(), 4)) if not df[col].dropna().empty else 0.0
                mask = df[col].isna()
                affected = int(mask.sum())
                if affected > 0:
                    sample_indices = df[mask].index[:5].tolist()
                    df[col] = df[col].fillna(mean_val)
                    changed_cells_count += affected
                    operations_executed.append(f"Imputed {affected} missing values in '{col}' with mean ({mean_val})")
                    representative_samples.append({
                        "column": col,
                        "change_type": "imputation",
                        "indices": sample_indices,
                        "original_val": "NaN",
                        "new_val": mean_val,
                        "count": affected
                    })

            elif action == "impute_mode":
                mode_series = df[col].mode()
                mode_val = mode_series.iloc[0] if not mode_series.empty else "Missing"
                mask = df[col].isna()
                affected = int(mask.sum())
                if affected > 0:
                    sample_indices = df[mask].index[:5].tolist()
                    df[col] = df[col].fillna(mode_val)
                    changed_cells_count += affected
                    operations_executed.append(f"Imputed {affected} missing values in '{col}' with mode ('{mode_val}')")
                    representative_samples.append({
                        "column": col,
                        "change_type": "imputation",
                        "indices": sample_indices,
                        "original_val": "NaN",
                        "new_val": str(mode_val),
                        "count": affected
                    })

            elif action == "impute_constant":
                fill_val = params.get("fill_value", "Missing")
                mask = df[col].isna()
                affected = int(mask.sum())
                if affected > 0:
                    sample_indices = df[mask].index[:5].tolist()
                    df[col] = df[col].fillna(fill_val)
                    changed_cells_count += affected
                    operations_executed.append(f"Replaced {affected} missing values in '{col}' with '{fill_val}'")
                    representative_samples.append({
                        "column": col,
                        "change_type": "imputation",
                        "indices": sample_indices,
                        "original_val": "NaN",
                        "new_val": str(fill_val),
                        "count": affected
                    })

            elif action == "drop_rows_missing":
                missing_mask = df[col].isna()
                affected_rows = int(missing_mask.sum())
                if affected_rows > 0:
                    df = df[~missing_mask].copy()
                    rows_removed_total += affected_rows
                    operations_executed.append(f"Dropped {affected_rows} rows with missing values in '{col}'")
                    representative_samples.append({
                        "column": col,
                        "change_type": "row_removal",
                        "count": affected_rows,
                        "description": f"Removed {affected_rows} rows missing '{col}'"
                    })

            elif action == "drop_column":
                df = df.drop(columns=[col])
                operations_executed.append(f"Dropped column '{col}'")
                representative_samples.append({
                    "column": col,
                    "change_type": "column_removal",
                    "description": f"Dropped column '{col}' entirely"
                })

            elif action == "remove_duplicates":
                dup_mask = df.duplicated()
                dup_rows = int(dup_mask.sum())
                if dup_rows > 0:
                    df = df.drop_duplicates(keep=params.get("keep", "first")).copy()
                    rows_removed_total += dup_rows
                    operations_executed.append(f"Removed {dup_rows} exact duplicate rows")
                    representative_samples.append({
                        "column": "ALL",
                        "change_type": "row_removal",
                        "count": dup_rows,
                        "description": f"Removed {dup_rows} exact duplicate rows"
                    })

            elif action == "cap_outliers":
                if not pd.api.types.is_numeric_dtype(df[col]):
                    raise ValueError(f"Outlier capping requires numeric column, got {df[col].dtype}")
                lower = params.get("lower_bound")
                upper = params.get("upper_bound")
                if lower is None or upper is None:
                    # Calculate IQR bounds dynamically if not provided
                    q1 = float(df[col].quantile(0.25))
                    q3 = float(df[col].quantile(0.75))
                    iqr = q3 - q1
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr

                lower_mask = df[col] < lower
                upper_mask = df[col] > upper
                capped_count = int(lower_mask.sum() + upper_mask.sum())
                if capped_count > 0:
                    df[col] = df[col].clip(lower=lower, upper=upper)
                    changed_cells_count += capped_count
                    operations_executed.append(f"Capped {capped_count} outliers in '{col}' to range [{lower}, {upper}]")
                    representative_samples.append({
                        "column": col,
                        "change_type": "clipping",
                        "count": capped_count,
                        "bounds": [lower, upper]
                    })

            elif action == "drop_outlier_rows":
                if not pd.api.types.is_numeric_dtype(df[col]):
                    raise ValueError(f"Outlier row dropping requires numeric column, got {df[col].dtype}")
                lower = params.get("lower_bound")
                upper = params.get("upper_bound")
                if lower is None or upper is None:
                    q1 = float(df[col].quantile(0.25))
                    q3 = float(df[col].quantile(0.75))
                    iqr = q3 - q1
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                
                outlier_mask = (df[col] < lower) | (df[col] > upper)
                outlier_count = int(outlier_mask.sum())
                if outlier_count > 0:
                    df = df[~outlier_mask].copy()
                    rows_removed_total += outlier_count
                    operations_executed.append(f"Dropped {outlier_count} outlier rows in '{col}'")
                    representative_samples.append({
                        "column": col,
                        "change_type": "row_removal",
                        "count": outlier_count,
                        "description": f"Removed {outlier_count} rows with outliers in '{col}'"
                    })

            elif action == "trim_whitespace":
                if col in df.columns:
                    series = df[col].astype(str)
                    trimmed = series.str.strip()
                    diff_mask = (series != trimmed) & df[col].notna()
                    ws_count = int(diff_mask.sum())
                    if ws_count > 0:
                        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
                        changed_cells_count += ws_count
                        operations_executed.append(f"Trimmed whitespace in {ws_count} cells in '{col}'")
                        representative_samples.append({
                            "column": col,
                            "change_type": "whitespace_trimmed",
                            "count": ws_count
                        })

            elif action == "standardize_casing":
                case_style = params.get("case_style", "title")
                if col in df.columns:
                    original_series = df[col].astype(str)
                    if case_style == "lower":
                        transformed = df[col].apply(lambda x: x.strip().lower() if isinstance(x, str) else x)
                    elif case_style == "upper":
                        transformed = df[col].apply(lambda x: x.strip().upper() if isinstance(x, str) else x)
                    else: # title
                        transformed = df[col].apply(lambda x: x.strip().title() if isinstance(x, str) else x)
                    
                    diff_mask = (original_series != transformed.astype(str)) & df[col].notna()
                    diff_count = int(diff_mask.sum())
                    if diff_count > 0:
                        df[col] = transformed
                        changed_cells_count += diff_count
                        operations_executed.append(f"Standardized {diff_count} cells in '{col}' to {case_style} case")
                        representative_samples.append({
                            "column": col,
                            "change_type": "casing_standardized",
                            "count": diff_count,
                            "case_style": case_style
                        })

            elif action == "convert_to_numeric":
                errors_mode = params.get("errors", "coerce")
                clean_col = df[col].astype(str).str.strip()
                converted = pd.to_numeric(clean_col, errors=errors_mode)
                diff_count = int((df[col] != converted).sum())
                df[col] = converted
                changed_cells_count += diff_count
                operations_executed.append(f"Converted column '{col}' to numeric format")
                representative_samples.append({
                    "column": col,
                    "change_type": "type_conversion",
                    "target_type": "numeric"
                })

            elif action in ["keep_duplicates", "keep_outliers"]:
                # Explicit no-op
                operations_executed.append(f"Kept {action.replace('keep_', '')} unchanged as requested.")

            else:
                skipped_operations.append({
                    "operation": op,
                    "reason": f"Unsupported or unknown action '{action}'"
                })

        except Exception as e:
            skipped_operations.append({
                "operation": op,
                "reason": f"Execution error: {str(e)}"
            })

    final_rows = len(df)
    final_cols = len(df.columns)
    final_missing = int(df.isna().sum().sum())
    final_duplicates = int(df.duplicated().sum())

    summary = {
        "initial_rows": initial_rows,
        "final_rows": final_rows,
        "rows_removed": rows_removed_total,
        "initial_cols": initial_cols,
        "final_cols": final_cols,
        "initial_missing": initial_missing,
        "final_missing": final_missing,
        "initial_duplicates": initial_duplicates,
        "final_duplicates": final_duplicates,
        "changed_cells": changed_cells_count,
        "operations_executed": operations_executed,
        "skipped_operations": skipped_operations,
        "representative_samples": representative_samples
    }

    return df, summary
