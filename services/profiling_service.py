import pandas as pd
from utils.analysis_store import update_analysis, register_dataset_upload
from services.quality_score_service import compute_quality_score
from services.cleaning_service import detect_cleaning_recommendations


def profile_dataset(file, session_id: str = "default_session"):
    df = pd.read_csv(file.file)
    register_dataset_upload(df, file.filename, session_id)
    
    # Calculate quality score as part of initial profile
    q_score = compute_quality_score(df)
    update_analysis("quality_score", q_score)

    # Detect and store cleaning recommendations
    cleaning_recs = detect_cleaning_recommendations(df)
    update_analysis("cleaning_recommendations", cleaning_recs)

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