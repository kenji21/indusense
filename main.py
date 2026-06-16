import sys

from ingestor import load_incidents, incident_report_per_operator_and_severity

INCIDENTS_PATH = "data/releves_incidents.csv"

COMMANDS = {
    "report": "Affiche le rapport incidents par opérateur et sévérité",
}


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "report":
        df = load_incidents(INCIDENTS_PATH)
        incident_report_per_operator_and_severity(df)
    else:
        print("Usage: python main.py <commande>")
        print("\nCommandes disponibles :")
        for name, desc in COMMANDS.items():
            print(f"  {name:<12} {desc}")


if __name__ == "__main__":
    main()
