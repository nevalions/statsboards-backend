"""is football qb lower added to scoreboard

Revision ID: e0ec44347ec5
Revises: cbc23a4c7596
Create Date: 2024-08-01 11:56:10.347457

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e0ec44347ec5"
down_revision: Union[str, None] = "cbc23a4c7596"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "scoreboard", sa.Column("is_home_football_qb_lower", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "scoreboard", sa.Column("is_away_football_qb_lower", sa.Boolean(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("scoreboard", "is_away_football_qb_lower")
    op.drop_column("scoreboard", "is_home_football_qb_lower")
    # ### end Alembic commands ###
