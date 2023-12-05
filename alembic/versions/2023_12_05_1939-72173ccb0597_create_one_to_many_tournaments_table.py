"""Create one_to_many tournaments table

Revision ID: 72173ccb0597
Revises: 1c58f1c54b5e
Create Date: 2023-12-05 19:39:24.145605

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "72173ccb0597"
down_revision: Union[str, None] = "1c58f1c54b5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("tournament", sa.Column("season_id", sa.Integer(), nullable=False))
    op.create_foreign_key(None, "tournament", "season", ["season_id"], ["id"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "tournament", type_="foreignkey")
    op.drop_column("tournament", "season_id")
    # ### end Alembic commands ###
