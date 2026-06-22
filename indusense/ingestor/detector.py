import pandas as pd

TELEMETRY_METRICS = ["temperature_c", "pressure_bar", "rotation_mean_rpm", "voltage_mean_v"]


def detect_telemetry_anomalies(df_tel: pd.DataFrame, z_threshold: float = 3.0) -> pd.DataFrame:
    date_col = next((c for c in df_tel.columns if c in ("date", "timestamp", "recorded_at", "datetime")), None)
    metrics = [c for c in TELEMETRY_METRICS if c in df_tel.columns]

    rows = []
    for machine, group in df_tel.groupby("machine_id"):
        for col in metrics:
            series = group[col].dropna()
            if series.empty:
                continue
            mean, std = series.mean(), series.std()
            if std == 0:
                continue
            z_scores = (group[col] - mean) / std
            anomalies = group[z_scores.abs() > z_threshold]
            for idx, row in anomalies.iterrows():
                entry = {
                    "machine_id": machine,
                    "colonne": col,
                    "valeur": row[col],
                    "z_score": round(z_scores[idx], 2),
                }
                if date_col:
                    entry["date"] = row[date_col]
                rows.append(entry)

    cols = ["machine_id", "colonne", "valeur", "z_score"]
    if date_col:
        cols = ["machine_id", "date", "colonne", "valeur", "z_score"]
    if not rows:
        return pd.DataFrame(columns=cols)

    return (
        pd.DataFrame(rows)[cols]
        .sort_values(["machine_id", "colonne"] + (["date"] if date_col else []))
        .reset_index(drop=True)
    )
