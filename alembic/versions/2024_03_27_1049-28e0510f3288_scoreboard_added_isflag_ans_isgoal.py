"""scoreboard added isflag ans isgoal

Revision ID: 28e0510f3288
Revises: 7c6505309e25
Create Date: 2024-03-27 10:49:02.074875

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "28e0510f3288"
down_revision: Union[str, None] = "7c6505309e25"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("scoreboard", sa.Column("is_flag", sa.Boolean(), nullable=True))
    op.add_column("scoreboard", sa.Column("is_goal_team_a", sa.Boolean(), nullable=True))
    op.add_column("scoreboard", sa.Column("is_goal_team_b", sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("scoreboard", "is_goal_team_b")
    op.drop_column("scoreboard", "is_goal_team_a")
    op.drop_column("scoreboard", "is_flag")
    # ### end Alembic commands ###
