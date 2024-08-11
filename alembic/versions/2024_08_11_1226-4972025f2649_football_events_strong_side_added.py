"""football events strong side added

Revision ID: 4972025f2649
Revises: 43c074388d36
Create Date: 2024-08-11 12:26:14.706446

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4972025f2649"
down_revision: Union[str, None] = "43c074388d36"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "football_event", sa.Column("event_strong_side", sa.String(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("football_event", "event_strong_side")
    # ### end Alembic commands ###
