import pytest
from src.playclocks.db_services import PlayClockServiceDB
from src.playclocks.schemas import PlayClockSchemaCreate
from src.matches.db_services import MatchServiceDB
from src.matches.schemas import MatchSchemaCreate
from src.teams.db_services import TeamServiceDB
from src.sports.db_services import SportServiceDB
from src.tournaments.db_services import TournamentServiceDB
from src.seasons.db_services import SeasonServiceDB
from tests.factories import MatchFactory, TeamFactory, TournamentFactory, SeasonFactorySample, SportFactorySample
from src.logging_config import setup_logging

setup_logging()


@pytest.mark.asyncio
class TestPlayClockResetEndpoint:
    async def test_reset_playclock_to_none(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(TournamentFactory.build(sport_id=sport.id, season_id=season.id))

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(MatchFactory.build(tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id))

        playclock_service = PlayClockServiceDB(test_db)
        playclock = await playclock_service.create(PlayClockSchemaCreate(match_id=match.id, playclock=60, playclock_status="stopped"))

        response = await client.put(f"/api/playclock/id/{playclock.id}/stopped/")

        assert response.status_code == 200
        assert response.json()["content"]["playclock"] is None
        assert response.json()["content"]["playclock_status"] == "stopped"
