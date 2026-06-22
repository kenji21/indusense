import pandas as pd
from sqlalchemy import text

from indusense.db.base import Base
from indusense.db.models.bronze_incident import BronzeIncident
from indusense.db.models.bronze_machine import BronzeMachine
from indusense.db.models.bronze_maintenance import BronzeMaintenance
from indusense.db.models.bronze_telemetry import BronzeTelemetry
from indusense.db.session import get_engine


def _warn_invalid(df_bad: "pd.DataFrame", table: str, key_col: str) -> None:
    print(f"\n  [WARN] {table} : {len(df_bad)} ligne(s) ignorée(s) ({key_col} inconnu)")
    with pd.option_context("display.max_rows", None, "display.max_columns", None, "display.width", 0):
        print(df_bad.to_string(index=False))
    print()


def bronze_from_raw() -> None:
    engine = get_engine()

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

    n_mach = _transform_machine(engine)
    valid_machines = set(
        pd.read_sql("SELECT machine_code FROM bronze_machine", con=engine)["machine_code"]
    )
    n_maint = _transform_maintenance(engine, valid_machines)
    n_tel, n_tel_invalid = _transform_telemetry(engine, valid_machines)
    n_inc, n_inc_invalid = _transform_incidents(engine, valid_machines)

    print(f"bronze_machine      : {n_mach} lignes")
    print(f"bronze_maintenance  : {n_maint} lignes")
    print(f"bronze_telemetry    : {n_tel} lignes  ({n_tel_invalid} invalides)")
    print(f"bronze_incidents    : {n_inc} lignes  ({n_inc_invalid} invalides)")


def _transform_machine(engine) -> int:
    df = pd.read_sql("SELECT * FROM machine ORDER BY machine_code", con=engine)
    df.to_sql("bronze_machine", con=engine, if_exists="append", index=False)
    return len(df)


def _transform_maintenance(engine, valid_machines: set) -> int:
    df = pd.read_sql("SELECT * FROM maintenance ORDER BY maintenance_at", con=engine)

    # Dates → UTC ISO 8601 (déjà TIMESTAMPTZ dans la source, on normalise quand même)
    for col in ("maintenance_at", "created_at", "updated_at"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True)

    mask_invalid = ~df["machine_code"].isin(valid_machines)
    if mask_invalid.any():
        _warn_invalid(df[mask_invalid], "maintenance", "machine_code")
    df = df[~mask_invalid]

    df.to_sql("bronze_maintenance", con=engine, if_exists="append", index=False)
    return len(df)


def _transform_telemetry(engine, valid_machines: set) -> tuple[int, int]:
    df = pd.read_sql("SELECT * FROM raw_telemetry ORDER BY recorded_at", con=engine)
    df = df.drop(columns=["id"], errors="ignore")

    # Dates → UTC ISO 8601
    df["recorded_at"] = pd.to_datetime(df["recorded_at"], utc=True)

    mask_invalid = ~df["machine_id"].isin(valid_machines)
    if mask_invalid.any():
        _warn_invalid(df[mask_invalid], "telemetry", "machine_id")
    df = df[~mask_invalid]

    # Règle : une seule télémétrie par (machine_id, recorded_at)
    df["bronze_data_valid"] = (
        df.groupby(["machine_id", "recorded_at"])["machine_id"].transform("size") == 1
    )

    df.to_sql("bronze_telemetry", con=engine, if_exists="append", index=False)
    return len(df), int((~df["bronze_data_valid"]).sum())


def _transform_incidents(engine, valid_machines: set) -> tuple[int, int]:
    df = pd.read_sql("SELECT * FROM raw_incidents ORDER BY occurred_at", con=engine)
    df = df.drop(columns=["id"], errors="ignore")

    # Dates → UTC ISO 8601
    df["occurred_at"] = pd.to_datetime(df["occurred_at"], utc=True)

    mask_invalid = ~df["machine_id"].isin(valid_machines)
    if mask_invalid.any():
        _warn_invalid(df[mask_invalid], "incidents", "machine_id")
    df = df[~mask_invalid]

    # Règle : severity doit être entre 1 et 5 inclus
    df["bronze_data_valid"] = df["severity"].between(1, 5)

    df.to_sql("bronze_incidents", con=engine, if_exists="append", index=False)
    return len(df), int((~df["bronze_data_valid"]).sum())
