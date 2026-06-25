import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import shutil
import seaborn as sns

def generate_histograms(df):
    output_dir = "plots/histograms"

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    saved_plots = []

    numerical_cols = df.select_dtypes(include=np.number).columns

    for col in numerical_cols:

        plt.figure(figsize=(8, 5))

        plt.hist(df[col].dropna(), bins=30)

        plt.title(f"Distribution of {col}")
        plt.xlabel(col)
        plt.ylabel("Frequency")

        filename = f"{output_dir}/hist_{col}.png"

        plt.savefig(filename, dpi=300, bbox_inches="tight")
        plt.close()

        saved_plots.append(filename)

    return saved_plots