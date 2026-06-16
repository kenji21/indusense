import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def incident_report_per_operator_and_severity(df: pd.DataFrame) -> None:
    pivot = df.groupby(["operator_name", "severity"]).size().unstack(fill_value=0)
    pivot = pivot.reindex(columns=[1, 2, 3], fill_value=0)

    operators = pivot.index.tolist()
    x = np.arange(len(operators))
    width = 0.25
    colors = ["#4caf50", "#ff9800", "#f44336"]
    labels = ["1 - Mineur", "2 - Modéré", "3 - Critique"]

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, (sev, color, label) in enumerate(zip([1, 2, 3], colors, labels)):
        bars = ax.bar(x + (i - 1) * width, pivot[sev], width, label=label, color=color)
        ax.bar_label(bars, padding=2, fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(operators, rotation=30, ha="right")
    ax.set_title("Incidents par opérateur et sévérité")
    ax.set_xlabel("Opérateur")
    ax.set_ylabel("Nombre d'incidents")
    ax.legend(title="Sévérité")
    plt.tight_layout()
    plt.show()
