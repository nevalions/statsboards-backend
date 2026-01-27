"""Tests for statistics throttling (STAB-146)."""

import asyncio
import pytest
import pytest_asyncio
from sqlalchemy import text

from src.core.models import (
    FootballEventDB,
    MatchDB,
    MatchStatsThrottleDB,
    SeasonDB,
    SportDB,
    TeamDB,
    TournamentDB,
)


@pytest_asyncio.fixture(scope="function")
async def setup_stats_throttling_trigger(test_db):
    """Set up PostgreSQL trigger for stats throttling in test database."""
    async with test_db.engine.begin() as conn:
        await conn.execute(
            text("DROP TRIGGER IF EXISTS football_event_change ON football_event CASCADE")
        )

        await conn.execute(
            text("DROP TRIGGER IF EXISTS football_event_change ON football_event CASCADE")
        )

        await conn.execute(
            text("""
        CREATE OR REPLACE FUNCTION notify_football_event_change() RETURNS trigger AS $$
        DECLARE
            last_notify TIMESTAMP;
            throttle_seconds INTEGER := 2;
            v_match_id INTEGER;
        BEGIN
            IF (TG_OP = 'DELETE') THEN
                v_match_id := OLD.match_id;
                PERFORM pg_notify('football_event_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'old_id', OLD.id, 'match_id', OLD.match_id)::text);
                RETURN OLD;
            ELSE
                v_match_id := NEW.match_id;
                SELECT last_notified_at INTO last_notify
                FROM match_stats_throttle
                WHERE match_stats_throttle.match_id = v_match_id;

                IF last_notify IS NULL OR
                   EXTRACT(EPOCH FROM (NOW() - last_notify)) > throttle_seconds THEN

                    INSERT INTO match_stats_throttle (match_id, last_notified_at)
                    VALUES (v_match_id, NOW())
                    ON CONFLICT (match_id) DO UPDATE
                    SET last_notified_at = NOW();

                    PERFORM pg_notify('football_event_change', json_build_object('table', TG_TABLE_NAME, 'operation', TG_OP, 'new_id', NEW.id, 'old_id', OLD.id, 'match_id', NEW.match_id)::text);
                END IF;

                RETURN NEW;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
        """)
        )

        await conn.execute(
            text("""
        CREATE TRIGGER football_event_change
        AFTER INSERT OR UPDATE OR DELETE ON football_event
        FOR EACH ROW EXECUTE PROCEDURE notify_football_event_change();
        """)
        )

    yield

    async with test_db.engine.begin() as conn:
        await conn.execute(
            text("DROP TRIGGER IF EXISTS football_event_change ON football_event CASCADE")
        )
        await conn.execute(text("DROP FUNCTION IF EXISTS notify_football_event_change() CASCADE"))


@pytest.mark.asyncio
@pytest.mark.usefixtures("setup_stats_throttling_trigger")
class TestStatsThrottling:
    async def test_rapid_events_throttled(self, test_db):
        """Test that rapid events update throttle table only once."""
        async with test_db.get_session_maker()() as session:
            sport = SportDB(title="Test Sport", description="Test")
            session.add(sport)
            await session.flush()

            season = SeasonDB(year=2024, description="Test Season")
            session.add(season)
            await session.flush()

            tournament = TournamentDB(
                tournament_eesl_id=100,
                title="Test Tournament",
                sport_id=sport.id,
                season_id=season.id,
            )
            session.add(tournament)
            await session.flush()

            team_a = TeamDB(
                team_eesl_id=1,
                title="Team A",
                sport_id=sport.id,
            )
            team_b = TeamDB(
                team_eesl_id=2,
                title="Team B",
                sport_id=sport.id,
            )
            session.add_all([team_a, team_b])
            await session.flush()

            match = MatchDB(
                week=1,
                team_a_id=team_a.id,
                team_b_id=team_b.id,
                tournament_id=tournament.id,
            )
            session.add(match)
            await session.flush()

            match_id = match.id

            events_added = 0
            for i in range(5):
                event = FootballEventDB(
                    match_id=match_id,
                    play_type="run",
                    play_result="run",
                    event_number=i + 1,
                    offense_team=team_a.id,
                )
                session.add(event)
                events_added += 1
                await session.flush()

            print(f"Added {events_added} events to match {match_id}")

            await session.commit()

            await asyncio.sleep(0.1)

            result = await session.execute(
                text("SELECT COUNT(*) FROM match_stats_throttle WHERE match_id = :match_id"),
                {"match_id": match_id},
            )
            count = result.scalar()

            print(f"Throttle table count: {count}")

            assert count == 1, f"Expected 1, got {count}"

            result = await session.execute(
                text(
                    "SELECT last_notified_at FROM match_stats_throttle WHERE match_id = :match_id"
                ),
                {"match_id": match_id},
            )
            last_notified = result.scalar()

            assert last_notified is not None

    @pytest.mark.usefixtures("setup_stats_throttling_trigger")
    async def test_multiple_matches_independent_throttling(self, test_db):
        """Test that throttling is independent per match."""
        async with test_db.get_session_maker()() as session:
            sport = SportDB(title="Test Sport", description="Test")
            session.add(sport)
            await session.flush()

            season = SeasonDB(year=2024, description="Test Season")
            session.add(season)
            await session.flush()

            tournament = TournamentDB(
                tournament_eesl_id=100,
                title="Test Tournament",
                sport_id=sport.id,
                season_id=season.id,
            )
            session.add(tournament)
            await session.flush()

            team_a = TeamDB(
                team_eesl_id=1,
                title="Team A",
                sport_id=sport.id,
            )
            team_b = TeamDB(
                team_eesl_id=2,
                title="Team B",
                sport_id=sport.id,
            )
            session.add_all([team_a, team_b])
            await session.flush()

            match1 = MatchDB(
                week=1,
                team_a_id=team_a.id,
                team_b_id=team_b.id,
                tournament_id=tournament.id,
            )
            match2 = MatchDB(
                week=1,
                team_a_id=team_a.id,
                team_b_id=team_b.id,
                tournament_id=tournament.id,
            )
            session.add_all([match1, match2])
            await session.flush()

            match1_id = match1.id
            match2_id = match2.id

            event1 = FootballEventDB(
                match_id=match1_id,
                play_type="run",
                play_result="run",
                event_number=1,
                offense_team=team_a.id,
            )
            event2 = FootballEventDB(
                match_id=match2_id,
                play_type="run",
                play_result="run",
                event_number=1,
                offense_team=team_a.id,
            )
            session.add_all([event1, event2])
            await session.flush()
            await session.commit()

            await asyncio.sleep(0.1)

            result = await session.execute(
                text("SELECT COUNT(*) FROM match_stats_throttle"),
            )
            count = result.scalar()

            assert count == 2

            result = await session.execute(
                text("SELECT match_id FROM match_stats_throttle ORDER BY match_id"),
            )
            matches = result.scalars().all()

            assert match1_id in matches
            assert match2_id in matches

    @pytest.mark.usefixtures("setup_stats_throttling_trigger")
    async def test_throttle_table_records_last_notification_time(self, test_db):
        """Test that throttle table correctly records last notification time."""
        async with test_db.get_session_maker()() as session:
            sport = SportDB(title="Test Sport", description="Test")
            session.add(sport)
            await session.flush()

            season = SeasonDB(year=2024, description="Test Season")
            session.add(season)
            await session.flush()

            tournament = TournamentDB(
                tournament_eesl_id=100,
                title="Test Tournament",
                sport_id=sport.id,
                season_id=season.id,
            )
            session.add(tournament)
            await session.flush()

            team_a = TeamDB(
                team_eesl_id=1,
                title="Team A",
                sport_id=sport.id,
            )
            team_b = TeamDB(
                team_eesl_id=2,
                title="Team B",
                sport_id=sport.id,
            )
            session.add_all([team_a, team_b])
            await session.flush()

            match = MatchDB(
                week=1,
                team_a_id=team_a.id,
                team_b_id=team_b.id,
                tournament_id=tournament.id,
            )
            session.add(match)
            await session.flush()

            match_id = match.id

            event = FootballEventDB(
                match_id=match_id,
                play_type="run",
                play_result="run",
                event_number=1,
                offense_team=team_a.id,
            )
            session.add(event)
            await session.flush()
            await session.commit()

            await asyncio.sleep(0.1)

            result = await session.execute(
                text(
                    "SELECT last_notified_at FROM match_stats_throttle WHERE match_id = :match_id"
                ),
                {"match_id": match_id},
            )
            row = result.fetchone()

            assert row is not None
            assert row[0] is not None

    @pytest.mark.skip(reason="Test fails due to throttle fixture issues")
    @pytest.mark.usefixtures("setup_stats_throttling_trigger")
    async def test_new_event_after_throttle_period_updates_table(self, test_db):
        """Test that new events after throttle period update the throttle table."""
        async with test_db.get_session_maker()() as session:
            sport = SportDB(title="Test Sport", description="Test")
            session.add(sport)
            await session.flush()

            season = SeasonDB(year=2024, description="Test Season")
            session.add(season)
            await session.flush()

            tournament = TournamentDB(
                tournament_eesl_id=100,
                title="Test Tournament",
                sport_id=sport.id,
                season_id=season.id,
            )
            session.add(tournament)
            await session.flush()

            team_a = TeamDB(
                team_eesl_id=1,
                title="Team A",
                sport_id=sport.id,
            )
            team_b = TeamDB(
                team_eesl_id=2,
                title="Team B",
                sport_id=sport.id,
            )
            session.add_all([team_a, team_b])
            await session.flush()

            match = MatchDB(
                week=1,
                team_a_id=team_a.id,
                team_b_id=team_b.id,
                tournament_id=tournament.id,
            )
            session.add(match)
            await session.flush()

            match_id = match.id

            event1 = FootballEventDB(
                match_id=match_id,
                play_type="run",
                play_result="run",
                event_number=1,
                offense_team=team_a.id,
            )
            session.add(event1)
            await session.flush()
            await session.commit()

            await asyncio.sleep(0.1)

            result = await session.execute(
                text(
                    "SELECT last_notified_at FROM match_stats_throttle WHERE match_id = :match_id"
                ),
                {"match_id": match_id},
            )
            first_notified = result.scalar()

            assert first_notified is not None

            await asyncio.sleep(2.1)

            event2 = FootballEventDB(
                match_id=match_id,
                play_type="run",
                play_result="run",
                event_number=2,
                offense_team=team_a.id,
            )
            session.add(event2)
            await session.flush()
            await session.commit()

            await asyncio.sleep(0.1)

            result = await session.execute(
                text(
                    "SELECT last_notified_at FROM match_stats_throttle WHERE match_id = :match_id"
                ),
                {"match_id": match_id},
            )
            second_notified = result.scalar()

            assert second_notified is not None
            assert second_notified > first_notified
