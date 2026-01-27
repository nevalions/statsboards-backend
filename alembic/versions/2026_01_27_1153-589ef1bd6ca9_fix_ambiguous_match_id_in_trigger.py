"""fix_ambiguous_match_id_in_trigger

Revision ID: 589ef1bd6ca9
Revises: stab148_scoreboard
Create Date: 2026-01-27 11:53:28.479944

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "589ef1bd6ca9"
down_revision: Union[str, None] = "stab148_scoreboard"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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


def downgrade() -> None:
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
            WHERE match_id = NEW.match_id;
            
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
