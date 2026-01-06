"""add pg_trgm extension for person search optimization

Revision ID: 32e4ddf548e3
Revises: 7468b271f771
Create Date: 2026-01-06 15:52:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "32e4ddf548e3"
down_revision: Union[str, None] = "7468b271f771"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE EXTENSION IF NOT EXISTS pg_trgm;
    """)

    op.execute("""
        CREATE INDEX ix_person_first_name_trgm
        ON person USING GIN (first_name gin_trgm_ops);
    """)

    op.execute("""
        CREATE INDEX ix_person_second_name_trgm
        ON person USING GIN (second_name gin_trgm_ops);
    """)


def downgrade() -> None:
    op.execute("""
        DROP INDEX IF EXISTS ix_person_first_name_trgm;
    """)

    op.execute("""
        DROP INDEX IF EXISTS ix_person_second_name_trgm;
    """)

    op.execute("""
        DROP EXTENSION IF EXISTS pg_trgm;
    """)
