"""scoreboard added scale logo

Revision ID: 7c6505309e25
Revises: b28de6cd1bc2
Create Date: 2024-03-26 12:58:21.686584

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7c6505309e25"
down_revision: Union[str, None] = "b28de6cd1bc2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "scoreboard",
        "scale_logo_a",
        existing_type=sa.INTEGER(),
        type_=sa.Float(),
        existing_nullable=True,
    )
    op.alter_column(
        "scoreboard",
        "scale_logo_b",
        existing_type=sa.INTEGER(),
        type_=sa.Float(),
        existing_nullable=True,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "scoreboard",
        "scale_logo_b",
        existing_type=sa.Float(),
        type_=sa.INTEGER(),
        existing_nullable=True,
    )
    op.alter_column(
        "scoreboard",
        "scale_logo_a",
        existing_type=sa.Float(),
        type_=sa.INTEGER(),
        existing_nullable=True,
    )
    # ### end Alembic commands ###
