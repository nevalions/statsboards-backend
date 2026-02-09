"""stab197_update_gameclock_notify_for_config_changes

Revision ID: 3a874ef6c2db
Revises: ed575af6cbb8
Create Date: 2026-02-09 14:13:19.864455

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3a874ef6c2db"
down_revision: Union[str, None] = "ed575af6cbb8"
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
                    'direction', OLD.direction,
                    'on_stop_behavior', OLD.on_stop_behavior,
                    'started_at_ms', OLD.started_at_ms
                )
            )::text);
        ELSE
            IF OLD.gameclock_status IS DISTINCT FROM NEW.gameclock_status
               OR OLD.gameclock IS DISTINCT FROM NEW.gameclock
               OR OLD.gameclock_max IS DISTINCT FROM NEW.gameclock_max
               OR OLD.direction IS DISTINCT FROM NEW.direction
               OR OLD.on_stop_behavior IS DISTINCT FROM NEW.on_stop_behavior
               OR OLD.started_at_ms IS DISTINCT FROM NEW.started_at_ms THEN
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
                        'direction', NEW.direction,
                        'on_stop_behavior', NEW.on_stop_behavior,
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
            IF OLD.gameclock_status IS DISTINCT FROM NEW.gameclock_status
               OR OLD.gameclock IS DISTINCT FROM NEW.gameclock THEN
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
