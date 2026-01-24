"""fix clock triggers to notify on status and value changes

Revision ID: stab133_clock_status_value
Revises: d23a0578d56e
Create Date: 2026-01-24 16:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "stab133_clock_status_value"
down_revision: Union[str, None] = "d23a0578d56e"
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
            IF OLD.playclock_status IS DISTINCT FROM NEW.playclock_status
               OR OLD.playclock IS DISTINCT FROM NEW.playclock THEN
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
        END IF;
        RETURN new;
    END;
    $$ LANGUAGE plpgsql;
    """)

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


def downgrade():
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
            IF OLD.playclock_status IS DISTINCT FROM NEW.playclock_status THEN
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
        END IF;
        RETURN new;
    END;
    $$ LANGUAGE plpgsql;
    """)

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
