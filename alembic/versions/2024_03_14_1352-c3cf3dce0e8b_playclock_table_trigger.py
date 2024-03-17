"""playclock table trigger

Revision ID: c3cf3dce0e8b
Revises: 3de595f1e2d9
Create Date: 2024-03-14 13:52:26.198389

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c3cf3dce0e8b"
down_revision: Union[str, None] = "3de595f1e2d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create notify function and trigger for PlayClockDB
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_playclock_change() RETURNS trigger AS $$
    DECLARE
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM pg_notify('playclock_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'old_id', OLD.id)::text); 
        ELSE
            PERFORM pg_notify('playclock_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'new_id', NEW.id, 'old_id', OLD.id)::text); 
        END IF;
        RETURN new;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Create a trigger on the PlayClockDB
    op.execute("""
    CREATE TRIGGER playclock_change
    AFTER INSERT OR UPDATE OR DELETE ON playclock
    FOR EACH ROW EXECUTE PROCEDURE notify_playclock_change();
    """)


def downgrade():
    # Remove trigger (if created)
    op.execute("""
    DROP TRIGGER IF EXISTS playclock_change ON playclock CASCADE;
    """)

    # Drop notify function
    op.execute("""
    DROP FUNCTION IF EXISTS playclock_change() CASCADE;
    """)
