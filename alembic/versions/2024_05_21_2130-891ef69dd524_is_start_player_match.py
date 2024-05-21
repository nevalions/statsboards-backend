"""is start player match

Revision ID: 891ef69dd524
Revises: ece324c18bfc
Create Date: 2024-05-21 21:30:04.469846

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "891ef69dd524"
down_revision: Union[str, None] = "ece324c18bfc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("player_match", sa.Column("is_start", sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("player_match", "is_start")
    # ### end Alembic commands ###
