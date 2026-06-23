import os
import subprocess
from datetime import datetime, timezone

from sqlalchemy import select, update

from indusense.db.base import Base
from indusense.db.models.pipeline_run import PipelineRun


def get_pipeline_tag() -> str:
    tag = os.environ.get("DATA_PIPELINE_VERSION")
    if not tag:
        raise EnvironmentError(
            "DATA_PIPELINE_VERSION non défini. Ajoutez-le dans .env (ex: DATA_PIPELINE_VERSION=v1)"
        )
    return tag


def ensure_pipeline_runs_table(engine) -> None:
    Base.metadata.create_all(engine, tables=[PipelineRun.__table__], checkfirst=True)


def resolve_run(
    engine,
    layer: str,
    tag: str,
    params: dict | None = None,
) -> int:
    now = datetime.now(tz=timezone.utc)
    sha = _git_sha()

    with engine.begin() as conn:
        row = conn.execute(
            select(PipelineRun.id).where(
                PipelineRun.tag == tag,
                PipelineRun.layer == layer,
            )
        ).fetchone()

        if row:
            conn.execute(
                update(PipelineRun)
                .where(PipelineRun.id == row.id)
                .values(updated_at=now, git_sha=sha, params=params or {})
            )
            return row.id

        result = conn.execute(
            PipelineRun.__table__.insert().values(
                tag=tag,
                layer=layer,
                created_at=now,
                updated_at=now,
                git_sha=sha,
                params=params or {},
            )
        )
        return result.inserted_primary_key[0]


def finalize_run(
    engine,
    run_id: int,
    row_count: int,
    csv_path: str | None = None,
    comment: str | None = None,
) -> None:
    now = datetime.now(tz=timezone.utc)
    with engine.begin() as conn:
        conn.execute(
            update(PipelineRun)
            .where(PipelineRun.id == run_id)
            .values(row_count=row_count, csv_path=csv_path, updated_at=now, comment=comment)
        )


def _git_sha() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=os.path.dirname(__file__),
        ).stdout.strip()
    except Exception:
        return None
