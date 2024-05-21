"""update player match migration

Revision ID: 7e07667d02ae
Revises: a24e8a741d0f
Create Date: 2024-05-21 11:05:46.645806

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7e07667d02ae"
down_revision: Union[str, None] = "a24e8a741d0f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
