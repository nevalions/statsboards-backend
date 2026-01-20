"""football_event trigger for websocket updates

Revision ID: stab100_event_trigger
Revises: c35330967b94
Create Date: 2026-01-20 14:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "stab100_event_trigger"
down_revision: Union[str, None] = "c35330967b94"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_football_event_change() RETURNS trigger AS $$
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM pg_notify('football_event_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'old_id', OLD.id, 'match_id', OLD.match_id)::text);
        ELSE
            PERFORM pg_notify('football_event_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'new_id', NEW.id, 'old_id', OLD.id, 'match_id', NEW.match_id)::text);
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
            WHERE tgname = 'football_event_change'
            AND tgenabled = 'O'
        ) THEN
            CREATE TRIGGER football_event_change
            AFTER INSERT OR UPDATE OR DELETE ON football_event
            FOR EACH ROW EXECUTE PROCEDURE notify_football_event_change();
        END IF;
    END;
    $do$
    """)


def downgrade():
    op.execute("""
    DROP TRIGGER IF EXISTS football_event_change ON football_event CASCADE;
    """)

    op.execute("""
    DROP FUNCTION IF EXISTS notify_football_event_change CASCADE;
    """)
