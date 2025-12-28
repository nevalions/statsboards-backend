import pytest
from src.gameclocks.db_services import GameClockServiceDB
from src.gameclocks.schemas import GameClockSchemaCreate, GameClockSchemaUpdate
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
class TestGameClockViews:
    async def test_create_gameclock_endpoint(self, client, test_db):
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
        
        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=600)
        
        response = await client.post("/api/gameclock/", json=gameclock_data.model_dump())
        
        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_update_gameclock_endpoint(self, client, test_db):
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
        
        gameclock_service = GameClockServiceDB(test_db)
        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=600)
        created = await gameclock_service.create(gameclock_data)
        
        update_data = GameClockSchemaUpdate(gameclock=500)
        
        response = await client.put(f"/api/gameclock/{created.id}/", json=update_data.model_dump())
        
        assert response.status_code == 200

    async def test_update_gameclock_not_found(self, client):
        update_data = GameClockSchemaUpdate(gameclock=500)
        
        response = await client.put("/api/gameclock/99999/", json=update_data.model_dump())
        
        assert response.status_code == 404

    async def test_update_gameclock_by_id_endpoint(self, client, test_db):
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
        
        gameclock_service = GameClockServiceDB(test_db)
        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=600)
        created = await gameclock_service.create(gameclock_data)
        
        update_data = GameClockSchemaUpdate(gameclock=500)
        
        response = await client.put(f"/api/gameclock/id/{created.id}/", json=update_data.model_dump())
        
        assert response.status_code == 200
        assert response.json()["success"] == True

    async def test_start_gameclock_endpoint(self, client, test_db):
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
        
        gameclock_service = GameClockServiceDB(test_db)
        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=600, gameclock_status="stopped")
        created = await gameclock_service.create(gameclock_data)
        
        response = await client.put(f"/api/gameclock/id/{created.id}/running/")
        
        assert response.status_code == 200

    async def test_pause_gameclock_endpoint(self, client, test_db):
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
        
        gameclock_service = GameClockServiceDB(test_db)
        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=600, gameclock_status="running")
        created = await gameclock_service.create(gameclock_data)
        
        response = await client.put(f"/api/gameclock/id/{created.id}/paused/")
        
        assert response.status_code == 200

    async def test_reset_gameclock_endpoint(self, client, test_db):
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
        
        gameclock_service = GameClockServiceDB(test_db)
        gameclock_data = GameClockSchemaCreate(match_id=match.id, gameclock=300)
        created = await gameclock_service.create(gameclock_data)
        
        response = await client.put(f"/api/gameclock/id/{created.id}/stopped/720/")
        
        assert response.status_code == 200
