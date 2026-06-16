import pandas as pd

SIGNAL_COLS = [c for c in [
    "type_surchauffe", "type_baisse_pression", "type_vibration",
    "type_bruit_mecanique", "type_surconsommation", "type_blocage_mecanique",
    "type_alarme_capteur", "type_arret_urgence", "type_defaut_qualite",
]]


def compute_confidence_score(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    signal_cols = [c for c in SIGNAL_COLS if c in data.columns]

    score = (
        data["comment"].notna().astype(float) * 0.4
        + (data[signal_cols].sum(axis=1) > 0).astype(float) * 0.4
        + data["operator_badge"].notna().astype(float) * 0.2
    )
    data["confidence_score"] = score.round(2)
    return data
