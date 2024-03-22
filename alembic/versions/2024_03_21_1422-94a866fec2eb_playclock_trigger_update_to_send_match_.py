"""playclock trigger update to send match id

Revision ID: 94a866fec2eb
Revises: 4b3cce5a35bc
Create Date: 2024-03-21 14:22:28.679483

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "94a866fec2eb"
down_revision: Union[str, None] = "4b3cce5a35bc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_playclock_change() RETURNS trigger AS $$
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM pg_notify('playclock_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'old_id', OLD.id, 'match_id', OLD.match_id)::text); 
        ELSE
            PERFORM pg_notify('playclock_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'new_id', NEW.id, 'old_id', OLD.id, 'match_id', NEW.match_id)::text); 
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
            WHERE tgname = 'playclock_change'
            AND tgenabled = 'O'  -- This line got changed
        ) THEN
            CREATE TRIGGER playclock_change
            AFTER INSERT OR UPDATE OR DELETE ON playclock
            FOR EACH ROW EXECUTE PROCEDURE notify_playclock_change();
        END IF;
    END;
    $do$
    """)


def downgrade():
    op.execute("""
    DROP TRIGGER IF EXISTS playclock_change ON playclock CASCADE;
    """)

    op.execute("""
    DROP FUNCTION IF EXISTS notify_playclock_change CASCADE;
    """)
