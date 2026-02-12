"""stab205_add_sport_preset_capability_flags

Revision ID: 6d3f4b51e8ab
Revises: 3a874ef6c2db
Create Date: 2026-02-12 19:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6d3f4b51e8ab"
down_revision: Union[str, None] = "3a874ef6c2db"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'sport_scoreboard_preset'
                AND column_name = 'has_playclock'
            ) THEN
                ALTER TABLE sport_scoreboard_preset ADD COLUMN has_playclock BOOLEAN DEFAULT true NOT NULL;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'sport_scoreboard_preset'
                AND column_name = 'has_timeouts'
            ) THEN
                ALTER TABLE sport_scoreboard_preset ADD COLUMN has_timeouts BOOLEAN DEFAULT true NOT NULL;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'sport_scoreboard_preset'
                AND column_name = 'has_timeouts'
            ) THEN
                ALTER TABLE sport_scoreboard_preset DROP COLUMN has_timeouts;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'sport_scoreboard_preset'
                AND column_name = 'has_playclock'
            ) THEN
                ALTER TABLE sport_scoreboard_preset DROP COLUMN has_playclock;
            END IF;
        END $$;
    """)
