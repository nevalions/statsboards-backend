"""gameclock trigger include full data

Revision ID: stab130_gameclock_full_data
Revises: stab130_playclock_full_data
Create Date: 2026-01-22 20:31:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "stab130_gameclock_full_data"
down_revision: Union[str, None] = "stab130_playclock_full_data"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_gameclock_change() RETURNS trigger AS $$
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM pg_notify('gameclock_change', json_build_object(
                'table', TG_TABLE_NAME,
                'operation', TG_OP,
                'match_id', OLD.match_id,
                'data', json_build_object(
                    'id', OLD.id,
                    'match_id', OLD.match_id,
                    'version', OLD.version,
                    'gameclock', OLD.gameclock,
                    'gameclock_time_remaining', OLD.gameclock_time_remaining,
                    'gameclock_max', OLD.gameclock_max,
                    'gameclock_status', OLD.gameclock_status
                )
            )::text);
        ELSE
            PERFORM pg_notify('gameclock_change', json_build_object(
                'table', TG_TABLE_NAME,
                'operation', TG_OP,
                'match_id', NEW.match_id,
                'data', json_build_object(
                    'id', NEW.id,
                    'match_id', NEW.match_id,
                    'version', NEW.version,
                    'gameclock', NEW.gameclock,
                    'gameclock_time_remaining', NEW.gameclock_time_remaining,
                    'gameclock_max', NEW.gameclock_max,
                    'gameclock_status', NEW.gameclock_status
                )
            )::text);
        END IF;
        RETURN new;
    END;
    $$ LANGUAGE plpgsql;
    """)


def downgrade():
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
