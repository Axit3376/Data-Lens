import pandas as pd
import numpy as np
from utils.analysis_store import update_analysis

ORDINAL_COLUMNS = {
    "loan_grade",
    "education_level",
    "rating"
}

def missing_value_strategy(df):
    recommendations = {}
    missing_percentage = (df.isnull().sum() / len(df)) * 100

    for col in df.columns:
        if missing_percentage[col] == 0:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            if missing_percentage[col] < 10:
                strategy = "Median Imputation"
            elif missing_percentage[col] <= 30:
                strategy = "Median Imputation (Review Recommended)"
            else:
                strategy = "Consider Dropping Column"
        else:
            if missing_percentage[col] <= 30:
                strategy = "Most Frequent Imputation"
            else:
                strategy = "Consider Dropping Column"

        recommendations[col] = {
            "missing_percentage": round(missing_percentage[col], 2),
            "recommendation": strategy
        }
    return recommendations

def encoding_recommendation(df):
    recommendations = {}
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns

    for col in categorical_cols:
        unique_count = df[col].nunique(dropna=True)
        unique_percentage = (unique_count / len(df)) * 100
        if unique_percentage > 90:
            recommendation = "Not Recommended (High Cardinality)"
        elif col in ORDINAL_COLUMNS:
            recommendation = "Ordinal Encoding"
        elif unique_count == 2:
            recommendation = "Label Encoding"
        else:
            recommendation = "One-Hot Encoding"
        recommendations[col] = {
            "unique_count": unique_count,
            "unique_percentage": round(unique_percentage, 2),
            "recommendation": recommendation
        }
    return recommendations

def scaling_recommendation(df):
    recommendations = {}
    numerical_cols = df.select_dtypes(include=np.number).columns

    for col in numerical_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        outlier_percentage = (
            ((df[col] < lower) | (df[col] > upper)).sum()
            / len(df)
        ) * 100
        if outlier_percentage > 5:
            recommendations[col] = {
                "outlier_percentage": round(outlier_percentage, 2),
                "recommendation": "RobustScaler"
            }
        else:
            recommendations[col] = {
                "outlier_percentage": round(outlier_percentage, 2),
                "recommendation": "StandardScaler"
            }
    return recommendations

def transformation_recommendation(df):
    recommendations = {}
    numerical_cols = df.select_dtypes(include=np.number).columns

    for col in numerical_cols:
        skewness = df[col].skew()
        if abs(skewness) <= 1:
            continue
        else:
            if (df[col] < 0).any():
                recommendations[col] = {
                    "skewness": round(skewness, 2),
                    "recommendation": "Yeo-Johnson Transformation"
                }
            else:
                recommendations[col] = {
                    "skewness": round(skewness, 2),
                    "recommendation": "Log Transformation"
                }
    return recommendations

def high_cardinality_detection(df):
    recommendations = {}
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns

    for col in categorical_cols:
        unique_percentage = (df[col].nunique(dropna=True) / len(df)) * 100
        if unique_percentage <= 90:
            continue
        recommendations[col] = {
            "unique_percentage": round(unique_percentage, 2),
            "recommendation": "Consider Dropping (High Cardinality)"
        }
    return recommendations

def constant_feature_detection(df):
    recommendations = {}

    for col in df.columns:
        unique_count = df[col].nunique(dropna=False)
        # Constant Feature
        if unique_count == 1:
            recommendations[col] = {
                "recommendation": "Drop Column (Constant Feature)"
            }
            continue
        # Near Constant Feature
        dominant_percentage = (
            df[col]
            .value_counts(normalize=True, dropna=False)
            .iloc[0]
        ) * 100
        if dominant_percentage >= 99:
            recommendations[col] = {
                "dominant_percentage": round(dominant_percentage, 2),
                "recommendation": "Consider Dropping (Near-Constant Feature)"
            }
    return recommendations

def correlation_recommendation(df):
    recommendations = []
    numerical_cols = df.select_dtypes(include=np.number)
    corr_matrix = numerical_cols.corr().abs()
    upper_triangle = corr_matrix.where(
        np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    )

    for col in upper_triangle.columns:
        for row in upper_triangle.index:
            corr_value = upper_triangle.loc[row, col]
            if pd.notna(corr_value) and corr_value > 0.9:
                recommendations.append({
                    "feature_1": row,
                    "feature_2": col,
                    "correlation": round(corr_value, 2),
                    "recommendation": f"Consider dropping either '{row}' or '{col}'"
                })
    return recommendations

def class_imbalance_detection(df, target=None):
    if target is None or target not in df.columns:
        return {}
    class_distribution = (
        df[target]
        .value_counts(normalize=True)
        .mul(100)
        .round(2)
        .to_dict()
    )
    max_percentage = max(class_distribution.values())
    if max_percentage <= 80:
        return {}
    return {
        "distribution": class_distribution,
        "recommendation": "Dataset is imbalanced. Consider using SMOTE, oversampling, undersampling, or class weights."
    }

def feature_engineering(df, target=None):

    results = {
        "missing_value_strategy": {},
        "encoding": {},
        "scaling": {},
        "transformations": {},
        "high_cardinality": {},
        "constant_features": [],
        "highly_correlated": [],
        "class_imbalance": {}
    }
    results["missing_value_strategy"] = missing_value_strategy(df)
    results["encoding"] = encoding_recommendation(df)
    results["scaling"] = scaling_recommendation(df)
    results["transformations"] = transformation_recommendation(df)
    results["high_cardinality"] = high_cardinality_detection(df)
    results["constant_features"] = constant_feature_detection(df)
    results["highly_correlated"] = correlation_recommendation(df)
    results["class_imbalance"] = class_imbalance_detection(df, target)

    update_analysis("feature_engineering", results)

    return results