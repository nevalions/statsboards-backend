"""scoreboard is match player lower player id

Revision ID: cededdf0a692
Revises: 66513fc806b4
Create Date: 2024-05-30 20:23:52.787057

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "cededdf0a692"
down_revision: Union[str, None] = "66513fc806b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "scoreboard", sa.Column("player_match_lower_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        None,
        "scoreboard",
        "player_match",
        ["player_match_lower_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "scoreboard", type_="foreignkey")
    op.drop_column("scoreboard", "player_match_lower_id")
    # ### end Alembic commands ###
