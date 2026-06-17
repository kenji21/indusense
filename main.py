import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt

from ingestor import *

INCIDENTS_RAW_PATH      = "data/releves_incidents.csv"
INCIDENTS_ANON_PATH     = "artifacts/releves_incidents.anonymised.csv"

COMMANDS = {
    "anonymize":       "Anonymise les opérateurs et écrit artifacts/releves_incidents.anonymised.csv",
    "ingest_incidents": "Charge les incidents anonymisés, génère les rapports dans artifacts/",
}


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

    df = load_incidents(INCIDENTS_ANON_PATH)
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


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "anonymize":
        anonymize()
    elif cmd == "ingest_incidents":
        ingest_incidents()
    else:
        print("Usage: python main.py <commande>")
        print("\nCommandes disponibles :")
        for name, desc in COMMANDS.items():
            print(f"  {name:<12} {desc}")


if __name__ == "__main__":
    main()
