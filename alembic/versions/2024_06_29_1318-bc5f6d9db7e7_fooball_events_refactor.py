"""fooball events refactor

Revision ID: bc5f6d9db7e7
Revises: 66a2c03c4088
Create Date: 2024-06-29 13:18:11.564096

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bc5f6d9db7e7"
down_revision: Union[str, None] = "66a2c03c4088"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("football_event", sa.Column("event_down", sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("football_event", "event_down")
    # ### end Alembic commands ###
