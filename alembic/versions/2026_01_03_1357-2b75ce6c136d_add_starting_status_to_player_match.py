"""add_starting_status_to_player_match

Revision ID: 2b75ce6c136d
Revises: 9fc1194c013a
Create Date: 2026-01-03 13:57:08.140963

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2b75ce6c136d"
down_revision: Union[str, None] = "9fc1194c013a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "player_match",
        sa.Column("is_starting", sa.Boolean(), nullable=True, server_default="false"),
    )
    op.add_column("player_match", sa.Column("starting_type", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("player_match", "starting_type")
    op.drop_column("player_match", "is_starting")
