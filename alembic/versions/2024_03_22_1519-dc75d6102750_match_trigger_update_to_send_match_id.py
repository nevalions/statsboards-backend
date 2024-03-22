"""match trigger update to send match id

Revision ID: dc75d6102750
Revises: 4ac3e0c1b4f1
Create Date: 2024-03-22 15:19:06.168706

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "dc75d6102750"
down_revision: Union[str, None] = "4ac3e0c1b4f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_match_change() RETURNS trigger AS $$
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM pg_notify('match_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'old_id', OLD.id, 'match_id', OLD.match_id)::text); 
        ELSE
            PERFORM pg_notify('match_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'new_id', NEW.id, 'old_id', OLD.id, 'match_id', NEW.match_id)::text); 
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
