import pandas as pd


def extract_report_data(df: pd.DataFrame) -> dict:
    signal_cols = [c for c in df.columns if c.startswith("type_")]

    def pivot_severity(group_col):
        p = df.groupby([group_col, "severity"]).size().unstack(fill_value=0)
        p = p.reindex(columns=[1, 2, 3], fill_value=0)
        return {str(k): v.to_dict() for k, v in p.iterrows()}

    corr = df[["severity"] + signal_cols].corr()

    return {
        "operator_severity":  pivot_severity("operator_name"),
        "shift_severity":     pivot_severity("shift"),
        "machine":            df.groupby("machine_id").size().to_dict(),
        "signal":             {c.removeprefix("type_"): int(df[c].sum()) for c in signal_cols},
        "confidence":         df["confidence_score"].value_counts().sort_index().to_dict(),
        "signal_correlation": {c: corr[c].to_dict() for c in corr.columns},
    }

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
