"""match trigger update to send match id

Revision ID: fd1c579bc678
Revises: 812a14b18a01
Create Date: 2024-03-22 15:27:00.257943

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "fd1c579bc678"
down_revision: Union[str, None] = "812a14b18a01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_match_change() RETURNS trigger AS $$
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM pg_notify('match_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'old_id', OLD.id, 'match_id', OLD.id)::text); 
        ELSE
            PERFORM pg_notify('match_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'new_id', NEW.id, 'old_id', OLD.id, 'match_id', NEW.id)::text); 
        END IF;
        RETURN new;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    DO
    $do$
    BEGIN
        IF NOT EXISTS (
            SELECT FROM pg_trigger
            WHERE tgname = 'match_change'
            AND tgenabled = 'O'  -- This line got changed
        ) THEN
            CREATE TRIGGER match_change
            AFTER INSERT OR UPDATE OR DELETE ON match
            FOR EACH ROW EXECUTE PROCEDURE notify_match_change();
        END IF;
    END;
    $do$
    """)


def downgrade():
    op.execute("""
    DROP TRIGGER IF EXISTS match_change ON match CASCADE;
    """)

    op.execute("""
    DROP FUNCTION IF EXISTS notify_match_change CASCADE;
    """)
