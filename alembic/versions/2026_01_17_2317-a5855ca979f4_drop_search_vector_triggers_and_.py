"""drop_search_vector_triggers_and_functions

Revision ID: a5855ca979f4
Revises: 5fc3e8f9a8f1
Create Date: 2026-01-17 23:17:50.799657

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a5855ca979f4"
down_revision: Union[str, None] = "5fc3e8f9a8f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS player_team_tournament_search_vector_trigger ON player_team_tournament CASCADE"
    )
    op.execute("DROP FUNCTION IF EXISTS player_team_tournament_search_vector_update() CASCADE")
    op.execute("DROP TRIGGER IF EXISTS person_search_vector_trigger ON person CASCADE")
    op.execute("DROP FUNCTION IF EXISTS person_search_vector_update() CASCADE")
    op.execute("DROP TRIGGER IF EXISTS team_search_vector_trigger ON team CASCADE")
    op.execute("DROP FUNCTION IF EXISTS team_search_vector_update() CASCADE")


def downgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION player_team_tournament_search_vector_update()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $function$
        BEGIN
            NEW.search_vector :=
                to_tsvector('simple', COALESCE(NEW.player_number, '')) ||
                to_tsvector('simple', COALESCE((
                    SELECT COALESCE(first_name, '') || ' ' || COALESCE(second_name, '')
                    FROM player
                    WHERE player.id = player_team_tournament.player_id
                ), ''));
            RETURN NEW;
        END;
        $function$
    """)
    op.execute(
        "CREATE TRIGGER player_team_tournament_search_vector_trigger BEFORE INSERT OR UPDATE OF player_number, player_id ON player_team_tournament FOR EACH ROW EXECUTE FUNCTION player_team_tournament_search_vector_update()"
    )

    op.execute("""
        CREATE OR REPLACE FUNCTION person_search_vector_update()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $function$
        BEGIN
            NEW.search_vector :=
                to_tsvector('simple', COALESCE(NEW.first_name, '')) ||
                to_tsvector('simple', COALESCE(NEW.second_name, ''));
            RETURN NEW;
        END;
        $function$
    """)
    op.execute(
        "CREATE TRIGGER person_search_vector_trigger BEFORE INSERT OR UPDATE OF first_name, second_name ON person FOR EACH ROW EXECUTE FUNCTION person_search_vector_update()"
    )

    op.execute("""
        CREATE OR REPLACE FUNCTION team_search_vector_update()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $function$
        BEGIN
            NEW.search_vector :=
                to_tsvector('simple', COALESCE(NEW.title, ''));
            RETURN NEW;
        END;
        $function$
    """)
    op.execute(
        "CREATE TRIGGER team_search_vector_trigger BEFORE INSERT OR UPDATE OF title ON team FOR EACH ROW EXECUTE FUNCTION team_search_vector_update()"
    )
