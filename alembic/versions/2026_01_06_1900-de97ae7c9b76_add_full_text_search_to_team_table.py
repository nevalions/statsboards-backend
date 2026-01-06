"""add full-text search to team table

Revision ID: de97ae7c9b76
Revises: 32e4ddf548e3
Create Date: 2026-01-06 19:00:04.808494

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "de97ae7c9b76"
down_revision: Union[str, None] = "32e4ddf548e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Part A: tsvector column + GIN index + trigger
    op.execute("""
        ALTER TABLE team
        ADD COLUMN search_vector tsvector;
    """)

    op.execute("""
        CREATE INDEX ix_team_search_vector
        ON team USING GIN (search_vector);
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION team_search_vector_update()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector :=
                to_tsvector('english', COALESCE(NEW.title, ''));
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER team_search_vector_trigger
        BEFORE INSERT OR UPDATE OF title ON team
        For EACH ROW
        EXECUTE FUNCTION team_search_vector_update();
    """)

    op.execute("""
        UPDATE team SET search_vector = NULL;
    """)

    # Part B: pg_trgm extension + trigram index on title
    op.execute("""
        CREATE EXTENSION IF NOT EXISTS pg_trgm;
    """)

    op.execute("""
        CREATE INDEX ix_team_title_trgm
        ON team USING GIN (title gin_trgm_ops);
    """)


def downgrade() -> None:
    # Part B: Remove trigram index and extension
    op.execute("""
        DROP INDEX IF EXISTS ix_team_title_trgm;
    """)

    op.execute("""
        DROP EXTENSION IF EXISTS pg_trgm;
    """)

    # Part A: Remove trigger, function, index, column
    op.execute("""
        DROP TRIGGER IF EXISTS team_search_vector_trigger ON team;
    """)

    op.execute("""
        DROP FUNCTION IF EXISTS team_search_vector_update();
    """)

    op.execute("""
        DROP INDEX IF EXISTS ix_team_search_vector;
    """)

    op.execute("""
        ALTER TABLE team
        DROP COLUMN IF EXISTS search_vector;
    """)
