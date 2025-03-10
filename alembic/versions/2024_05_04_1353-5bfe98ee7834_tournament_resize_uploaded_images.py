"""tournament resize uploaded images

Revision ID: 5bfe98ee7834
Revises: d0338dce74c0
Create Date: 2024-05-04 13:53:28.699254

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5bfe98ee7834"
down_revision: Union[str, None] = "d0338dce74c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "tournament",
        sa.Column(
            "tournament_logo_icon_url",
            sa.String(length=500),
            server_default="",
            nullable=True,
        ),
    )
    op.add_column(
        "tournament",
        sa.Column(
            "tournament_logo_web_url",
            sa.String(length=500),
            server_default="",
            nullable=True,
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("tournament", "tournament_logo_web_url")
    op.drop_column("tournament", "tournament_logo_icon_url")
    # ### end Alembic commands ###
