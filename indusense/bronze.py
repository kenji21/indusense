import pandas as pd
from sqlalchemy import text

from indusense.db.base import Base
from indusense.db.models.bronze_incident import BronzeIncident
from indusense.db.models.bronze_machine import BronzeMachine
from indusense.db.models.bronze_maintenance import BronzeMaintenance
from indusense.db.models.bronze_telemetry import BronzeInvalidReason, BronzeTelemetry
from indusense.db.session import get_engine
from indusense.pipeline import (
    ensure_pipeline_runs_table,
    finalize_run,
    get_pipeline_tag,
    resolve_run,
)


def _warn_invalid(warnings: list, df_bad: "pd.DataFrame", table: str, key_col: str) -> None:
    msg = f"[WARN] {table} : {len(df_bad)} ligne(s) ignorée(s) ({key_col} inconnu)"
    warnings.append(msg)
    print(f"\n  {msg}")
    with pd.option_context("display.max_rows", None, "display.max_columns", None, "display.width", 0):
        print(df_bad.to_string(index=False))
    print()


def bronze_from_raw() -> None:
    engine = get_engine()
    ensure_pipeline_runs_table(engine)

    tag = get_pipeline_tag()
    run_id = resolve_run(
        engine,
        layer="bronze",
        tag=tag,
        params={
            "source_telemetry": "data/telemetry.csv",
            "source_incidents": "artifacts/releves_incidents.anonymised.csv",
        },
    )

    # DROP + CREATE garantit que le schéma en base est toujours en phase avec les modèles
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS bronze_telemetry"))
        conn.execute(text("DROP TABLE IF EXISTS bronze_incidents"))
        conn.execute(text("DROP TABLE IF EXISTS bronze_maintenance"))
        conn.execute(text("DROP TABLE IF EXISTS bronze_machine CASCADE"))

    Base.metadata.create_all(
        engine,
        tables=[
            BronzeMachine.__table__,
            BronzeMaintenance.__table__,
            BronzeTelemetry.__table__,
            BronzeIncident.__table__,
        ],
    )

    warnings: list[str] = []
    n_mach = _transform_machine(engine, run_id)
    valid_machines = set(
        pd.read_sql("SELECT machine_code FROM bronze_machine", con=engine)["machine_code"]
    )
    n_maint = _transform_maintenance(engine, valid_machines, run_id, warnings)
    n_tel, n_tel_invalid, tel_summary = _transform_telemetry(engine, valid_machines, run_id, warnings)
    n_inc, n_inc_invalid = _transform_incidents(engine, valid_machines, run_id, warnings)

    parts = [tel_summary] if tel_summary else []
    parts += warnings
    comment = "\n".join(parts) if parts else None
    finalize_run(engine, run_id, row_count=n_mach + n_maint + n_tel + n_inc, comment=comment)

    print(f"bronze_machine      : {n_mach} lignes")
    print(f"bronze_maintenance  : {n_maint} lignes")
    print(f"bronze_telemetry    : {n_tel} lignes  ({n_tel_invalid} invalides)")
    print(f"bronze_incidents    : {n_inc} lignes  ({n_inc_invalid} invalides)")
    print(f"[pipeline_runs]     : layer=bronze  tag={tag}  run_id={run_id}")


def _transform_machine(engine, run_id: int) -> int:
    df = pd.read_sql("SELECT * FROM machine ORDER BY machine_code", con=engine)
    df["run_id"] = run_id
    df.to_sql("bronze_machine", con=engine, if_exists="append", index=False)
    return len(df)


def _transform_maintenance(engine, valid_machines: set, run_id: int, warnings: list) -> int:
    df = pd.read_sql("SELECT * FROM maintenance ORDER BY maintenance_at", con=engine)

    # Dates → UTC ISO 8601 (déjà TIMESTAMPTZ dans la source, on normalise quand même)
    for col in ("maintenance_at", "created_at", "updated_at"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True)

    mask_invalid = ~df["machine_code"].isin(valid_machines)
    if mask_invalid.any():
        _warn_invalid(warnings, df[mask_invalid], "maintenance", "machine_code")
    df = df[~mask_invalid]

    df["run_id"] = run_id
    df.to_sql("bronze_maintenance", con=engine, if_exists="append", index=False)
    return len(df)


def _transform_telemetry(engine, valid_machines: set, run_id: int, warnings: list) -> tuple[int, int]:
    df = pd.read_sql("SELECT * FROM raw_telemetry ORDER BY recorded_at", con=engine)
    df = df.drop(columns=["id"], errors="ignore")

    # Dates → UTC ISO 8601
    df["recorded_at"] = pd.to_datetime(df["recorded_at"], utc=True)

    mask_invalid = ~df["machine_id"].isin(valid_machines)
    if mask_invalid.any():
        _warn_invalid(warnings, df[mask_invalid], "telemetry", "machine_id")
    df = df[~mask_invalid]

    # Détection des invalides
    mask_duplicate = df.groupby(["machine_id", "recorded_at"])["machine_id"].transform("size") > 1
    mask_missing_temp = df["temperature_c"].isna()
    mask_missing_pres = df["pressure_bar"].isna()
    mask_missing_rpm = df["rotation_mean_rpm"].isna()
    mask_missing_voltage = df["voltage_mean_v"].isna()
    mask_missing_pieces = df["pieces_produced"].isna()

    df["bronze_data_valid"] = ~(
        mask_duplicate
        | mask_missing_temp
        | mask_missing_pres
        | mask_missing_rpm
        | mask_missing_voltage
        | mask_missing_pieces
    )

    # Priorité : duplicate > missing_temperature > missing_pressure > missing_rotation_mean_rpm > missing_voltage_mean_v > missing_pieces_produced
    df["bronze_data_comment"] = None
    df.loc[mask_missing_pieces, "bronze_data_comment"] = BronzeInvalidReason.missing_pieces_produced.value
    df.loc[mask_missing_voltage, "bronze_data_comment"] = BronzeInvalidReason.missing_voltage_mean_v.value
    df.loc[mask_missing_rpm, "bronze_data_comment"] = BronzeInvalidReason.missing_rotation_mean_rpm.value
    df.loc[mask_missing_pres, "bronze_data_comment"] = BronzeInvalidReason.missing_pressure.value
    df.loc[mask_missing_temp, "bronze_data_comment"] = BronzeInvalidReason.missing_temperature.value
    df.loc[mask_duplicate, "bronze_data_comment"] = BronzeInvalidReason.duplicate.value

    df["run_id"] = run_id
    df.to_sql("bronze_telemetry", con=engine, if_exists="append", index=False)

    counts = df["bronze_data_comment"].value_counts()
    summary = " ; ".join(f"{v} {k}" for k, v in counts.items()) if not counts.empty else None
    return len(df), int((~df["bronze_data_valid"]).sum()), summary


def _transform_incidents(engine, valid_machines: set, run_id: int, warnings: list) -> tuple[int, int]:
    df = pd.read_sql("SELECT * FROM raw_incidents ORDER BY occurred_at", con=engine)
    df = df.drop(columns=["id"], errors="ignore")

    # Dates → UTC ISO 8601
    df["occurred_at"] = pd.to_datetime(df["occurred_at"], utc=True)

    mask_invalid = ~df["machine_id"].isin(valid_machines)
    if mask_invalid.any():
        _warn_invalid(warnings, df[mask_invalid], "incidents", "machine_id")
    df = df[~mask_invalid]

    # Règle : severity doit être entre 1 et 5 inclus
    df["bronze_data_valid"] = df["severity"].between(1, 5)

    df["run_id"] = run_id
    df.to_sql("bronze_incidents", con=engine, if_exists="append", index=False)
    return len(df), int((~df["bronze_data_valid"]).sum())
