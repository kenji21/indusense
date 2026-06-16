import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def incident_report_per_day_and_severity(df: pd.DataFrame) -> None:
    data = df.copy()
    data["date"] = pd.to_datetime(data["date"])
    pivot = data.groupby(["date", "severity"]).size().unstack(fill_value=0)
    pivot = pivot.reindex(columns=[1, 2, 3], fill_value=0)

    colors = ["#4caf50", "#ff9800", "#f44336"]
    labels = ["1 - Mineur", "2 - Modéré", "3 - Critique"]

    fig, ax = plt.subplots(figsize=(14, 5))
    bottom = np.zeros(len(pivot))
    for sev, color, label in zip([1, 2, 3], colors, labels):
        ax.bar(pivot.index, pivot[sev], bottom=bottom, label=label, color=color)
        bottom += pivot[sev].values

    ax.set_title("Incidents par jour et sévérité")
    ax.set_xlabel("Date")
    ax.set_ylabel("Nombre d'incidents")
    ax.legend(title="Sévérité")
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.show()


def incident_report_per_week_and_severity(df: pd.DataFrame) -> None:
    data = df.copy()
    data["date"] = pd.to_datetime(data["date"])
    pivot = (
        data.groupby([pd.Grouper(key="date", freq="W"), "severity"])
        .size()
        .unstack(fill_value=0)
    )
    pivot = pivot.reindex(columns=[1, 2, 3], fill_value=0)

    colors = ["#4caf50", "#ff9800", "#f44336"]
    labels = ["1 - Mineur", "2 - Modéré", "3 - Critique"]
    week_labels = [d.strftime("S%W\n%d/%m") for d in pivot.index]

    fig, ax = plt.subplots(figsize=(12, 5))
    bottom = np.zeros(len(pivot))
    for sev, color, label in zip([1, 2, 3], colors, labels):
        ax.bar(range(len(pivot)), pivot[sev], bottom=bottom, label=label, color=color)
        bottom += pivot[sev].values

    ax.set_xticks(range(len(pivot)))
    ax.set_xticklabels(week_labels, fontsize=8)
    ax.set_title("Incidents par semaine et sévérité")
    ax.set_xlabel("Semaine")
    ax.set_ylabel("Nombre d'incidents")
    ax.legend(title="Sévérité")
    plt.tight_layout()
    plt.show()


def incident_report_per_shift(df: pd.DataFrame) -> None:
    pivot = df.groupby(["shift", "severity"]).size().unstack(fill_value=0)
    pivot = pivot.reindex(columns=[1, 2, 3], fill_value=0)

    shifts = pivot.index.tolist()
    x = np.arange(len(shifts))
    width = 0.25
    colors = ["#4caf50", "#ff9800", "#f44336"]
    labels = ["1 - Mineur", "2 - Modéré", "3 - Critique"]

    fig, ax = plt.subplots(figsize=(8, 5))
    for i, (sev, color, label) in enumerate(zip([1, 2, 3], colors, labels)):
        bars = ax.bar(x + (i - 1) * width, pivot[sev], width, label=label, color=color)
        ax.bar_label(bars, padding=2, fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(shifts, rotation=15, ha="right")
    ax.set_title("Incidents par shift et sévérité")
    ax.set_xlabel("Shift")
    ax.set_ylabel("Nombre d'incidents")
    ax.legend(title="Sévérité")
    plt.tight_layout()
    plt.show()


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
