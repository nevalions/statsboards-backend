"""player_match model refactored

Revision ID: a24e8a741d0f
Revises: 6bfab158561e
Create Date: 2024-05-17 15:03:32.201612

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a24e8a741d0f"
down_revision: Union[str, None] = "6bfab158561e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "player_match", "match_position_id", existing_type=sa.INTEGER(), nullable=True
    )
    op.drop_constraint(
        "player_match_match_position_id_key", "player_match", type_="unique"
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(
        "player_match_match_position_id_key", "player_match", ["match_position_id"]
    )
    op.alter_column(
        "player_match", "match_position_id", existing_type=sa.INTEGER(), nullable=False
    )
    # ### end Alembic commands ###
