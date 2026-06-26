import numpy as np
from utils.analysis_store import update_analysis

def get_missing_values(df):
    missing_count = df.isnull().sum()
    missing_percentage = (missing_count / len(df)) * 100

    return {
        col: {
            "count": int(missing_count[col]),
            "percentage": round(float(missing_percentage[col]), 2)
        }
        for col in missing_count.index
        if missing_count[col] > 0
    }

def get_duplicate_rows(df):
    return int(df.duplicated().sum())

def get_constant_columns(df):
    constant_columns = []
    for col in df.columns:
        if df[col].nunique() == 1:
            constant_columns.append(col)
    return constant_columns

def outlier_detection(df):
    numerical_cols = df.select_dtypes(include=np.number).columns

    results = {}

    for col in numerical_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        outliers = df[
            (df[col] < lower) |
            (df[col] > upper)
        ]
        count = len(outliers)
        percent = round((count / len(df)) * 100, 2)
        if count > 0:
            results[col] = {
                "count": count,
                "percent": percent
            }

    return results

def get_high_cardinality_columns(df):

    high_cardinality = {}

    for col in df.columns:

        unique_count = df[col].nunique()

        if unique_count > len(df) * 0.5:

            high_cardinality[col] = unique_count

    return high_cardinality

def analyze_quality(df):
    quality = {
        "missing_values": get_missing_values(df),
        "duplicate_rows": get_duplicate_rows(df),
        "constant_columns": get_constant_columns(df),
        "outlier_detection": outlier_detection(df),
        "high_cardinality": get_high_cardinality_columns(df)
    }
    update_analysis("quality", quality)

    return quality