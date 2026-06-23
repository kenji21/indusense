from sqlalchemy import Column, DateTime, Integer, JSON, String, UniqueConstraint

from indusense.db.base import Base


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    __table_args__ = (UniqueConstraint("tag", "layer", name="uq_pipeline_runs_tag_layer"),)

    id         = Column(Integer, primary_key=True, autoincrement=True)
    tag        = Column(String(32), nullable=False)   # DATA_PIPELINE_VERSION
    layer      = Column(String(16), nullable=False)   # 'raw_telemetry' | 'raw_incidents' | 'bronze' | 'silver' | 'gold'
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    git_sha    = Column(String(40))
    row_count  = Column(Integer)
    params     = Column(JSON)
    csv_path   = Column(String(256))
