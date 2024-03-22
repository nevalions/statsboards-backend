"""gameclock trigger update to send match id

Revision ID: d5ff310ae465
Revises: 94a866fec2eb
Create Date: 2024-03-22 15:00:44.822458

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d5ff310ae465"
down_revision: Union[str, None] = "94a866fec2eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_gameclock_change() RETURNS trigger AS $$
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM pg_notify('gameclock_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'old_id', OLD.id, 'match_id', OLD.match_id)::text); 
        ELSE
            PERFORM pg_notify('gameclock_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'new_id', NEW.id, 'old_id', OLD.id, 'match_id', NEW.match_id)::text); 
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
            WHERE tgname = 'gameclock_change'
            AND tgenabled = 'O'  -- This line got changed
        ) THEN
            CREATE TRIGGER gameclock_change
            AFTER INSERT OR UPDATE OR DELETE ON gameclock
            FOR EACH ROW EXECUTE PROCEDURE notify_gameclock_change();
        END IF;
    END;
    $do$
    """)


def downgrade():
    op.execute("""
    DROP TRIGGER IF EXISTS gameclock_change ON gameclock CASCADE;
    """)

    op.execute("""
    DROP FUNCTION IF EXISTS notify_gameclock_change CASCADE;
    """)
