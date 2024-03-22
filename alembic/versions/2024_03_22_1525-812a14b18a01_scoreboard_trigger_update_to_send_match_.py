"""scoreboard trigger update to send match id

Revision ID: 812a14b18a01
Revises: 09fb9d017853
Create Date: 2024-03-22 15:25:04.389340

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "812a14b18a01"
down_revision: Union[str, None] = "09fb9d017853"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_scoreboard_change() RETURNS trigger AS $$
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM pg_notify('scoreboard_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'old_id', OLD.id, 'match_id', OLD.match_id)::text); 
        ELSE
            PERFORM pg_notify('scoreboard_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'new_id', NEW.id, 'old_id', OLD.id, 'match_id', NEW.match_id)::text); 
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
            WHERE tgname = 'scoreboard_change'
            AND tgenabled = 'O'  -- This line got changed
        ) THEN
            CREATE TRIGGER scoreboard_change
            AFTER INSERT OR UPDATE OR DELETE ON scoreboard
            FOR EACH ROW EXECUTE PROCEDURE notify_scoreboard_change();
        END IF;
    END;
    $do$
    """)


def downgrade():
    op.execute("""
    DROP TRIGGER IF EXISTS scoreboard_change ON scoreboard CASCADE;
    """)

    op.execute("""
    DROP FUNCTION IF EXISTS notify_scoreboard_change CASCADE;
    """)
