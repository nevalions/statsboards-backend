"""add_missing_match_stats_throttle_table

Revision ID: aef5fea559e2
Revises: c2f371562f41
Create Date: 2026-01-28 09:29:13.840588

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "aef5fea559e2"
down_revision: Union[str, None] = "c2f371562f41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS match_stats_throttle (
        match_id INTEGER PRIMARY KEY NOT NULL,
        last_notified_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
    );
    """)

    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_match_stats_throttle_notified_at 
    ON match_stats_throttle(last_notified_at);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS match_stats_throttle CASCADE;")
