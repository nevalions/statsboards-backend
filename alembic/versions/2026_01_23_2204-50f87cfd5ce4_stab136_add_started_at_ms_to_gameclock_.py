"""stab136_add_started_at_ms_to_gameclock_trigger

Revision ID: 50f87cfd5ce4
Revises: 20063b48a50b
Create Date: 2026-01-23 22:04:59.524872

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "50f87cfd5ce4"
down_revision: Union[str, None] = "20063b48a50b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
                    'gameclock_status', OLD.gameclock_status,
                    'started_at_ms', OLD.started_at_ms
                )
            )::text);
        ELSE
            IF OLD.gameclock_status IS DISTINCT FROM NEW.gameclock_status THEN
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
                        'gameclock_status', NEW.gameclock_status,
                        'started_at_ms', NEW.started_at_ms
                    )
                )::text);
            END IF;
        END IF;
        RETURN new;
    END;
    $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
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
            IF OLD.gameclock_status IS DISTINCT FROM NEW.gameclock_status THEN
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
        END IF;
        RETURN new;
    END;
    $$ LANGUAGE plpgsql;
    """)
