"""scoreboard add tournament logo sponsors featers to scoreboard

Revision ID: fc865adb8983
Revises: f2270d185c2d
Create Date: 2024-04-19 10:32:31.506717

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "fc865adb8983"
down_revision: Union[str, None] = "f2270d185c2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "scoreboard", sa.Column("is_tournament_logo", sa.Boolean(), nullable=False, server_default='t')
    )
    op.add_column(
        "scoreboard", sa.Column("is_main_sponsor", sa.Boolean(), nullable=False, server_default='t')
    )
    op.add_column(
        "scoreboard", sa.Column("is_sponsor_line", sa.Boolean(), nullable=False, server_default='t')
    )
    op.add_column(
        "scoreboard", sa.Column("scale_tournament_logo", sa.Float(), nullable=False, server_default='2.0')
    )
    op.add_column(
        "scoreboard", sa.Column("scale_main_sponsor", sa.Float(), nullable=False, server_default='2.0')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("scoreboard", "scale_main_sponsor")
    op.drop_column("scoreboard", "scale_tournament_logo")
    op.drop_column("scoreboard", "is_sponsor_line")
    op.drop_column("scoreboard", "is_main_sponsor")
    op.drop_column("scoreboard", "is_tournament_logo")
    # ### end Alembic commands ###
