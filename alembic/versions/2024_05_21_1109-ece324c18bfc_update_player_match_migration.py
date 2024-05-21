"""update player match migration

Revision ID: ece324c18bfc
Revises: 7e07667d02ae
Create Date: 2024-05-21 11:09:03.892368

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ece324c18bfc"
down_revision: Union[str, None] = "7e07667d02ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("player_match_match_id_key", "player_match", type_="unique")
    op.drop_constraint("player_match_team_id_key", "player_match", type_="unique")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint("player_match_team_id_key", "player_match", ["team_id"])
    op.create_unique_constraint(
        "player_match_match_id_key", "player_match", ["match_id"]
    )
    # ### end Alembic commands ###
