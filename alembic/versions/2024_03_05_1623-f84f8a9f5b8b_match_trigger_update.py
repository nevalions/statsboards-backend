"""match-trigger-update

Revision ID: f84f8a9f5b8b
Revises: 511d319eccb3
Create Date: 2024-03-05 16:23:42.148157

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f84f8a9f5b8b"
down_revision: Union[str, None] = "511d319eccb3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create notify function and trigger for MatchDB
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_match_change() RETURNS trigger AS $$
    DECLARE
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM pg_notify('match_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'old_id', OLD.id)::text); 
        ELSE
            PERFORM pg_notify('match_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'new_id', NEW.id, 'old_id', OLD.id)::text); 
        END IF;
        RETURN new;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Similarly create a trigger on the MatchDb
    op.execute("""
    CREATE TRIGGER match_change
    AFTER INSERT OR UPDATE OR DELETE ON match
    FOR EACH ROW EXECUTE PROCEDURE notify_match_change();
    """)

    # Create notify function and trigger for MatchData
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_matchdata_change() RETURNS trigger AS $$
    DECLARE
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM pg_notify('matchdata_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'old_id', OLD.id)::text); 
        ELSE
            PERFORM pg_notify('matchdata_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'new_id', NEW.id, 'old_id', OLD.id)::text); 
        END IF;
        RETURN new;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Create a trigger on the MatchData
    op.execute("""
    CREATE TRIGGER matchdata_change
    AFTER INSERT OR UPDATE OR DELETE ON matchdata
    FOR EACH ROW EXECUTE PROCEDURE notify_matchdata_change();
    """)


def downgrade():
    # Remove triggers (if created)
    op.execute("""
    DROP TRIGGER IF EXISTS match_change ON MatchDB CASCADE;
    """)
    # Similarly for matchdata
    op.execute("""
    DROP TRIGGER IF EXISTS matchdata_change ON MatchDataDB CASCADE;
    """)

    # Drop notify functions
    op.execute("""
    DROP FUNCTION IF EXISTS notify_match_change() CASCADE;
    """)
    # Similarly for `notify_matchdata_change()`
    op.execute("""
    DROP FUNCTION IF EXISTS notify_matchdata_change() CASCADE;
    """)
