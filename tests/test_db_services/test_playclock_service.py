import pytest
from src.playclocks.db_services import PlayClockServiceDB
from src.playclocks.schemas import PlayClockSchemaCreate, PlayClockSchemaUpdate
from src.matches.db_services import MatchServiceDB
from src.matches.schemas import MatchSchemaCreate
from src.teams.db_services import TeamServiceDB
from src.sports.db_services import SportServiceDB
from src.tournaments.db_services import TournamentServiceDB
from src.seasons.db_services import SeasonServiceDB
from tests.factories import (
    MatchFactory,
    TeamFactory,
    TournamentFactory,
    SeasonFactorySample,
    SportFactorySample,
)
from src.logging_config import setup_logging

setup_logging()


@pytest.mark.asyncio
class TestPlayClockServiceDB:
    async def test_create_playclock(self, test_db):
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

        playclock_service = PlayClockServiceDB(test_db)
        playclock_data = PlayClockSchemaCreate(
            match_id=match.id, playclock=40, playclock_status="stopped"
        )

        result = await playclock_service.create(playclock_data)

        assert result is not None
        assert result.id is not None
        assert result.match_id == match.id
        assert result.playclock == 40

    async def test_create_playclock_duplicate(self, test_db):
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

        playclock_service = PlayClockServiceDB(test_db)
        playclock_data = PlayClockSchemaCreate(match_id=match.id, playclock=40)

        result1 = await playclock_service.create(playclock_data)
        result2 = await playclock_service.create(playclock_data)

        assert result1 is not None
        assert result2 is not None

    async def test_update_playclock(self, test_db):
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

        playclock_service = PlayClockServiceDB(test_db)
        playclock_data = PlayClockSchemaCreate(match_id=match.id, playclock=40)

        created = await playclock_service.create(playclock_data)
        update_data = PlayClockSchemaUpdate(playclock=35, playclock_status="running")

        updated = await playclock_service.update(created.id, update_data)

        assert updated.playclock == 35
        assert updated.playclock_status == "running"

    async def test_get_playclock_by_match_id(self, test_db):
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

        playclock_service = PlayClockServiceDB(test_db)
        playclock_data = PlayClockSchemaCreate(match_id=match.id, playclock=40)

        created = await playclock_service.create(playclock_data)
        result = await playclock_service.get_playclock_by_match_id(match.id)

        assert result is not None
        assert result.id == created.id

    async def test_get_playclock_status(self, test_db):
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

        playclock_service = PlayClockServiceDB(test_db)
        playclock_data = PlayClockSchemaCreate(
            match_id=match.id, playclock=40, playclock_status="running"
        )

        created = await playclock_service.create(playclock_data)
        status = await playclock_service.get_playclock_status(created.id)

        assert status == "running"

    async def test_enable_match_data_clock_queues(self, test_db):
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

        playclock_service = PlayClockServiceDB(test_db)
        playclock_data = PlayClockSchemaCreate(match_id=match.id, playclock=40)

        created = await playclock_service.create(playclock_data)
        queue = await playclock_service.enable_match_data_clock_queues(created.id)

        assert queue is not None
        assert created.id in playclock_service.clock_manager.active_playclock_matches

    async def test_decrement_playclock_one_second(self, test_db):
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

        playclock_service = PlayClockServiceDB(test_db)
        playclock_data = PlayClockSchemaCreate(match_id=match.id, playclock=10)

        created = await playclock_service.create(playclock_data)
        result = await playclock_service.decrement_playclock_one_second(created.id)

        assert result == 9
