import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
from sqlalchemy import text

from indusense.ingestor import *

INCIDENTS_RAW_PATH      = "data/releves_incidents.csv"
INCIDENTS_ANON_PATH     = "artifacts/releves_incidents.anonymised.csv"
TELEMETRY_RAW_PATH      = "data/telemetry.csv"
MACHINE_SQL_PATH        = "data/machine.sql"

COMMANDS = {
    "anonymize":        "Anonymise les opérateurs et écrit artifacts/releves_incidents.anonymised.csv",
    "ingest_machine":   "Charge data/machine.sql → tables machine + maintenance (avec run_id)",
    "ingest_incidents": "Charge les incidents anonymisés, génère les rapports dans artifacts/",
    "ingest_telemetry": "Charge data/telemetry.csv et insère les données brutes dans raw_telemetry (PostgreSQL)",
    "bronze_from_raw":  "Construit les tables bronze depuis raw (rejouable : TRUNCATE + INSERT, dates UTC, FK machine)",
}


def ingest_machine():
    if not Path(MACHINE_SQL_PATH).exists():
        print(f"Fichier introuvable : {MACHINE_SQL_PATH}")
        sys.exit(1)

    from indusense.db.session import get_engine
    from indusense.pipeline import ensure_pipeline_runs_table, finalize_run, get_pipeline_tag, resolve_run

    engine = get_engine()
    ensure_pipeline_runs_table(engine)

    # machine.sql définit son propre schéma — on l'exécute entièrement
    sql_content = Path(MACHINE_SQL_PATH).read_text()
    with engine.begin() as conn:
        conn.execute(text(sql_content))

    # Ajoute run_id si absent, puis le valorise
    tag = get_pipeline_tag()
    run_id = resolve_run(engine, layer="raw_machine", tag=tag, params={"source": MACHINE_SQL_PATH})

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE machine ADD COLUMN IF NOT EXISTS run_id INTEGER"))
        conn.execute(text("ALTER TABLE maintenance ADD COLUMN IF NOT EXISTS run_id INTEGER"))
        conn.execute(text("UPDATE machine SET run_id = :rid WHERE run_id IS NULL"), {"rid": run_id})
        conn.execute(text("UPDATE maintenance SET run_id = :rid WHERE run_id IS NULL"), {"rid": run_id})

    n_machine = engine.connect().execute(text("SELECT COUNT(*) FROM machine")).scalar()
    n_maint   = engine.connect().execute(text("SELECT COUNT(*) FROM maintenance")).scalar()
    finalize_run(engine, run_id, row_count=n_machine + n_maint)

    print(f"machine             : {n_machine} lignes")
    print(f"maintenance         : {n_maint} lignes")
    print(f"[pipeline_runs]     : layer=raw_machine  tag={tag}  run_id={run_id}")


def anonymize():
    df = load_incidents(INCIDENTS_RAW_PATH)
    df = anonymize_operators(df)
    out = Path(INCIDENTS_ANON_PATH)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Fichier anonymisé : {out} ({len(df)} lignes)")


def ingest_incidents():
    if not Path(INCIDENTS_ANON_PATH).exists():
        print(f"Fichier anonymisé introuvable : {INCIDENTS_ANON_PATH}")
        print("Lancez d'abord : python main.py anonymize")
        sys.exit(1)

    from indusense.db.session import get_engine
    from indusense.pipeline import ensure_pipeline_runs_table, finalize_run, get_pipeline_tag, resolve_run

    df = load_incidents(INCIDENTS_ANON_PATH)

    df_db = incidents_to_db_df(df)
    engine = get_engine()
    ensure_pipeline_runs_table(engine)

    from indusense.db.base import Base
    from indusense.db.models.incident import Incident
    Base.metadata.create_all(engine, tables=[Incident.__table__], checkfirst=True)

    tag = get_pipeline_tag()
    run_id = resolve_run(engine, layer="raw_incidents", tag=tag, params={"source": INCIDENTS_ANON_PATH})

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE raw_incidents RESTART IDENTITY"))
    df_db["run_id"] = run_id
    df_db.to_sql("raw_incidents", con=engine, if_exists="append", index=False)
    finalize_run(engine, run_id, row_count=len(df_db))
    print(f"{len(df_db)} lignes insérées dans raw_incidents.")
    print(f"[pipeline_runs]     : layer=raw_incidents  tag={tag}  run_id={run_id}")

    df = compute_confidence_score(df)

    print(f"Fichier chargé : {INCIDENTS_ANON_PATH}")
    print(f"  Lignes      : {len(df)}")
    print(f"  Colonnes    : {len(df.columns)}")
    print(f"  Doublons    : {df.duplicated().sum()}")
    print(f"  Valeurs NaN : {df.isnull().sum().sum()}")
    print(f"\nColonnes : {', '.join(df.columns.tolist())}")

    stamp = datetime.now().strftime("%Y%m%d%H%M")
    out_dir = Path("artifacts/ingestions/incidents") / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    figures = {
        "shift_severity":     incident_report_per_shift(df),
        "day_severity":       incident_report_per_day_and_severity(df),
        "week_severity":      incident_report_per_week_and_severity(df),
        "signal":             incident_report_per_signal(df),
        "machine":            incident_report_per_machine(df),
        "confidence":         incident_report_confidence(df),
        "signal_correlation": incident_report_signal_correlation(df),
    }

    for name, fig in figures.items():
        path = out_dir / f"{name}.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        print(f"  Sauvegardé : {path}")

    data = extract_report_data(df)
    data["meta"] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": INCIDENTS_ANON_PATH,
        "rows": len(df),
        "columns": len(df.columns),
        "duplicates": int(df.duplicated().sum()),
        "nulls": int(df.isnull().sum().sum()),
    }
    (out_dir / "data.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"  Sauvegardé : {out_dir / 'data.json'}")

    md_lines = [
        f"# Rapport incidents — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Résumé",
        f"- Source : `{INCIDENTS_ANON_PATH}`",
        f"- Lignes : {len(df)} | Colonnes : {len(df.columns)}",
        f"- Doublons : {int(df.duplicated().sum())} | Valeurs NaN : {int(df.isnull().sum().sum())}",
        "",
        "## Graphiques",
    ]
    titles = {
        "shift_severity":     "Par shift et sévérité",
        "day_severity":       "Par jour de la semaine et sévérité",
        "week_severity":      "Par semaine et sévérité",
        "signal":             "Par type de signal",
        "machine":            "Par machine",
        "confidence":         "Indice de confiance des signalements",
        "signal_correlation": "Corrélation signaux / incidents",
    }
    for name, title in titles.items():
        md_lines += ["", f"### {title}", f"![{title}]({name}.png)"]

    (out_dir / "report.md").write_text("\n".join(md_lines))
    print(f"  Sauvegardé : {out_dir / 'report.md'}")

    print(f"\nRapport généré dans : {out_dir}")


def bronze_from_raw_cmd():
    from indusense.bronze import bronze_from_raw
    bronze_from_raw()


def ingest_telemetry():
    if not Path(TELEMETRY_RAW_PATH).exists():
        print(f"Fichier introuvable : {TELEMETRY_RAW_PATH}")
        sys.exit(1)

    from indusense.db.session import get_engine
    from indusense.pipeline import ensure_pipeline_runs_table, finalize_run, get_pipeline_tag, resolve_run

    df = load_telemetry(TELEMETRY_RAW_PATH)
    df_db = telemetry_to_db_df(df)

    print(f"Fichier chargé : {TELEMETRY_RAW_PATH}")
    print(f"  Lignes    : {len(df_db)}")
    print(f"  Colonnes  : {', '.join(df_db.columns.tolist())}")
    print(f"  Doublons  : {df_db.duplicated().sum()}")
    print(f"  NaN       : {df_db.isnull().sum().sum()} ({df_db.isnull().any(axis=1).sum()} lignes)")

    engine = get_engine()
    ensure_pipeline_runs_table(engine)

    from indusense.db.base import Base
    from indusense.db.models.telemetry import Telemetry
    Base.metadata.create_all(engine, tables=[Telemetry.__table__], checkfirst=True)

    tag = get_pipeline_tag()
    run_id = resolve_run(engine, layer="raw_telemetry", tag=tag, params={"source": TELEMETRY_RAW_PATH})

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE raw_telemetry RESTART IDENTITY"))
    df_db["run_id"] = run_id
    df_db.to_sql("raw_telemetry", con=engine, if_exists="append", index=False)
    finalize_run(engine, run_id, row_count=len(df_db))
    print(f"\n{len(df_db)} lignes insérées dans raw_telemetry.")
    print(f"[pipeline_runs]     : layer=raw_telemetry  tag={tag}  run_id={run_id}")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "anonymize":
        anonymize()
    elif cmd == "ingest_machine":
        ingest_machine()
    elif cmd == "ingest_incidents":
        ingest_incidents()
    elif cmd == "ingest_telemetry":
        ingest_telemetry()
    elif cmd == "bronze_from_raw":
        bronze_from_raw_cmd()
    else:
        print("Usage: python main.py <commande>")
        print("\nCommandes disponibles :")
        for name, desc in COMMANDS.items():
            print(f"  {name:<12} {desc}")


if __name__ == "__main__":
    main()
