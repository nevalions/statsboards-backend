"""merge heads after stab230

Revision ID: 2734ff08c2a5
Revises: 6d3f4b51e8ab, stab230_goal_metadata
Create Date: 2026-02-13 13:53:24.402440

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "2734ff08c2a5"
down_revision: Union[str, None] = ("6d3f4b51e8ab", "stab230_goal_metadata")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
