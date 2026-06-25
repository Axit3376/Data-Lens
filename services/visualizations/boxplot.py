import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import shutil
import seaborn as sns

def generate_boxplots(df):

    output_dir = "plots/boxplots"

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    saved_plots = []

    numerical_cols = df.select_dtypes(include=np.number).columns

    for col in numerical_cols:

        plt.figure(figsize=(8,5))

        plt.boxplot(df[col].dropna(), vert=True)

        plt.title(f"Box Plot of {col}")
        plt.ylabel(col)

        filename = f"{output_dir}/box_{col}.png"

        plt.savefig(filename, dpi=300, bbox_inches="tight")

        plt.close()

        saved_plots.append(filename)

    return saved_plots