import os
import shutil

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


def generate_target_distribution(df, target):

    output_dir = "plots/target"

    os.makedirs(output_dir, exist_ok=True)

    plt.figure(figsize=(8,6))

    if df[target].dtype == "object" or df[target].nunique() <= 10:

        sns.countplot(data=df, x=target)

        plt.ylabel("Count")

    else:

        plt.hist(df[target].dropna(), bins=30)

        plt.ylabel("Frequency")

    plt.title(f"Distribution of {target}")

    plt.tight_layout()

    filename = f"{output_dir}/target_distribution.png"

    plt.savefig(filename, dpi=300)

    plt.close()

    return filename

def generate_numeric_target_plots(df, target):

    output_dir = "plots/target/numerical"

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    saved_plots = []

    numerical_cols = df.select_dtypes(include=np.number).columns

    numerical_cols = [col for col in numerical_cols if col != target]

    for col in numerical_cols:

        plt.figure(figsize=(8,6))

        sns.boxplot(
            data=df,
            x=target,
            y=col
        )

        plt.title(f"{col} vs {target}")

        plt.tight_layout()

        filename = f"{output_dir}/{col}_vs_{target}.png"

        plt.savefig(filename, dpi=300)

        plt.close()

        saved_plots.append(filename)

    return saved_plots

def generate_categorical_target_plots(df, target):

    output_dir = "plots/target/categorical"

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    saved_plots = []

    categorical_cols = df.select_dtypes(
        include=["object","category"]
    ).columns

    categorical_cols = [col for col in categorical_cols if col != target]

    for col in categorical_cols:

        if df[col].nunique() > 20:
            continue

        plt.figure(figsize=(10,6))

        sns.countplot(
            data=df,
            x=col,
            hue=target
        )

        plt.xticks(rotation=45)

        plt.title(f"{col} vs {target}")

        plt.tight_layout()

        filename = f"{output_dir}/{col}_vs_{target}.png"

        plt.savefig(filename,dpi=300)

        plt.close()

        saved_plots.append(filename)

    return saved_plots

def generate_target_visualizations(df, target):

    if target not in df.columns:
        return {}

    output_dir = "plots/target"

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    results = {}

    results["distribution"] = generate_target_distribution(df,target)

    results["numeric_relationships"] = generate_numeric_target_plots(df,target)

    results["categorical_relationships"] = generate_categorical_target_plots(df,target)

    return results