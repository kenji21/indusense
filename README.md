# InduSense 4.0 — Détection de pannes machines

## KPI

Succès si le modèle propose les maintenances en anticipation des pannes.

## Stakeholders

- **Client / Business** : maximiser la production, minimiser les arrêts machines
- **Équipe maintenance** : éviter les interventions "sous pression"
- **Opérateurs** : signalement et traçabilité des incidents
- **IT / DSI / RSSI** : sécurité, conformité, hébergement
- **Juridique** : conformité RGPD, anonymisation des données

---

## Prérequis

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (gestionnaire de dépendances)
- Docker + Docker Compose (pour PostgreSQL)

## Installation

```bash
uv sync
cp .env.example .env
# éditer .env avec les valeurs réelles
```

## Variables d'environnement

Fichier `.env` à créer depuis `.env.example` :

| Variable                | Description                                       | Exemple                                            |
|-------------------------|---------------------------------------------------|----------------------------------------------------|
| `ANON_SALT`             | Sel de hachage pour l'anonymisation               | `une_valeur_secrete`                               |
| `DATABASE_URL`          | URL de connexion SQLAlchemy à PostgreSQL          | `postgresql://dbuser:dbpassword@localhost:5432/db` |
| `DATA_PIPELINE_VERSION` | Tag de versioning du run courant (obligatoire)    | `v1`                                               |

---

## Base de données

### Démarrer PostgreSQL (Docker)

```bash
cd pgdocker
cp .env.sample .env   # puis éditer si besoin
docker compose up -d
```

---

## Pipeline de données et traçabilité

### Architecture Bronze / Silver / Gold

```
data/telemetry.csv        data/releves_incidents.csv      data/machine.sql
        │                           │                            │
        ▼                           ▼                            ▼
 ingest_telemetry           ingest_incidents             (chargement SQL)
  → raw_telemetry             → raw_incidents          → machine + maintenance
        │                           │                            │
        └───────────────────────────┴────────────────────────────┘
                                    │
                              bronze_from_raw
                       → bronze_telemetry / bronze_incidents
                         bronze_machine / bronze_maintenance
                                    │
                          (silver — à venir)
                                    │
                           (gold — à venir)
```

Chaque table de données porte un `run_id` → `pipeline_runs.id`. La traçabilité d'une ligne gold vers les données raw se fait via `tag` + `machine_id` + fenêtre temporelle.

### Versioning des runs (`pipeline_runs`)

**Un `pipeline_run` = une étape du pipeline pour un tag.** Le tag est la valeur de `DATA_PIPELINE_VERSION`. La clé naturelle est `(tag, layer)`, enforced par une contrainte UNIQUE.

```
pipeline_runs
  id         — identifiant
  tag        — DATA_PIPELINE_VERSION (ex: 'v1')       ┐ UNIQUE
  layer      — 'raw_telemetry' | 'raw_incidents'       │
               'bronze' | 'silver' | 'gold'            ┘
  created_at — première exécution du run
  updated_at — mise à jour à chaque rejeu du même tag
  git_sha    — commit Git associé
  row_count  — nombre de lignes produites
  params     — paramètres de l'étape (sources CSV, seuils…)
  csv_path   — chemin du CSV exporté (gold uniquement)
```

**Comportement upsert :** rejouer une commande avec le même tag met à jour la ligne existante. Changer `DATA_PIPELINE_VERSION` ouvre un nouveau slot de comparaison.

```bash
# Pipeline complet en v1
uv run python main.py ingest_telemetry
uv run python main.py ingest_incidents
uv run python main.py bronze_from_raw

# Ouvrir v2 (ex : après modification d'un paramètre)
# → changer DATA_PIPELINE_VERSION=v2 dans .env puis relancer

# Inspecter tous les runs
uv run python -c "
import pandas as pd
from indusense.db.session import get_engine
print(pd.read_sql('SELECT id, tag, layer, row_count, updated_at FROM pipeline_runs ORDER BY id', get_engine()).to_string())
"
```

### Initialisation complète depuis zéro

```bash
# 1. Charger le référentiel machines (SQL seed)
docker exec -i pgdocker-db-1 psql -U dbuser -d db < data/machine.sql

# 2. Anonymiser les opérateurs
uv run python main.py anonymize

# 3. Ingestion raw
uv run python main.py ingest_telemetry
uv run python main.py ingest_incidents

# 4. Fabrication Bronze
uv run python main.py bronze_from_raw
```

---

## Commandes principales

| Commande           | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| `anonymize`        | Anonymise les opérateurs → `artifacts/releves_incidents.anonymised.csv`     |
| `ingest_telemetry` | Charge `data/telemetry.csv` → table `raw_telemetry`                         |
| `ingest_incidents` | Charge le CSV anonymisé → table `raw_incidents` + rapports dans `artifacts/`|
| `bronze_from_raw`  | Construit les tables `bronze_*` : normalisation UTC, FK, `bronze_data_valid` |

---

## Structure du projet

```
indusense/
  pipeline.py          — versioning : get_pipeline_tag, resolve_run, finalize_run
  bronze.py            — transformations Bronze (raw → bronze_*)
  db/
    base.py            — DeclarativeBase SQLAlchemy
    session.py         — get_engine() (lazy, lit DATABASE_URL)
    models/
      machine.py             — table machine (référentiel, chargé via SQL)
      telemetry.py           — table raw_telemetry (+ run_id)
      incident.py            — table raw_incidents (+ run_id)
      bronze_machine.py      — table bronze_machine (+ run_id)
      bronze_telemetry.py    — table bronze_telemetry (+ run_id, bronze_data_valid)
      bronze_incident.py     — table bronze_incidents (+ run_id, bronze_data_valid)
      bronze_maintenance.py  — table bronze_maintenance (+ run_id)
      pipeline_run.py        — table pipeline_runs (clé unique tag+layer)
  alembic/             — migrations Alembic
  ingestor/
    loader.py          — chargement CSV
    anonymizer.py      — anonymisation opérateurs
    inspector.py       — extraction métriques et scores de confiance
    detector.py        — détection d'anomalies (z-score)
    imputer.py         — analyse des valeurs manquantes
    reports.py         — génération figures matplotlib
alembic.ini            — configuration Alembic
pgdocker/              — Docker Compose PostgreSQL + PgAdmin
artifacts/             — sorties générées (CSV anonymisé, rapports, graphiques)
doc/
  gold_roadmap.md      — spécification complète du Gold dataset
main.py                — point d'entrée CLI
```
