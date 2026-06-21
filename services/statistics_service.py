import pandas as pd
from services.quality_service import outlier_detection, get_missing_values


def descriptive_statistics(df):
    numerical_cols = df.select_dtypes(include="number").columns
    results = {}

    for col in numerical_cols:

        mode_val = df[col].mode()

        results[col] = {
            "mean": float(round(df[col].mean(), 2)),
            "median": float(round(df[col].median(), 2)),
            "mode": float(round(mode_val.iloc[0], 2)) if not mode_val.empty else None,
            "min": float(round(df[col].min(), 2)),
            "max": float(round(df[col].max(), 2)),
            "range": float(round(df[col].max() - df[col].min(), 2)),
            "variance": float(round(df[col].var(), 2)),
            "std_dev": float(round(df[col].std(), 2)),
        }

    return results

def categorical_analysis(df):

    categorical_cols = df.select_dtypes(include=["object", "category"]).columns

    results = {}

    for col in categorical_cols:
        unique_values = int(df[col].nunique())
        mode_val = df[col].mode()
        top_category = (mode_val.iloc[0]
            if not mode_val.empty
            else None
        )

        top_cat_freq = int(df[col].value_counts().iloc[0])

        percentage = round((top_cat_freq / len(df)) * 100, 2)

        results[col] = {
            "unique_values": unique_values,
            "most_frequent": top_category,
            "top_cat_freq": top_cat_freq,
            "percentage": percentage,
        }

    return results

def correlation_analysis(df):

    numerical_df = df.select_dtypes(include="number")

    corr_matrix = numerical_df.corr()

    cols = corr_matrix.columns

    results = []

    for i in range(len(cols)):
        for j in range(i+1, len(cols)):

            col1 = cols[i]
            col2 = cols[j]

            corr = corr_matrix.loc[col1, col2]

            if abs(corr) >= 0.7:

                results.append({
                    "column_1": col1,
                    "column_2": col2,
                    "correlation": round(float(corr), 2)
                })

    return {
        "strong_correlations": results
    }

def distribution_analysis(df):
    numerical_df = df.select_dtypes(include="number").columns
    results = {}
    for col in numerical_df:
        skewness = float(round(df[col].skew(), 2))
        kurtosis = float(round(df[col].kurt(), 2))

        if skewness > 0.5:
            distribution = "Right Skewed"
        elif skewness < -0.5:
            distribution = "Left Skewed"
        else:
            distribution = "Approximately Normal"
        results[col]=  {
            "skewness": skewness,
            "kurtosis": kurtosis,
            "distribution": distribution
        }
    return results

def insight_engine(df):
    insights = []
    # -------------------------
    # Distribution Insights
    # -------------------------
    distribution_results = distribution_analysis(df)
    for col, stats in distribution_results.items():
        if df[col].nunique() <= 2:
            continue
        skewness = stats["skewness"]
        if skewness > 1.5:
            insights.append(f"{col} is highly right skewed and may benefit from log transformation")
        elif skewness < -1.5:
            insights.append(f"{col} is highly left skewed")
    # -------------------------
    # Correlation Insights
    # -------------------------
    corr_results = correlation_analysis(df)
    for relation in corr_results["strong_correlations"]:
        col1 = relation["column_1"]
        col2 = relation["column_2"]
        corr = relation["correlation"]
        if abs(corr) > 0.9:
            insights.append(f"{col1} and {col2} exhibit extremely strong correlation ({corr}), which may indicate redundant information")
        elif abs(corr) > 0.7:
            insights.append(f"{col1} and {col2} exhibit strong correlation ({corr})")
    # -------------------------
    # Outlier Insights
    # -------------------------
    outlier_results = outlier_detection(df)
    for col, stats in outlier_results.items():
        if df[col].nunique() <= 2:
            continue
        percent = stats["percent"]
        if percent > 20:
            insights.append(f"{col} contains a very high proportion of outliers ({percent}%)")
        elif percent > 10:
            insights.append(f"{col} contains a high proportion of outliers ({percent}%)")
        elif percent > 5:
            insights.append(f"{col} contains a moderate number of outliers ({percent}%)")
    # -------------------------
    # Missing Value Insights
    # -------------------------
    missing_results = get_missing_values(df)
    for col, stats in missing_results.items():
        percent = stats["percentage"]
        if percent > 40:
            insights.append(f"{col} has excessive missing values ({percent}%) and may require removal")
        elif percent > 20:
            insights.append(f"{col} contains substantial missing values ({percent}%)")
    # -------------------------
    # Constant Column Detection
    # -------------------------
    for col in df.columns:
        if df[col].nunique(dropna=False) == 1:
            insights.append(f"{col} contains only one unique value and provides little analytical value")

    return insights



async def statistics_analysis(file):
    df = pd.read_csv(file.file)
    return {
        "descriptive_statistics": descriptive_statistics(df),
        "categorical_analysis": categorical_analysis(df),
        "correlation_analysis": correlation_analysis(df),
        "distribution_analysis": distribution_analysis(df),
        "insights": insight_engine(df)
    }