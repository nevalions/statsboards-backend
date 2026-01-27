"""optimized matchdata trigger with row data

Revision ID: stab147_optimized_matchdata_trigger
Revises: stab146_stats_throttling
Create Date: 2026-01-27 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "stab147_matchdata"
down_revision: Union[str, None] = "stab146_stats_throttling"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_matchdata_change() RETURNS trigger AS $$
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM pg_notify('matchdata_change', 
                json_build_object(
                    'table', TG_TABLE_NAME,
                    'operation', TG_OP,
                    'old_id', OLD.id,
                    'match_id', OLD.match_id
                )::text);
        ELSE
            PERFORM pg_notify('matchdata_change',
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
