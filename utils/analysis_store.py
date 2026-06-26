import json

FILE_PATH = "analysis/latest_analysis.json"


def load_analysis():
    with open(FILE_PATH, "r") as f:
        return json.load(f)


def save_analysis(data):
    with open(FILE_PATH, "w") as f:
        json.dump(data, f, indent=4)


def update_analysis(section, data):
    analysis = load_analysis()
    analysis[section] = data
    save_analysis(analysis)

def clear_analysis():
    save_analysis({})