import pandas as pd

def profile_dataset(file):
    df = pd.read_csv(file.file)
    return {
        "dataset_info": {
            "filename": file.filename,
            "rows": df.shape[0],
            "cols": df.shape[1],
            "duplicate_values": int(df.duplicated().sum()),
        },

        # "col_names": list(df.columns),
        # "col_dtypes": df.dtypes.astype(str).to_dict(),
        # List comprehension: new_list = [expression for item in old_list]
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
                # "duplicate_values": int(df[col].duplicated().sum()),
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