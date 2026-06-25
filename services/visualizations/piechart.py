import os
import shutil

import matplotlib.pyplot as plt
import pandas as pd

MAX_PIE_CATEGORIES = 6


def generate_piecharts(df):

    output_dir = "plots/piecharts"

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    saved_plots = []

    categorical_cols = df.select_dtypes(include=["object", "category"]).columns

    for col in categorical_cols:

        unique_values = df[col].nunique(dropna=True)

        # Only generate for small-cardinality columns
        if unique_values < 2 or unique_values > MAX_PIE_CATEGORIES:
            continue

        plt.figure(figsize=(7, 7))

        value_counts = df[col].value_counts()

        plt.pie(
            value_counts,
            labels=value_counts.index,
            autopct="%1.1f%%",
            startangle=90
        )

        plt.title(f"Pie Chart of {col}")

        filename = f"{output_dir}/pie_{col}.png"

        plt.savefig(filename, dpi=300, bbox_inches="tight")

        plt.close()

        saved_plots.append(filename)

    return saved_plots