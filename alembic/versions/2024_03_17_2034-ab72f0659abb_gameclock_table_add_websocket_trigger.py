"""gameclock table add websocket trigger

Revision ID: ab72f0659abb
Revises: 777f9cc33163
Create Date: 2024-03-17 20:34:40.018469

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "ab72f0659abb"
down_revision: Union[str, None] = "777f9cc33163"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create notify function and trigger for GameClockDB
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_gameclock_change() RETURNS trigger AS $$
    DECLARE
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM pg_notify('gameclock_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'old_id', OLD.id)::text); 
        ELSE
            PERFORM pg_notify('gameclock_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'new_id', NEW.id, 'old_id', OLD.id)::text); 
        END IF;
        RETURN new;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Create a trigger on the PlayClockDB
    op.execute("""
    CREATE TRIGGER gameclock_change
    AFTER INSERT OR UPDATE OR DELETE ON gameclock
    FOR EACH ROW EXECUTE PROCEDURE notify_gameclock_change();
    """)


def downgrade():
    # Remove trigger (if created)
    op.execute("""
    DROP TRIGGER IF EXISTS gameclock_change ON playclock CASCADE;
    """)

    # Drop notify function
    op.execute("""
    DROP FUNCTION IF EXISTS gameclock_change() CASCADE;
    """)
