"""person eesl_id

Revision ID: 09da569e356c
Revises: 2ad83031f5de
Create Date: 2024-04-29 12:14:45.436869

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "09da569e356c"
down_revision: Union[str, None] = "2ad83031f5de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("person", sa.Column("person_eesl_id", sa.Integer(), nullable=True))
    op.create_unique_constraint(None, "person", ["person_eesl_id"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "person", type_="unique")
    op.drop_column("person", "person_eesl_id")
    # ### end Alembic commands ###
