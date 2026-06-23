import pandas as pd
from sqlalchemy import text

from indusense.db.base import Base
from indusense.db.models.silver_telemetry import SilverTelemetry
from indusense.db.session import get_engine
from indusense.pipeline import (
    ensure_pipeline_runs_table,
    finalize_run,
    get_pipeline_tag,
    resolve_run,
)

# Seuil de détection des valeurs Fahrenheit : une température > 80 °C est suspecte
_FAHRENHEIT_THRESHOLD = 80.0


def silver_from_bronze() -> None:
    engine = get_engine()
    ensure_pipeline_runs_table(engine)

    tag = get_pipeline_tag()
    run_id = resolve_run(
        engine,
        layer="silver",
        tag=tag,
        params={"source": "bronze_telemetry"},
    )

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS silver_telemetry"))

    Base.metadata.create_all(engine, tables=[SilverTelemetry.__table__])

    df = pd.read_sql(
        "SELECT id, machine_id, recorded_at, temperature_c, pressure_bar, "
        "rotation_mean_rpm, voltage_mean_v, pieces_produced "
        "FROM bronze_telemetry ORDER BY machine_id, recorded_at, id",
        con=engine,
    )

    # 1. Déduplication : clé (machine_id, recorded_at), on garde la première occurrence
    n_before = len(df)
    df = df.drop_duplicates(subset=["machine_id", "recorded_at"], keep="first").copy()
    n_dedup = n_before - len(df)

    # 2. Normalisation des unités : temperature > 80 °C → valeur en °F, on convertit
    mask_fahrenheit = df["temperature_c"].notna() & (df["temperature_c"] > _FAHRENHEIT_THRESHOLD)
    df["silver_unit_converted"] = mask_fahrenheit
    df.loc[mask_fahrenheit, "temperature_c"] = (df.loc[mask_fahrenheit, "temperature_c"] - 32) * 5 / 9

    df = df.rename(columns={"id": "bronze_id"})
    df["run_id"] = run_id
    df.to_sql("silver_telemetry", con=engine, if_exists="append", index=False)

    n_converted = int(mask_fahrenheit.sum())
    finalize_run(
        engine,
        run_id,
        row_count=len(df),
        comment=f"{n_dedup} doublon(s) supprimé(s) ; {n_converted} conversion(s) °F→°C",
    )

    print(f"silver_telemetry    : {len(df)} lignes")
    print(f"  doublons supprimés: {n_dedup}")
    print(f"  conversions °F→°C : {n_converted}")
    print(f"[pipeline_runs]     : layer=silver  tag={tag}  run_id={run_id}")
