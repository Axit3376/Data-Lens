import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import shutil
import seaborn as sns

def generate_heatmap(df):

    output_dir = "plots/heatmaps"

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    numerical_df = df.select_dtypes(include=np.number)

    if numerical_df.shape[1] < 2:
        return None

    corr_matrix = numerical_df.corr()

    plt.figure(figsize=(10, 8))

    sns.heatmap(
        corr_matrix,
        annot=True,
        cmap="coolwarm",
        fmt=".2f",
        linewidths=0.5
    )

    plt.title("Correlation Heatmap")

    filename = f"{output_dir}/correlation_heatmap.png"

    plt.savefig(filename, dpi=300, bbox_inches="tight")

    plt.close()

    return filename