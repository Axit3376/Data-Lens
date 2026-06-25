import os
import shutil
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

MAX_PLOTS = 20


def generate_countplots(df):

    output_dir = "plots/countplots"

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    saved_plots = []

    categorical_cols = df.select_dtypes(include=["object", "category"]).columns

    for col in categorical_cols:

        # Skip columns with too many unique values
        if df[col].nunique(dropna=True) > MAX_PLOTS:
            continue

        plt.figure(figsize=(10, 6))

        order = df[col].value_counts().index

        sns.countplot(
            data=df,
            x=col,
            order=order
        )

        plt.title(f"Count Plot of {col}")
        plt.xlabel(col)
        plt.ylabel("Count")

        plt.xticks(rotation=45, ha="right")

        plt.tight_layout()

        filename = f"{output_dir}/count_{col}.png"

        plt.savefig(filename, dpi=300)

        plt.close()

        saved_plots.append(filename)

    return saved_plots