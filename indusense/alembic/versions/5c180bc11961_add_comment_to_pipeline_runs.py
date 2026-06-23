"""add_comment_to_pipeline_runs

Revision ID: 5c180bc11961
Revises: 
Create Date: 2026-06-23 09:10:52.055456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c180bc11961'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('pipeline_runs', sa.Column('comment', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('pipeline_runs', 'comment')
