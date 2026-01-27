"""optimized scoreboard trigger with row data

Revision ID: stab148_optimized_scoreboard_trigger
Revises: stab147_optimized_matchdata_trigger
Create Date: 2026-01-27 10:05:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "stab148_scoreboard"
down_revision: Union[str, None] = "stab147_matchdata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_scoreboard_change() RETURNS trigger AS $$
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM pg_notify('scoreboard_change', 
                json_build_object(
                    'table', TG_TABLE_NAME,
                    'operation', TG_OP,
                    'old_id', OLD.id,
                    'match_id', OLD.match_id
                )::text);
        ELSE
            PERFORM pg_notify('scoreboard_change',
                json_build_object(
                    'table', TG_TABLE_NAME,
                    'operation', TG_OP,
                    'new_id', NEW.id,
                    'old_id', OLD.id,
                    'match_id', NEW.match_id,
                    'data', row_to_json(NEW)
                )::text);
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)


def downgrade():
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_scoreboard_change() RETURNS trigger AS $$
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM pg_notify('scoreboard_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'old_id', OLD.id, 'match_id', OLD.match_id)::text); 
        ELSE
            PERFORM pg_notify('scoreboard_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'new_id', NEW.id, 'old_id', OLD.id, 'match_id', NEW.match_id)::text); 
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)
