import pytest

from src.logging_config import setup_logging
from src.matches.db_services import MatchServiceDB
from src.matches.schemas import MatchSchemaCreate, MatchSchemaUpdate
from src.seasons.db_services import SeasonServiceDB
from src.sports.db_services import SportServiceDB
from src.teams.db_services import TeamServiceDB
from src.tournaments.db_services import TournamentServiceDB
from tests.factories import (
    SeasonFactorySample,
    SportFactorySample,
    TeamFactory,
    TournamentFactory,
)

setup_logging()


@pytest.mark.asyncio
class TestMatchViews:
    async def test_create_match_endpoint(self, client, test_db):
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

        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date="2025-01-01",
            week=1,
        )

        response = await client.post(
            "/api/matches/", json=match_data.model_dump(mode="json")
        )

        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_update_match_endpoint(self, client, test_db):
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
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date="2025-01-01",
            week=1,
        )
        created = await match_service.create_or_update_match(match_data)

        update_data = MatchSchemaUpdate(week=2)

        response = await client.put(
            f"/api/matches/{created.id}/", json=update_data.model_dump()
        )

        assert response.status_code == 200

    async def test_update_match_not_found(self, client):
        update_data = MatchSchemaUpdate(week=2)

        response = await client.put(
            "/api/matches/99999/", json=update_data.model_dump()
        )

        assert response.status_code == 404

    async def test_get_all_matches_endpoint(self, client, test_db):
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
        await match_service.create_or_update_match(
            MatchSchemaCreate(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )
        await match_service.create_or_update_match(
            MatchSchemaCreate(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        response = await client.get("/api/matches/")

        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_get_match_by_id_endpoint(self, client, test_db):
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
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
        )
        created = await match_service.create_or_update_match(match_data)

        response = await client.get(f"/api/matches/id/{created.id}")

        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_match_by_id_not_found(self, client):
        response = await client.get("/api/matches/id/99999")

        assert response.status_code == 404
