import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SEVERITY_COLORS = ["#4caf50", "#ff9800", "#f44336"]
SEVERITY_LABELS = ["1 - Mineur", "2 - Modéré", "3 - Critique"]
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


def incident_report_per_day_and_severity(df: pd.DataFrame) -> None:
    data = df.copy()
    data["date"] = pd.to_datetime(data["date"])
    data["jour_semaine"] = data["date"].dt.dayofweek
    pivot = data.groupby(["jour_semaine", "severity"]).size().unstack(fill_value=0)
    pivot = pivot.reindex(index=range(7), columns=[1, 2, 3], fill_value=0)

    x = np.arange(7)
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, (sev, color, label) in enumerate(zip([1, 2, 3], SEVERITY_COLORS, SEVERITY_LABELS)):
        bars = ax.bar(x + (i - 1) * width, pivot[sev], width, label=label, color=color)
        ax.bar_label(bars, padding=2, fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(JOURS)

    ax.set_title("Incidents par jour de la semaine et sévérité")
    ax.set_xlabel("Jour")
    ax.set_ylabel("Nombre d'incidents")
    ax.legend(title="Sévérité")
    plt.tight_layout()
    plt.show()


def incident_report_per_week_and_severity(df: pd.DataFrame) -> None:
    data = df.copy()
    data["date"] = pd.to_datetime(data["date"])
    data["semaine"] = data["date"].dt.isocalendar().week.astype(int)
    pivot = data.groupby(["semaine", "severity"]).size().unstack(fill_value=0)
    pivot = pivot.reindex(index=range(1, 53), columns=[1, 2, 3], fill_value=0)

    week_labels = [f"S{w:02d}" for w in range(1, 53)]

    fig, ax = plt.subplots(figsize=(18, 5))
    bottom = np.zeros(52)
    for sev, color, label in zip([1, 2, 3], SEVERITY_COLORS, SEVERITY_LABELS):
        ax.bar(range(52), pivot[sev], bottom=bottom, label=label, color=color)
        bottom += pivot[sev].values

    ax.set_xticks(range(52))
    ax.set_xticklabels(week_labels, fontsize=7, rotation=45, ha="right")
    ax.set_title("Incidents par semaine (toutes années confondues)")
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

    fig, ax = plt.subplots(figsize=(8, 5))
    for i, (sev, color, label) in enumerate(zip([1, 2, 3], SEVERITY_COLORS, SEVERITY_LABELS)):
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

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, (sev, color, label) in enumerate(zip([1, 2, 3], SEVERITY_COLORS, SEVERITY_LABELS)):
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
