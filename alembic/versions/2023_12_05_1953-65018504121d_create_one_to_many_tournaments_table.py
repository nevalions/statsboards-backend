"""Create one_to_many tournaments table

Revision ID: 65018504121d
Revises: 72173ccb0597
Create Date: 2023-12-05 19:53:44.269623

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "65018504121d"
down_revision: Union[str, None] = "72173ccb0597"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("tournament_season_id_fkey", "tournament", type_="foreignkey")
    op.create_foreign_key(
        None, "tournament", "season", ["season_id"], ["id"], ondelete="CASCADE"
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "tournament", type_="foreignkey")
    op.create_foreign_key(
        "tournament_season_id_fkey", "tournament", "season", ["season_id"], ["id"]
    )
    # ### end Alembic commands ###
