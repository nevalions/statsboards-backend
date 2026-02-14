"""add statistics throttling

Revision ID: stab146_stats_throttling
Revises: stab132_clock_status_only_notify
Create Date: 2026-01-26 21:02:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "stab146_stats_throttling"
down_revision: Union[str, None] = "stab133_clock_status_value"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS match_stats_throttle (
            match_id INTEGER PRIMARY KEY NOT NULL,
            last_notified_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
        );
        """
    )

    op.execute("DROP TRIGGER IF EXISTS football_event_change ON football_event CASCADE")

    op.execute("""
    CREATE OR REPLACE FUNCTION notify_football_event_change() RETURNS trigger AS $$
    DECLARE
        last_notify TIMESTAMP;
        throttle_seconds INTEGER := 2;
        match_id INTEGER;
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            match_id := OLD.match_id;
            PERFORM pg_notify('football_event_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'old_id', OLD.id, 'match_id', OLD.match_id)::text);
            RETURN OLD;
        ELSE
            match_id := NEW.match_id;
            SELECT last_notified_at INTO last_notify 
            FROM match_stats_throttle 
            WHERE match_stats_throttle.match_id = NEW.match_id;
            
            IF last_notify IS NULL OR 
               EXTRACT(EPOCH FROM (NOW() - last_notify)) > throttle_seconds THEN
                
                INSERT INTO match_stats_throttle (match_id, last_notified_at)
                VALUES (NEW.match_id, NOW())
                ON CONFLICT (match_id) DO UPDATE 
                SET last_notified_at = NOW();
                
                PERFORM pg_notify('football_event_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'new_id', NEW.id, 'old_id', OLD.id, 'match_id', NEW.match_id)::text);
            END IF;
            
            RETURN NEW;
        END IF;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    DO
    $do$
    BEGIN
        IF NOT EXISTS (
            SELECT FROM pg_trigger
            WHERE tgname = 'football_event_change'
        ) THEN
            CREATE TRIGGER football_event_change
            AFTER INSERT OR UPDATE OR DELETE ON football_event
            FOR EACH ROW EXECUTE PROCEDURE notify_football_event_change();
        END IF;
    END;
    $do$
    """)

    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_match_stats_throttle_notified_at 
    ON match_stats_throttle(last_notified_at);
    """)

    op.execute("""
    CREATE OR REPLACE FUNCTION notify_football_event_change() RETURNS trigger AS $$
    DECLARE
        last_notify TIMESTAMP;
        throttle_seconds INTEGER := 2;
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM pg_notify('football_event_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'old_id', OLD.id, 'match_id', OLD.match_id)::text);
            RETURN OLD;
        ELSE
            SELECT last_notified_at INTO last_notify 
            FROM match_stats_throttle 
            WHERE match_stats_throttle.match_id = NEW.match_id;
            
            IF last_notify IS NULL OR 
               EXTRACT(EPOCH FROM (NOW() - last_notify)) > throttle_seconds THEN
                
                INSERT INTO match_stats_throttle (match_id, last_notified_at)
                VALUES (NEW.match_id, NOW())
                ON CONFLICT (match_id) DO UPDATE 
                SET last_notified_at = NOW();
                
                PERFORM pg_notify('football_event_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'new_id', NEW.id, 'old_id', OLD.id, 'match_id', NEW.match_id)::text);
            END IF;
            
            RETURN NEW;
        END IF;
    END;
    $$ LANGUAGE plpgsql;
    """)


def downgrade():
    op.execute("""
    DROP TABLE IF EXISTS match_stats_throttle CASCADE;
    """)

    op.execute("""
    CREATE OR REPLACE FUNCTION notify_football_event_change() RETURNS trigger AS $$
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            PERFORM pg_notify('football_event_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'old_id', OLD.id, 'match_id', OLD.match_id)::text);
        ELSE
            PERFORM pg_notify('football_event_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'new_id', NEW.id, 'old_id', OLD.id, 'match_id', NEW.match_id)::text);
        END IF;
        RETURN new;
    END;
    $$ LANGUAGE plpgsql;
    """)
