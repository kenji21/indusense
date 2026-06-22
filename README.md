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

| Variable       | Description                                  | Exemple                                          |
|----------------|----------------------------------------------|--------------------------------------------------|
| `ANON_SALT`    | Sel de hachage pour l'anonymisation          | `une_valeur_secrete`                             |
| `DATABASE_URL` | URL de connexion SQLAlchemy à PostgreSQL     | `postgresql://dbuser:dbpassword@localhost:5432/db` |

---

## Base de données

### Démarrer PostgreSQL (Docker)

```bash
cd pgdocker
cp .env.sample .env   # puis éditer si besoin
docker compose up -d
```

### Modèles SQLAlchemy

Deux tables sont définies dans `indusense/db/models/` :

**`telemetry`** — relevés de capteurs (température, pression, vibration) par machine et horodatage.

| Colonne       | Type      | Description                    |
|---------------|-----------|--------------------------------|
| `id`          | Integer   | Clé primaire                   |
| `machine_id`  | String    | Identifiant de la machine      |
| `recorded_at` | DateTime  | Horodatage du relevé           |
| `temperature` | Float     | Température (°C), nullable     |
| `pressure`    | Float     | Pression hydraulique, nullable |
| `vibration`   | Float     | Niveau de vibration, nullable  |

**`incidents`** — relevés d'incidents opérateurs (issus du CSV anonymisé).

| Colonne                 | Type        | Description                              |
|-------------------------|-------------|------------------------------------------|
| `id`                    | Integer     | Clé primaire                             |
| `machine_id`            | String      | Identifiant de la machine                |
| `occurred_at`           | DateTime    | Date/heure de l'incident, nullable       |
| `operator_name`         | String      | Opérateur (anonymisé `OP-<hash>`)        |
| `operator_badge`        | String      | Badge (anonymisé `BADGE-<hash>`)         |
| `severity`              | SmallInteger| Sévérité 1 / 2 / 3                      |
| `shift`                 | String      | Poste (matin / après-midi / nuit)        |
| `comment`               | Text        | Commentaire libre, nullable              |
| `confidence_score`      | Float       | Score de confiance calculé (0–1)         |
| `type_surchauffe`       | Boolean     | Signal : surchauffe                      |
| `type_baisse_pression`  | Boolean     | Signal : baisse de pression              |
| `type_vibration`        | Boolean     | Signal : vibration anormale              |
| `type_bruit_mecanique`  | Boolean     | Signal : bruit mécanique                 |
| `type_surconsommation`  | Boolean     | Signal : surconsommation                 |
| `type_blocage_mecanique`| Boolean     | Signal : blocage mécanique               |
| `type_alarme_capteur`   | Boolean     | Signal : alarme capteur                  |
| `type_arret_urgence`    | Boolean     | Signal : arrêt d'urgence                 |
| `type_defaut_qualite`   | Boolean     | Signal : défaut qualité                  |

### Charger les données initiales

```bash
set -o allexport && source pgdocker/.env && set +o allexport
docker exec -i pgdocker-db-1 \
  psql -U "${DB_USER:-dbuser}" -d "${DB_NAME:-db}" \
  < data/machine.sql
```

### Migrations (Alembic)

Générer et appliquer la première migration :

```bash
alembic revision --autogenerate -m "init telemetry incidents"
alembic upgrade head
```

Rollback d'une version :

```bash
alembic downgrade -1
```

---

## Commandes principales

### Anonymiser les données brutes

```bash
uv run python main.py anonymize
```

Lit `data/releves_incidents.csv`, applique le hachage des opérateurs, écrit `artifacts/releves_incidents.anonymised.csv`.

### Générer le rapport d'analyse

```bash
uv run python main.py ingest_incidents
```

Charge le CSV anonymisé, calcule les scores de confiance, génère graphiques et rapport Markdown dans `artifacts/ingestions/incidents/<horodatage>/`.

---

## Structure du projet

```
indusense/
  db/
    base.py            — DeclarativeBase SQLAlchemy
    session.py         — get_engine() / get_session() (lazy, lit DATABASE_URL)
    models/
      telemetry.py     — modèle Telemetry
      incident.py      — modèle Incident
  alembic/             — migrations Alembic
  ingestor/
    loader.py          — chargement CSV
    anonymizer.py      — anonymisation opérateurs
    inspector.py       — extraction métriques et graphiques
    reports.py         — génération figures matplotlib
alembic.ini            — configuration Alembic (pointe sur indusense/alembic/)
pgdocker/              — Docker Compose PostgreSQL + PgAdmin
artifacts/             — sorties générées (CSV anonymisé, rapports, graphiques)
main.py                — point d'entrée CLI
```
