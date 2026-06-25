import os
import shutil

import matplotlib.pyplot as plt


def generate_missing_values_plot(df):

    output_dir = "plots/missing"

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    missing = df.isnull().sum()

    # Skip if there are no missing values
    missing = missing[missing > 0]

    if missing.empty:
        return None

    plt.figure(figsize=(10, 6))

    missing.sort_values(ascending=False).plot(kind="bar")

    plt.title("Missing Values by Column")
    plt.xlabel("Columns")
    plt.ylabel("Missing Count")

    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()

    filename = f"{output_dir}/missing_values.png"

    plt.savefig(filename, dpi=300)

    plt.close()

    return filename