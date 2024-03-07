"""match-scoreboard-trigger

Revision ID: 5d7a5e992574
Revises: f84f8a9f5b8b
Create Date: 2024-03-07 22:15:20.000802

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "5d7a5e992574"
down_revision: Union[str, None] = "f84f8a9f5b8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create notify function and trigger for ScoreboardDB
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_scoreboard_change() RETURNS trigger AS $$
    DECLARE
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM pg_notify('scoreboard_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'old_id', OLD.id)::text); 
        ELSE
            PERFORM pg_notify('scoreboard_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'new_id', NEW.id, 'old_id', OLD.id)::text); 
        END IF;
        RETURN new;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Create a trigger on the ScoreboardDB
    op.execute("""
    CREATE TRIGGER scoreboard_change
    AFTER INSERT OR UPDATE OR DELETE ON scoreboard
    FOR EACH ROW EXECUTE PROCEDURE notify_scoreboard_change();
    """)


def downgrade():
    # Remove trigger (if created)
    op.execute("""
    DROP TRIGGER IF EXISTS scoreboard_change ON scoreboard CASCADE;
    """)

    # Drop notify function
    op.execute("""
    DROP FUNCTION IF EXISTS notify_scoreboard_change() CASCADE;
    """)
