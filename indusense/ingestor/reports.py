import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SEVERITY_COLORS = ["#4caf50", "#ff9800", "#f44336"]
SEVERITY_LABELS = ["1 - Mineur", "2 - Modéré", "3 - Critique"]
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


def _split_failure_telemetry(
    df_tel: pd.DataFrame, df_inc: pd.DataFrame, machine: str, window_hours: int = 1
) -> tuple[pd.DataFrame, pd.DataFrame]:
    inc_m = df_inc[df_inc["machine_id"] == machine].copy()
    date_col = next((c for c in df_tel.columns if c in ("date", "timestamp", "recorded_at", "datetime")), None)
    tel_m = df_tel[df_tel["machine_id"] == machine].copy()

    if date_col is None or inc_m.empty:
        return tel_m.iloc[0:0], tel_m

    if "time" in inc_m.columns:
        inc_m["_dt"] = pd.to_datetime(inc_m["date"].astype(str) + " " + inc_m["time"].astype(str))
    else:
        inc_m["_dt"] = pd.to_datetime(inc_m["date"])

    tel_m["_dt"] = pd.to_datetime(tel_m[date_col])

    failure_mask = pd.Series(False, index=tel_m.index)
    delta = pd.Timedelta(hours=window_hours)
    for t_end in inc_m["_dt"]:
        failure_mask |= (tel_m["_dt"] >= t_end - delta) & (tel_m["_dt"] <= t_end)

    return tel_m[failure_mask], tel_m[~failure_mask]

def telemetry_report_temperature_per_machine(df: pd.DataFrame) -> plt.Figure:
    machines = sorted(df["machine_id"].unique())
    data = [df[df["machine_id"] == m]["temperature_c"].dropna() for m in machines]

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.boxplot(data, patch_artist=True)
    ax.set_xticks(range(1, len(machines) + 1))
    ax.set_xticklabels(machines, rotation=45, ha="right")
    ax.set_xlabel("Machine")
    ax.set_ylabel("Température (°C)")
    ax.set_title("Répartition de la température par machine")
    plt.tight_layout()
    return fig


def telemetry_report_temperature_distribution(df: pd.DataFrame) -> plt.Figure:
    machines = sorted(df["machine_id"].unique())

    fig, ax = plt.subplots(figsize=(12, 5))
    for machine in machines:
        values = df[df["machine_id"] == machine]["temperature_c"].dropna()
        ax.hist(values, bins=30, alpha=0.4, label=machine, density=True)

    ax.set_xlabel("Température (°C)")
    ax.set_ylabel("Densité")
    ax.set_title("Distribution des températures par machine")
    ax.legend(fontsize=7, ncol=4, loc="upper right")
    plt.tight_layout()
    return fig


def telemetry_report_rotation_failure_per_machine(df_tel: pd.DataFrame, df_inc: pd.DataFrame, machine: str) -> plt.Figure:
    tel_failure, tel_normal = _split_failure_telemetry(df_tel, df_inc, machine)

    data_failure = tel_failure["rotation_mean_rpm"].dropna()
    data_normal = tel_normal["rotation_mean_rpm"].dropna()

    bins = np.linspace(
        min(data_normal.min() if not data_normal.empty else 0,
            data_failure.min() if not data_failure.empty else 0),
        max(data_normal.max() if not data_normal.empty else 1,
            data_failure.max() if not data_failure.empty else 1),
        25,
    )

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(data_normal, bins=bins, color="#1e88e5", alpha=0.25, edgecolor="white", label="Hors panne")
    ax.hist(data_failure, bins=bins, color="#1e88e5", alpha=0.85, edgecolor="white", label="Panne")
    if not data_normal.empty:
        ax.axvline(data_normal.mean(), color="gray", linestyle="--", linewidth=1,
                   label=f"Moy hors panne: {data_normal.mean():.0f}")
    if not data_failure.empty:
        ax.axvline(data_failure.mean(), color="black", linestyle="--", linewidth=1,
                   label=f"Moy panne: {data_failure.mean():.0f}")
    ax.set_xlabel("Rotation moyenne (RPM)")
    ax.set_ylabel("Fréquence")
    ax.set_title(f"{machine} — Distribution rotation (panne vs hors panne)")
    ax.legend(fontsize=8)
    plt.tight_layout()
    return fig


def telemetry_report_pieces_per_machine(df: pd.DataFrame) -> plt.Figure:
    machines = sorted(df["machine_id"].unique())
    data = [df[df["machine_id"] == m]["pieces_produced"].dropna() for m in machines]

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.boxplot(data, patch_artist=True)
    ax.set_xticks(range(1, len(machines) + 1))
    ax.set_xticklabels(machines, rotation=45, ha="right")
    ax.set_xlabel("Machine")
    ax.set_ylabel("Pièces produites")
    ax.set_title("Répartition des pièces produites par machine")
    plt.tight_layout()
    return fig


def telemetry_report_voltage_per_machine(df: pd.DataFrame) -> plt.Figure:
    machines = sorted(df["machine_id"].unique())
    data = [df[df["machine_id"] == m]["voltage_mean_v"].dropna() for m in machines]

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.boxplot(data, patch_artist=True)
    ax.set_xticks(range(1, len(machines) + 1))
    ax.set_xticklabels(machines, rotation=45, ha="right")
    ax.set_xlabel("Machine")
    ax.set_ylabel("Tension moyenne (V)")
    ax.set_title("Répartition de la tension moyenne par machine")
    plt.tight_layout()
    return fig


def telemetry_report_pressure_per_machine(df: pd.DataFrame) -> plt.Figure:
    machines = sorted(df["machine_id"].unique())
    data = [df[df["machine_id"] == m]["pressure_bar"].dropna() for m in machines]

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.boxplot(data, patch_artist=True)
    ax.set_xticks(range(1, len(machines) + 1))
    ax.set_xticklabels(machines, rotation=45, ha="right")
    ax.set_xlabel("Machine")
    ax.set_ylabel("Pression (bar)")
    ax.set_title("Répartition de la pression par machine")
    plt.tight_layout()
    return fig


def incident_report_type_per_machine(df: pd.DataFrame) -> plt.Figure:
    type_cols = [c for c in df.columns if c.startswith("type_")]
    pivot = df.groupby("machine_id")[type_cols].sum()
    pivot.columns = [c.removeprefix("type_").replace("_", " ") for c in pivot.columns]
    pivot = pivot.loc[sorted(pivot.index)]

    fig, ax = plt.subplots(figsize=(14, 7))
    im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto")
    fig.colorbar(im, ax=ax, shrink=0.8, label="Nombre d'incidents")

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=35, ha="right", fontsize=9)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=9)

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            v = int(pivot.values[i, j])
            ax.text(j, i, str(v) if v > 0 else "", ha="center", va="center", fontsize=8,
                    color="black" if pivot.values[i, j] < pivot.values.max() * 0.6 else "white")

    ax.set_title("Répartition des types de panne par machine")
    plt.tight_layout()
    return fig


def incident_report_signal_correlation(df: pd.DataFrame) -> plt.Figure:
    signal_cols = [c for c in df.columns if c.startswith("type_")]
    cols = ["severity"] + signal_cols
    corr = df[cols].corr()
    labels = ["sévérité"] + [c.removeprefix("type_").replace("_", " ") for c in signal_cols]

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(corr.values, cmap="RdYlGn", vmin=-1, vmax=1)
    fig.colorbar(im, ax=ax, shrink=0.8)

    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(labels, fontsize=8)

    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center", va="center", fontsize=7)

    ax.set_title("Corrélation entre incidents et signaux")
    plt.tight_layout()
    return fig


def incident_report_confidence(df: pd.DataFrame) -> plt.Figure:
    buckets = pd.cut(df["confidence_score"], bins=[0, 0.2, 0.6, 1.0],
                     labels=["Faible (0–0.2)", "Moyen (0.2–0.6)", "Élevé (0.6–1.0)"],
                     include_lowest=True)
    counts = buckets.value_counts().reindex(["Faible (0–0.2)", "Moyen (0.2–0.6)", "Élevé (0.6–1.0)"])

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(counts.index, counts.values, color=["#f44336", "#ff9800", "#4caf50"])
    ax.bar_label(bars, padding=2, fontsize=9)
    ax.set_title("Distribution de l'indice de confiance des signalements")
    ax.set_xlabel("Niveau de confiance")
    ax.set_ylabel("Nombre d'incidents")
    plt.tight_layout()
    return fig


def incident_report_per_signal(df: pd.DataFrame) -> plt.Figure:
    signal_cols = [c for c in df.columns if c.startswith("type_")]
    counts = df[signal_cols].sum().sort_values(ascending=False)
    labels = [c.removeprefix("type_").replace("_", " ") for c in counts.index]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(range(len(counts)), counts.values, color="#1976d2")
    ax.bar_label(bars, padding=2, fontsize=8)
    ax.set_xticks(range(len(counts)))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_title("Incidents par type de signal")
    ax.set_xlabel("Signal")
    ax.set_ylabel("Nombre d'incidents")
    plt.tight_layout()
    return fig


def incident_report_per_machine(df: pd.DataFrame) -> plt.Figure:
    counts = df.groupby("machine_id").size().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(12, 5))
    bars = ax.bar(range(len(counts)), counts.values, color="#7b1fa2")
    ax.bar_label(bars, padding=2, fontsize=8)
    ax.set_xticks(range(len(counts)))
    ax.set_xticklabels(counts.index, rotation=45, ha="right")
    ax.set_title("Incidents par machine")
    ax.set_xlabel("Machine")
    ax.set_ylabel("Nombre d'incidents")
    plt.tight_layout()
    return fig


def incident_report_per_day_and_severity(df: pd.DataFrame) -> plt.Figure:
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
    return fig


def incident_report_per_week_and_severity(df: pd.DataFrame) -> plt.Figure:
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
    return fig


def incident_report_per_shift(df: pd.DataFrame) -> plt.Figure:
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
    return fig


def telemetry_report_failure_distributions(df_tel: pd.DataFrame, df_inc: pd.DataFrame, machine: str) -> plt.Figure:
    tel_failure, tel_normal = _split_failure_telemetry(df_tel, df_inc, machine)

    metrics = [
        ("temperature_c", "Température (°C)", "#e53935"),
        ("pressure_bar", "Pression (bar)", "#1e88e5"),
        ("voltage_mean_v", "Tension (V)", "#43a047"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(f"{machine} — Distribution des capteurs aux moments de panne", fontsize=13)

    for ax, (col, label, color) in zip(axes, metrics):
        data_normal = tel_normal[col].dropna()
        data_failure = tel_failure[col].dropna()
        bins = np.linspace(
            min(data_normal.min() if not data_normal.empty else 0,
                data_failure.min() if not data_failure.empty else 0),
            max(data_normal.max() if not data_normal.empty else 1,
                data_failure.max() if not data_failure.empty else 1),
            25,
        )
        ax.hist(data_normal, bins=bins, color=color, alpha=0.25, edgecolor="white", label="Hors panne")
        ax.hist(data_failure, bins=bins, color=color, alpha=0.85, edgecolor="white", label="Panne")
        if not data_normal.empty:
            ax.axvline(data_normal.mean(), color="gray", linestyle="--", linewidth=1,
                       label=f"Moy hors panne: {data_normal.mean():.1f}")
        if not data_failure.empty:
            ax.axvline(data_failure.mean(), color="black", linestyle="--", linewidth=1,
                       label=f"Moy panne: {data_failure.mean():.1f}")
        ax.set_xlabel(label)
        ax.set_ylabel("Fréquence")
        ax.set_title(label)
        ax.legend(fontsize=8)

    plt.tight_layout()
    return fig


def incident_report_per_operator_and_severity(df: pd.DataFrame) -> plt.Figure:
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
    return fig
