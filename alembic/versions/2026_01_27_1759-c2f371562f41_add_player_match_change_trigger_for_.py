"""add player_match_change trigger for WebSocket notifications

Revision ID: c2f371562f41
Revises: 589ef1bd6ca9
Create Date: 2026-01-27 17:59:49.560628

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c2f371562f41"
down_revision: Union[str, None] = "589ef1bd6ca9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_player_match_change() RETURNS trigger AS $$
    DECLARE
        match_id INTEGER;
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            match_id := OLD.match_id;
            PERFORM pg_notify('player_match_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'old_id', OLD.id, 'match_id', OLD.match_id)::text);
            RETURN OLD;
        ELSE
            match_id := NEW.match_id;
            PERFORM pg_notify('player_match_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'new_id', NEW.id, 'old_id', OLD.id, 'match_id', NEW.match_id)::text);
            RETURN NEW;
        END IF;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE TRIGGER player_match_change_notify
    AFTER INSERT OR UPDATE OR DELETE ON player_match
    FOR EACH ROW EXECUTE FUNCTION notify_player_match_change();
    """)


def downgrade() -> None:
    op.execute("""
    DROP TRIGGER IF EXISTS player_match_change_notify ON player_match CASCADE;
    """)

    op.execute("""
    DROP FUNCTION IF EXISTS notify_player_match_change() CASCADE;
    """)
