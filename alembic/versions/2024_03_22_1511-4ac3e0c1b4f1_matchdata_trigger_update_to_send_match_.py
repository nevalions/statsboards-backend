"""matchdata trigger update to send match id

Revision ID: 4ac3e0c1b4f1
Revises: d5ff310ae465
Create Date: 2024-03-22 15:11:02.351827

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "4ac3e0c1b4f1"
down_revision: Union[str, None] = "d5ff310ae465"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_matchdata_change() RETURNS trigger AS $$
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM pg_notify('matchdata_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'old_id', OLD.id, 'match_id', OLD.match_id)::text); 
        ELSE
            PERFORM pg_notify('matchdata_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'new_id', NEW.id, 'old_id', OLD.id, 'match_id', NEW.match_id)::text); 
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
            WHERE tgname = 'matchdata_change'
            AND tgenabled = 'O'  -- This line got changed
        ) THEN
            CREATE TRIGGER matchdata_change
            AFTER INSERT OR UPDATE OR DELETE ON matchdata
            FOR EACH ROW EXECUTE PROCEDURE notify_matchdata_change();
        END IF;
    END;
    $do$
    """)


def downgrade():
    op.execute("""
    DROP TRIGGER IF EXISTS matchdata_change ON matchdata CASCADE;
    """)

    op.execute("""
    DROP FUNCTION IF EXISTS notify_matchdata_change CASCADE;
    """)
