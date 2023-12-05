"""Create one_to_many tournaments table

Revision ID: 912aa2bd784a
Revises: 65018504121d
Create Date: 2023-12-05 20:37:18.227173

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "912aa2bd784a"
down_revision: Union[str, None] = "65018504121d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, "tournament", ["season_id"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "tournament", type_="unique")
    # ### end Alembic commands ###
