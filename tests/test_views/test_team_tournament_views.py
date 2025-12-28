import pytest
from src.team_tournament.db_services import TeamTournamentServiceDB
from src.team_tournament.schemas import TeamTournamentSchemaCreate, TeamTournamentSchemaUpdate
from src.teams.db_services import TeamServiceDB
from src.sports.db_services import SportServiceDB
from src.tournaments.db_services import TournamentServiceDB
from src.seasons.db_services import SeasonServiceDB
from tests.factories import TeamFactory, TournamentFactory, SeasonFactorySample, SportFactorySample
from src.logging_config import setup_logging

setup_logging()


@pytest.mark.asyncio
class TestTeamTournamentViews:
    async def test_create_team_tournament_relation_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(TournamentFactory.build(sport_id=sport.id, season_id=season.id))
        
        team_service = TeamServiceDB(test_db)
        team = await team_service.create(TeamFactory.build(sport_id=sport.id))
        
        response = await client.post(f"/api/team_in_tournament/{team.id}in{tournament.id}")
        
        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_get_team_tournament_relation_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(TournamentFactory.build(sport_id=sport.id, season_id=season.id))
        
        team_service = TeamServiceDB(test_db)
        team = await team_service.create(TeamFactory.build(sport_id=sport.id))
        
        tt_service = TeamTournamentServiceDB(test_db)
        relation_data = TeamTournamentSchemaCreate(team_id=team.id, tournament_id=tournament.id)
        created = await tt_service.create(relation_data)
        
        response = await client.get(f"/api/team_in_tournament/{team.id}in{tournament.id}")
        
        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_team_tournament_relation_not_found(self, client):
        response = await client.get("/api/team_in_tournament/99999in99999")
        
        assert response.status_code == 404

    async def test_update_team_tournament_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(TournamentFactory.build(sport_id=sport.id, season_id=season.id))
        
        team_service = TeamServiceDB(test_db)
        team = await team_service.create(TeamFactory.build(sport_id=sport.id))
        
        tt_service = TeamTournamentServiceDB(test_db)
        relation_data = TeamTournamentSchemaCreate(team_id=team.id, tournament_id=tournament.id)
        created = await tt_service.create(relation_data)
        
        update_data = TeamTournamentSchemaUpdate(team_id=team.id, tournament_id=tournament.id)
        
        response = await client.put(f"/api/team_in_tournament/", params={"item_id": created.id}, json=update_data.model_dump())
        
        assert response.status_code == 200

    async def test_update_team_tournament_not_found(self, client):
        update_data = TeamTournamentSchemaUpdate(team_id=1, tournament_id=1)
        
        response = await client.put(f"/api/team_in_tournament/", params={"item_id": 99999}, json=update_data.model_dump())
        
        assert response.status_code == 404

    async def test_get_teams_in_tournament_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(TournamentFactory.build(sport_id=sport.id, season_id=season.id))
        
        team_service = TeamServiceDB(test_db)
        team1 = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team2 = await team_service.create(TeamFactory.build(sport_id=sport.id))
        
        tt_service = TeamTournamentServiceDB(test_db)
        await tt_service.create(TeamTournamentSchemaCreate(team_id=team1.id, tournament_id=tournament.id))
        await tt_service.create(TeamTournamentSchemaCreate(team_id=team2.id, tournament_id=tournament.id))
        
        response = await client.get(f"/api/team_in_tournament/tournament/id/{tournament.id}/teams")
        
        assert response.status_code == 200
        assert len(response.json()) >= 2

    async def test_delete_team_tournament_relation_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(TournamentFactory.build(sport_id=sport.id, season_id=season.id))
        
        team_service = TeamServiceDB(test_db)
        team = await team_service.create(TeamFactory.build(sport_id=sport.id))
        
        tt_service = TeamTournamentServiceDB(test_db)
        relation_data = TeamTournamentSchemaCreate(team_id=team.id, tournament_id=tournament.id)
        await tt_service.create(relation_data)
        
        response = await client.delete(f"/api/team_in_tournament/{team.id}in{tournament.id}")
        
        assert response.status_code == 200
