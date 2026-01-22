"""

Revision ID: stab127_clock_versions
Revises: stab100_event_trigger
Create Date: 2026-01-22 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "stab127_clock_versions"
down_revision: Union[str, None] = "stab100_event_trigger"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "gameclock",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "playclock",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade():
    op.drop_column("playclock", "version")
    op.drop_column("gameclock", "version")
