import pandas as pd

_DATE_COLS = ("date", "timestamp", "recorded_at", "datetime")

_TELEMETRY_COLS = [
    "machine_id",
    "recorded_at",
    "temperature_c",
    "pressure_bar",
    "rotation_mean_rpm",
    "voltage_mean_v",
    "pieces_produced",
]

_INCIDENT_COLS = [
    "machine_id",
    "occurred_at",
    "operator_name",
    "operator_badge",
    "severity",
    "shift",
    "comment",
    "type_surchauffe",
    "type_baisse_pression",
    "type_vibration",
    "type_bruit_mecanique",
    "type_surconsommation",
    "type_blocage_mecanique",
    "type_alarme_capteur",
    "type_arret_urgence",
    "type_defaut_qualite",
]

_INCIDENT_BOOL_COLS = [c for c in _INCIDENT_COLS if c.startswith("type_")]


def load_incidents(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def load_telemetry(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    date_col = next((c for c in df.columns if c in _DATE_COLS), None)
    if date_col and date_col != "recorded_at":
        df = df.rename(columns={date_col: "recorded_at"})
    if "recorded_at" in df.columns:
        df["recorded_at"] = pd.to_datetime(df["recorded_at"])
    return df


def telemetry_to_db_df(df: pd.DataFrame) -> pd.DataFrame:
    """Retourne uniquement les colonnes attendues par raw_telemetry."""
    cols = [c for c in _TELEMETRY_COLS if c in df.columns]
    return df[cols]


def incidents_to_db_df(df: pd.DataFrame) -> pd.DataFrame:
    """Retourne les colonnes brutes attendues par raw_incidents (sans confidence_score)."""
    data = df.copy()
    # Normalise la colonne date → occurred_at
    date_col = next((c for c in data.columns if c in _DATE_COLS and c != "occurred_at"), None)
    if date_col:
        data = data.rename(columns={date_col: "occurred_at"})
    if "occurred_at" in data.columns:
        data["occurred_at"] = pd.to_datetime(data["occurred_at"], errors="coerce")
    # Garantit les booléens NOT NULL
    for col in _INCIDENT_BOOL_COLS:
        if col not in data.columns:
            data[col] = False
        else:
            data[col] = data[col].fillna(False).astype(bool)
    cols = [c for c in _INCIDENT_COLS if c in data.columns]
    return data[cols]
