import sys

import matplotlib.pyplot as plt

from ingestor import *

INCIDENTS_PATH = "data/releves_incidents.csv"

COMMANDS = {
    "ingest_incidents": "Charge et résume le fichier incidents (lignes, colonnes, nulls, doublons)",
}


def ingest_incidents():
    df = load_incidents(INCIDENTS_PATH)
    print(f"Fichier chargé : {INCIDENTS_PATH}")
    print(f"  Lignes      : {len(df)}")
    print(f"  Colonnes    : {len(df.columns)}")
    print(f"  Doublons    : {df.duplicated().sum()}")
    print(f"  Valeurs NaN : {df.isnull().sum().sum()}")
    print(f"\nColonnes : {', '.join(df.columns.tolist())}")
    fig_operator = incident_report_per_operator_and_severity(df)
    fig_shift = incident_report_per_shift(df)
    plt.show()

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "ingest_incidents":
        ingest_incidents()
    else:
        print("Usage: python main.py <commande>")
        print("\nCommandes disponibles :")
        for name, desc in COMMANDS.items():
            print(f"  {name:<12} {desc}")


if __name__ == "__main__":
    main()
