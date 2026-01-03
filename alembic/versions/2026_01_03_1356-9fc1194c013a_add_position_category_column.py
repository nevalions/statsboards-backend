"""add_position_category_column

Revision ID: 9fc1194c013a
Revises: a3b4c5d6e7f8
Create Date: 2026-01-03 13:56:30.143648

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9fc1194c013a"
down_revision: Union[str, None] = "a3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("position", sa.Column("category", sa.String(50), nullable=True))

    op.execute("""
        UPDATE position
        SET category = CASE
            WHEN title IN ('Quarterback', 'Running Back', 'Wide Receiver', 'Tight End', 'Offensive Line', 'Center', 'Guard', 'Tackle')
                THEN 'offense'
            WHEN title IN ('Defensive Line', 'Linebacker', 'Defensive Back', 'Cornerback', 'Safety')
                THEN 'defense'
            WHEN title IN ('Kicker', 'Punter', 'Return Specialist')
                THEN 'special'
            ELSE 'other'
        END
    """)


def downgrade() -> None:
    op.drop_column("position", "category")
