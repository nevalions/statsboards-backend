"""add full-text search to person table

Revision ID: 7468b271f771
Revises: 5634d8b97e3e
Create Date: 2026-01-06 12:14:55.580238

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "7468b271f771"
down_revision: Union[str, None] = "5634d8b97e3e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE person
        ADD COLUMN search_vector tsvector;
    """)

    op.execute("""
        CREATE INDEX ix_person_search_vector
        ON person USING GIN (search_vector);
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION person_search_vector_update()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', COALESCE(NEW.first_name, '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(NEW.second_name, '')), 'A');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER person_search_vector_trigger
        BEFORE INSERT OR UPDATE OF first_name, second_name ON person
        FOR EACH ROW
        EXECUTE FUNCTION person_search_vector_update();
    """)

    op.execute("""
        UPDATE person SET search_vector = NULL;
    """)


def downgrade() -> None:
    op.execute("""
        DROP TRIGGER IF EXISTS person_search_vector_trigger ON person;
    """)

    op.execute("""
        DROP FUNCTION IF EXISTS person_search_vector_update();
    """)

    op.execute("""
        DROP INDEX IF EXISTS ix_person_search_vector;
    """)

    op.execute("""
        ALTER TABLE person
        DROP COLUMN IF EXISTS search_vector;
    """)
