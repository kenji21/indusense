import matplotlib.pyplot as plt
import pandas as pd


def _build_h1_mask(df_tel: pd.DataFrame, df_inc: pd.DataFrame) -> pd.Series | None:
    date_col = next((c for c in df_tel.columns if c in ("date", "timestamp", "recorded_at", "datetime")), None)
    if date_col is None:
        return None
    tel = df_tel.copy()
    tel["_dt"] = pd.to_datetime(tel[date_col])
    mask = pd.Series(False, index=tel.index)
    delta = pd.Timedelta(hours=1)
    for machine, inc_m in df_inc.groupby("machine_id"):
        if "time" in inc_m.columns:
            dts = pd.to_datetime(inc_m["date"].astype(str) + " " + inc_m["time"].astype(str))
        else:
            dts = pd.to_datetime(inc_m["date"])
        idx = tel[tel["machine_id"] == machine].index
        for t_end in dts:
            mask.loc[idx] |= (tel.loc[idx, "_dt"] >= t_end - delta) & (tel.loc[idx, "_dt"] <= t_end)
    return mask


def list_missing_telemetry(df_tel: pd.DataFrame, df_inc: pd.DataFrame | None = None) -> pd.DataFrame:
    numeric_cols = [c for c in df_tel.columns if c not in ("machine_id",) and df_tel[c].dtype != object]
    h1_mask = _build_h1_mask(df_tel, df_inc) if df_inc is not None else None

    rows = []
    for machine in sorted(df_tel["machine_id"].unique()):
        sub = df_tel[df_tel["machine_id"] == machine]
        sub_h1 = df_tel[h1_mask & (df_tel["machine_id"] == machine)] if h1_mask is not None else None
        for col in numeric_cols:
            n_missing = sub[col].isna().sum()
            if n_missing > 0:
                row = {
                    "machine_id": machine,
                    "colonne": col,
                    "manquants": n_missing,
                    "total": len(sub),
                    "pct": round(n_missing / len(sub) * 100, 1),
                }
                if sub_h1 is not None:
                    row["manquants_h1"] = int(sub_h1[col].isna().sum())
                rows.append(row)

    cols = ["machine_id", "colonne", "manquants", "total", "pct"]
    if h1_mask is not None:
        cols.append("manquants_h1")
    if not rows:
        return pd.DataFrame(columns=cols)

    return pd.DataFrame(rows).sort_values(["machine_id", "colonne"]).reset_index(drop=True)


def missing_telemetry_incident_correlation(df_tel: pd.DataFrame, df_inc: pd.DataFrame) -> plt.Figure:
    numeric_cols = [c for c in df_tel.columns if c not in ("machine_id",) and df_tel[c].dtype != object]
    date_col = next((c for c in df_tel.columns if c in ("date", "timestamp", "recorded_at", "datetime")), None)

    if date_col is None:
        raise ValueError("Aucune colonne date trouvée dans la télémétrie.")

    tel = df_tel.copy()
    tel["_date"] = pd.to_datetime(tel[date_col]).dt.date
    tel["_missing"] = tel[numeric_cols].isna().sum(axis=1)
    daily_missing = tel.groupby(["machine_id", "_date"])["_missing"].sum().reset_index()

    inc = df_inc.copy()
    inc["_date"] = pd.to_datetime(inc["date"]).dt.date
    daily_incidents = inc.groupby(["machine_id", "_date"]).size().reset_index(name="_incidents")

    merged = daily_missing.merge(daily_incidents, on=["machine_id", "_date"], how="left")
    merged["_incidents"] = merged["_incidents"].fillna(0)

    correlations = (
        merged.groupby("machine_id")
        .apply(lambda g: g["_missing"].corr(g["_incidents"]), include_groups=False)
        .sort_index()
    )

    machines = correlations.index.tolist()
    values = correlations.values
    colors = ["#e53935" if v > 0 else "#1e88e5" for v in values]

    fig, ax = plt.subplots(figsize=(12, 5))
    bars = ax.bar(range(len(machines)), values, color=colors)
    ax.bar_label(bars, fmt="%.2f", padding=3, fontsize=8)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(range(len(machines)))
    ax.set_xticklabels(machines, rotation=45, ha="right")
    ax.set_ylabel("Corrélation de Pearson")
    ax.set_title("Corrélation entre données manquantes et incidents (par machine, par jour)")
    plt.tight_layout()
    return fig
