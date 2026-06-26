import pandas as pd
from utils.analysis_store import update_analysis


def profile_dataset(file):
    df = pd.read_csv(file.file)

    profile = {
        "dataset_info": {
            "filename": file.filename,
            "rows": df.shape[0],
            "cols": df.shape[1],
            "duplicate_values": int(df.duplicated().sum()),
        },

        "columns": [
            {
                "col_name": col,
                "dtype": str(df[col].dtype),
                "missing_values": int(df[col].isna().sum()),
                "missing_percent": round(
                    (df[col].isna().sum() / len(df)) * 100,
                    2
                ),
                "unique_values": int(df[col].nunique()),
            }
            for col in df.columns
        ],

        "statistical_summary": [
            {
                "column": col,
                "mean": float(df[col].mean()),
                "median": float(df[col].median()),
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "std": float(df[col].std())
            }
            for col in df.select_dtypes(include="number").columns
        ],

        "categorical_summary": [
            {
                "column": col,
                "top_value": str(df[col].mode().iloc[0]) if not df[col].mode().empty else None,
                "unique_values": int(df[col].nunique())
            }
            for col in df.select_dtypes(include=["object"]).columns
        ]
    }

    update_analysis("profiling", profile)

    return profile