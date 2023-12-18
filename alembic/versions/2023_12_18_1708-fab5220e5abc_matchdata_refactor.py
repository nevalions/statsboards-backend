"""matchdata refactor

Revision ID: fab5220e5abc
Revises: 7d8ef0402236
Create Date: 2023-12-18 17:08:20.922928

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fab5220e5abc"
down_revision: Union[str, None] = "7d8ef0402236"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
