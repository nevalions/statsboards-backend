"""player_team_tournament eesl_id

Revision ID: cb048424352e
Revises: 16900df02f8a
Create Date: 2024-04-29 13:02:59.127369

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "cb048424352e"
down_revision: Union[str, None] = "16900df02f8a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "player_team_tournament",
        sa.Column("player_team_tournament_eesl_id", sa.Integer(), nullable=True),
    )
    op.create_unique_constraint(
        None, "player_team_tournament", ["player_team_tournament_eesl_id"]
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "player_team_tournament", type_="unique")
    op.drop_column("player_team_tournament", "player_team_tournament_eesl_id")
    # ### end Alembic commands ###
