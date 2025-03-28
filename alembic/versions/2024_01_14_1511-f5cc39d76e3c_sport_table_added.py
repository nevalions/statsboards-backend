"""sport table added

Revision ID: f5cc39d76e3c
Revises: ff91e63a5c14
Create Date: 2024-01-14 15:11:14.128790

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f5cc39d76e3c"
down_revision: Union[str, None] = "ff91e63a5c14"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "sport",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("tournament", sa.Column("sport_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        None, "tournament", "sport", ["sport_id"], ["id"], ondelete="CASCADE"
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "tournament", type_="foreignkey")
    op.drop_column("tournament", "sport_id")
    op.drop_table("sport")
    # ### end Alembic commands ###
