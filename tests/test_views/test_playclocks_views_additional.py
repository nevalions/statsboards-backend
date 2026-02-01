import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.enums import ClockStatus
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


@pytest.mark.asyncio
class TestPlayClockViewsAdditional:
    async def test_create_playclock_endpoint_integrity_error(self, client, test_db):
        """Test create playclock with database integrity error."""
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
            match_id=match.id, playclock=60, playclock_status=ClockStatus.STOPPED
        )

        from unittest.mock import patch

        async def mock_create(*args, **kwargs):
            raise IntegrityError("INSERT INTO", "params", Exception("orig"))

        with patch.object(PlayClockServiceDB, "create", side_effect=mock_create):
            response = await client.post("/api/playclock/", json=playclock_data.model_dump())

        assert response.status_code == 500

    async def test_create_playclock_endpoint_sqlalchemy_error(self, client, test_db):
        """Test create playclock with SQLAlchemy error."""
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
            match_id=match.id, playclock=60, playclock_status=ClockStatus.STOPPED
        )

        from unittest.mock import patch

        async def mock_create(*args, **kwargs):
            raise SQLAlchemyError("Database error")

        with patch.object(PlayClockServiceDB, "create", side_effect=mock_create):
            response = await client.post("/api/playclock/", json=playclock_data.model_dump())

        assert response.status_code == 500

    async def test_update_playclock_endpoint_not_found(self, client, test_db):
        """Test update playclock when not found."""
        update_data = PlayClockSchemaUpdate(playclock=120)

        response = await client.put("/api/playclock/99999/", json=update_data.model_dump())

        assert response.status_code == 404

    async def test_get_playclock_by_id_endpoint_not_found(self, client):
        """Test get playclock by id when not found."""
        response = await client.get("/api/playclock/id/99999/")

        assert response.status_code == 404

    async def test_start_playclock_endpoint_success(self, client, test_db):
        """Test start playclock endpoint."""
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
            match_id=match.id, playclock=60, playclock_status=ClockStatus.STOPPED
        )
        created = await playclock_service.create(playclock_data)

        response = await client.put(f"/api/playclock/id/{created.id}/running/40/")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["content"]["playclock"] == 40
        assert data["content"]["playclock_status"] == "running"
        assert "server_time_ms" in data["content"]

    async def test_start_playclock_endpoint_not_found(self, client):
        """Test start playclock when playclock not found."""
        response = await client.put("/api/playclock/id/99999/running/40/")

        assert response.status_code == 404

    async def test_reset_playclock_endpoint_success(self, client, test_db):
        """Test reset playclock endpoint."""
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
            match_id=match.id, playclock=60, playclock_status=ClockStatus.RUNNING
        )
        created = await playclock_service.create(playclock_data)

        response = await client.put(f"/api/playclock/id/{created.id}/stopped/25/")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["content"]["playclock"] == 25
        assert data["content"]["playclock_status"] == "stopped"

    async def test_reset_playclock_endpoint_not_found(self, client):
        """Test reset playclock when playclock not found."""
        response = await client.put("/api/playclock/id/99999/stopped/25/")

        assert response.status_code == 404

    async def test_reset_playclock_stopped_endpoint_success(self, client, test_db):
        """Test reset playclock to stopped endpoint."""
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
            match_id=match.id, playclock=60, playclock_status=ClockStatus.RUNNING
        )
        created = await playclock_service.create(playclock_data)

        response = await client.put(f"/api/playclock/id/{created.id}/stopped/")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["content"]["playclock"] is None
        assert data["content"]["playclock_status"] == "stopped"

    async def test_reset_playclock_stopped_endpoint_not_found(self, client):
        """Test reset playclock to stopped when playclock not found."""
        response = await client.put("/api/playclock/id/99999/stopped/")

        assert response.status_code == 404

    async def test_delete_playclock_endpoint_unauthorized(self, client):
        """Test delete playclock without authentication."""
        response = await client.delete("/api/playclock/id/1")

        assert response.status_code == 401

    async def test_update_playclock_by_id_endpoint_success(self, client, test_db):
        """Test update playclock by id endpoint."""
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
            match_id=match.id, playclock=60, playclock_status=ClockStatus.STOPPED
        )
        created = await playclock_service.create(playclock_data)

        update_data = PlayClockSchemaUpdate(playclock=120)

        response = await client.put(
            f"/api/playclock/id/{created.id}/", json=update_data.model_dump()
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["content"]["playclock"] == 120

    async def test_update_playclock_by_id_endpoint_not_found(self, client):
        """Test update playclock by id when playclock not found."""
        update_data = PlayClockSchemaUpdate(playclock=120)

        response = await client.put("/api/playclock/id/99999/", json=update_data.model_dump())

        assert response.status_code == 404
