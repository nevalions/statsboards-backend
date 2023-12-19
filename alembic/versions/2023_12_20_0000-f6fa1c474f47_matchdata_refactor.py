"""matchdata refactor

Revision ID: f6fa1c474f47
Revises: fab5220e5abc
Create Date: 2023-12-20 00:00:16.627628

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f6fa1c474f47"
down_revision: Union[str, None] = "fab5220e5abc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
