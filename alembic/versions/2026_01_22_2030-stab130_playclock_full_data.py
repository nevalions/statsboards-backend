"""playclock trigger include full data

Revision ID: stab130_playclock_full_data
Revises: stab127_clock_versions
Create Date: 2026-01-22 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "stab130_playclock_full_data"
down_revision: Union[str, None] = "stab127_clock_versions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_playclock_change() RETURNS trigger AS $$
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM pg_notify('playclock_change', json_build_object(
                'table', TG_TABLE_NAME,
                'operation', TG_OP,
                'match_id', OLD.match_id,
                'data', json_build_object(
                    'id', OLD.id,
                    'match_id', OLD.match_id,
                    'version', OLD.version,
                    'playclock', OLD.playclock,
                    'playclock_status', OLD.playclock_status
                )
            )::text);
        ELSE
            PERFORM pg_notify('playclock_change', json_build_object(
                'table', TG_TABLE_NAME,
                'operation', TG_OP,
                'match_id', NEW.match_id,
                'data', json_build_object(
                    'id', NEW.id,
                    'match_id', NEW.match_id,
                    'version', NEW.version,
                    'playclock', NEW.playclock,
                    'playclock_status', NEW.playclock_status
                )
            )::text);
        END IF;
        RETURN new;
    END;
    $$ LANGUAGE plpgsql;
    """)


def downgrade():
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
