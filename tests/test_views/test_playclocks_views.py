import pytest

from src.logging_config import setup_logging
from src.matches.db_services import MatchServiceDB
from src.playclocks.db_services import PlayClockServiceDB
from src.playclocks.schemas import PlayClockSchemaCreate, PlayClockSchemaUpdate
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

setup_logging()


@pytest.mark.asyncio
class TestPlayClockViews:
    async def test_create_playclock_endpoint(self, client, test_db):
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

        playclock_data = PlayClockSchemaCreate(
            match_id=match.id, playclock=60, playclock_status="stopped"
        )

        response = await client.post(
            "/api/playclock/", json=playclock_data.model_dump()
        )

        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_update_playclock_endpoint(self, client, test_db):
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
            match_id=match.id, playclock=60, playclock_status="stopped"
        )
        created = await playclock_service.create(playclock_data)

        update_data = PlayClockSchemaUpdate(playclock=120)

        response = await client.put(
            f"/api/playclock/{created.id}/", json=update_data.model_dump()
        )

        assert response.status_code == 200

    async def test_update_playclock_not_found(self, client):
        update_data = PlayClockSchemaUpdate(playclock=120)

        response = await client.put(
            "/api/playclock/99999/", json=update_data.model_dump()
        )

        assert response.status_code == 404

    async def test_get_playclock_by_id_endpoint(self, client, test_db):
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
            match_id=match.id, playclock=60, playclock_status="stopped"
        )
        created = await playclock_service.create(playclock_data)

        response = await client.get(f"/api/playclock/id/{created.id}/")

        assert response.status_code == 200
        assert response.json()["content"]["id"] == created.id

    async def test_get_playclock_by_id_not_found(self, client):
        response = await client.get("/api/playclock/id/99999/")

        assert response.status_code == 404

    async def test_get_all_playclocks_endpoint(self, client, test_db):
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
        match2 = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        playclock_service = PlayClockServiceDB(test_db)
        await playclock_service.create(
            PlayClockSchemaCreate(
                match_id=match.id, playclock=60, playclock_status="stopped"
            )
        )
        await playclock_service.create(
            PlayClockSchemaCreate(
                match_id=match2.id, playclock=90, playclock_status="stopped"
            )
        )

        response = await client.get("/api/playclock/")

        assert response.status_code == 200
        assert len(response.json()) == 2
