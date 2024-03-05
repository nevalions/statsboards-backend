"""match-trigger

Revision ID: 511d319eccb3
Revises: 3f5e971e270e
Create Date: 2024-03-05 14:21:46.263818

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "511d319eccb3"
down_revision: Union[str, None] = "3f5e971e270e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create notify function and trigger for MatchDB
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_match_change() RETURNS trigger AS $$
    DECLARE
    BEGIN
        PERFORM pg_notify('match_change', TG_TABLE_NAME || ', ' || TG_OP || ', ' || NEW.id || ', ' || OLD.id);
        RETURN new;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE TRIGGER match_change_notify
    AFTER INSERT OR UPDATE OR DELETE ON match
    FOR EACH ROW EXECUTE PROCEDURE notify_match_change();
    """)

    # Create notify function and trigger for MatchDataDB
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_matchdata_change() RETURNS trigger AS $$
    DECLARE
    BEGIN
        PERFORM pg_notify('matchdata_change', TG_TABLE_NAME || ', ' || TG_OP || ', ' || NEW.id || ', ' || OLD.id);
        RETURN new;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE TRIGGER matchdata_change_notify
    AFTER INSERT OR UPDATE OR DELETE ON matchdata
    FOR EACH ROW EXECUTE PROCEDURE notify_matchdata_change();
    """)


def downgrade():
    # Optionally, you can also provide a way to undo the changes (Drop the triggers and functions)
    op.execute("DROP TRIGGER match_change_notify ON match;")
    op.execute("DROP FUNCTION notify_match_change;")
    op.execute("DROP TRIGGER matchdata_change_notify ON matchdata;")
    op.execute("DROP FUNCTION notify_matchdata_change;")
