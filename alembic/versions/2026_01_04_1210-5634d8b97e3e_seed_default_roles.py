"""seed_default_roles

Revision ID: 5634d8b97e3e
Revises: 752e65b4a9a0
Create Date: 2026-01-04 12:10:28.193289

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5634d8b97e3e"
down_revision: Union[str, None] = "752e65b4a9a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO role (name, description) VALUES
        ('user', 'Basic viewer role'),
        ('admin', 'Administrator with full access'),
        ('editor', 'Can edit content'),
        ('player', 'Player account'),
        ('coach', 'Coach account'),
        ('streamer', 'Streamer account')
        ON CONFLICT (name) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM role WHERE name IN ('user', 'admin', 'editor', 'player', 'coach', 'streamer')"
    )
