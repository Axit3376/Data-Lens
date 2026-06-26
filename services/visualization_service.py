from services.visualizations.histogram import generate_histograms
from services.visualizations.boxplot import generate_boxplots
from services.visualizations.heatmap import generate_heatmap
from services.visualizations.countplot import generate_countplots
from services.visualizations.piechart import generate_piecharts
from services.visualizations.missing import generate_missing_values_plot
from services.visualizations.target import generate_target_visualizations
from utils.analysis_store import update_analysis

def visualization_analysis(df, target=None):
    results = {
        "numerical": {},
        "categorical": {},
        "dataset": {},
        "target": {}
    }

    results["numerical"]["histograms"] = generate_histograms(df)
    results["numerical"]["boxplots"] = generate_boxplots(df)
    results["numerical"]["heatmap"] = generate_heatmap(df)
    results["categorical"]["countplots"] = generate_countplots(df)
    results["categorical"]["piecharts"] = generate_piecharts(df)
    results["dataset"]["missing_values"] = generate_missing_values_plot(df)
    if target:
        results["target"] = generate_target_visualizations(df, target)

    update_analysis("visualizations", results)

    return results