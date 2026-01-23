"""add_started_at_ms_to_gameclock

Revision ID: 20063b48a50b
Revises: stab132_clock_status_only_notify
Create Date: 2026-01-23 21:38:15.279565

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20063b48a50b"
down_revision: Union[str, None] = "stab132_clock_status_only_notify"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("gameclock", sa.Column("started_at_ms", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("gameclock", "started_at_ms")
