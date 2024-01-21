"""team table added sport_id

Revision ID: 505f3d350535
Revises: b99c51e3b2b8
Create Date: 2024-01-20 10:51:26.965349

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "505f3d350535"
down_revision: Union[str, None] = "b99c51e3b2b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("team_sport_id_key", "team", type_="unique")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint("team_sport_id_key", "team", ["sport_id"])
    # ### end Alembic commands ###
