import pytest

from src.football_events.db_services import FootballEventServiceDB
from src.football_events.schemas import (
    FootballEventSchemaCreate,
    FootballEventSchemaUpdate,
)
from src.matches.db_services import MatchServiceDB
from src.seasons.db_services import SeasonServiceDB
from src.sports.db_services import SportServiceDB
from src.teams.db_services import TeamServiceDB
from src.tournaments.db_services import TournamentServiceDB
from tests.factories import (
    MatchFactory,
    SeasonFactorySample,
    SportFactorySample,
    TeamFactory,
    TournamentFactory,
)



@pytest.mark.asyncio
class TestFootballEventServiceDB:
    async def test_create_football_event(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        event_service = FootballEventServiceDB(test_db)
        event_data = FootballEventSchemaCreate(
            match_id=match.id,
            event_number=1,
            event_qtr=1,
            ball_on=20,
            event_down=1,
            event_distance=10,
            play_type="run",
            play_result="touchdown",
            score_result="6",
        )

        result = await event_service.create(event_data)

        assert result is not None
        assert result.id is not None
        assert result.match_id == match.id

    async def test_update_football_event(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        event_service = FootballEventServiceDB(test_db)
        event_data = FootballEventSchemaCreate(
            match_id=match.id, event_number=1, event_qtr=1, ball_on=20
        )

        created = await event_service.create(event_data)
        update_data = FootballEventSchemaUpdate(ball_on=30, event_qtr=2)

        updated = await event_service.update(created.id, update_data)

        assert updated.ball_on == 30
        assert updated.event_qtr == 2

    async def test_get_match_football_events_by_match_id(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        event_service = FootballEventServiceDB(test_db)
        event1 = await event_service.create(
            FootballEventSchemaCreate(match_id=match.id, event_number=1)
        )
        event2 = await event_service.create(
            FootballEventSchemaCreate(match_id=match.id, event_number=2)
        )

        result = await event_service.get_match_football_events_by_match_id(match.id)

        assert len(result) == 2
        assert event1.id in [e.id for e in result]
        assert event2.id in [e.id for e in result]

    async def test_get_match_football_events_empty(self, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        event_service = FootballEventServiceDB(test_db)
        result = await event_service.get_match_football_events_by_match_id(match.id)

        assert result == []
