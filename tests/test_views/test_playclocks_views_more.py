import pytest

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
class TestPlayClockViewsMore:
    async def test_create_playclock_endpoint_exception(self, client, test_db):
        """Test create playclock with general exception."""
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

        async def mock_create_exception(*args, **kwargs):
            raise Exception("General exception")

        with patch.object(PlayClockServiceDB, "create", side_effect=mock_create_exception):
            response = await client.post("/api/playclock/", json=playclock_data.model_dump())

        assert response.status_code == 500

    async def test_update_playclock_endpoint_exception(self, client, test_db):
        """Test update playclock with general exception."""
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

        from unittest.mock import patch

        async def mock_update_exception(*args, **kwargs):
            raise Exception("General exception")

        with patch.object(PlayClockServiceDB, "update", side_effect=mock_update_exception):
            response = await client.put(
                f"/api/playclock/{created.id}/", json=update_data.model_dump()
            )

        assert response.status_code == 500

    async def test_start_playclock_endpoint_integrity_error(self, client, test_db):
        """Test start playclock with integrity error."""
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

        from unittest.mock import patch

        from sqlalchemy.exc import IntegrityError

        async def mock_update_integrity(*args, **kwargs):
            raise IntegrityError("UPDATE", "params", Exception("orig"))

        with patch.object(PlayClockServiceDB, "update", side_effect=mock_update_integrity):
            response = await client.put(f"/api/playclock/id/{created.id}/running/40/")

        assert response.status_code == 500

    async def test_start_playclock_endpoint_sqlalchemy_error(self, client, test_db):
        """Test start playclock with SQLAlchemy error."""
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

        from unittest.mock import patch

        from sqlalchemy.exc import SQLAlchemyError

        async def mock_update_sqlalchemy(*args, **kwargs):
            raise SQLAlchemyError("Database error")

        with patch.object(PlayClockServiceDB, "update", side_effect=mock_update_sqlalchemy):
            response = await client.put(f"/api/playclock/id/{created.id}/running/40/")

        assert response.status_code == 500

    async def test_start_playclock_endpoint_exception(self, client, test_db):
        """Test start playclock with general exception."""
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

        from unittest.mock import patch

        async def mock_update_exception(*args, **kwargs):
            raise Exception("General exception")

        with patch.object(PlayClockServiceDB, "update", side_effect=mock_update_exception):
            response = await client.put(f"/api/playclock/id/{created.id}/running/40/")

        assert response.status_code == 500

    async def test_reset_playclock_endpoint_integrity_error(self, client, test_db):
        """Test reset playclock with integrity error."""
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

        from unittest.mock import patch

        from sqlalchemy.exc import IntegrityError

        async def mock_update_integrity(*args, **kwargs):
            raise IntegrityError("UPDATE", "params", Exception("orig"))

        with patch.object(PlayClockServiceDB, "update", side_effect=mock_update_integrity):
            response = await client.put(f"/api/playclock/id/{created.id}/stopped/25/")

        assert response.status_code == 500

    async def test_reset_playclock_endpoint_sqlalchemy_error(self, client, test_db):
        """Test reset playclock with SQLAlchemy error."""
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

        from unittest.mock import patch

        from sqlalchemy.exc import SQLAlchemyError

        async def mock_update_sqlalchemy(*args, **kwargs):
            raise SQLAlchemyError("Database error")

        with patch.object(PlayClockServiceDB, "update", side_effect=mock_update_sqlalchemy):
            response = await client.put(f"/api/playclock/id/{created.id}/stopped/25/")

        assert response.status_code == 500

    async def test_reset_playclock_endpoint_exception(self, client, test_db):
        """Test reset playclock with general exception."""
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

        from unittest.mock import patch

        async def mock_update_exception(*args, **kwargs):
            raise Exception("General exception")

        with patch.object(PlayClockServiceDB, "update", side_effect=mock_update_exception):
            response = await client.put(f"/api/playclock/id/{created.id}/stopped/25/")

        assert response.status_code == 500

    async def test_reset_playclock_stopped_endpoint_integrity_error(self, client, test_db):
        """Test reset playclock to stopped with integrity error."""
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

        from unittest.mock import patch

        from sqlalchemy.exc import IntegrityError

        async def mock_update_integrity(*args, **kwargs):
            raise IntegrityError("UPDATE", "params", Exception("orig"))

        with patch.object(
            PlayClockServiceDB, "update_with_none", side_effect=mock_update_integrity
        ):
            response = await client.put(f"/api/playclock/id/{created.id}/stopped/")

        assert response.status_code == 500

    async def test_reset_playclock_stopped_endpoint_sqlalchemy_error(self, client, test_db):
        """Test reset playclock to stopped with SQLAlchemy error."""
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

        from unittest.mock import patch

        from sqlalchemy.exc import SQLAlchemyError

        async def mock_update_sqlalchemy(*args, **kwargs):
            raise SQLAlchemyError("Database error")

        with patch.object(
            PlayClockServiceDB, "update_with_none", side_effect=mock_update_sqlalchemy
        ):
            response = await client.put(f"/api/playclock/id/{created.id}/stopped/")

        assert response.status_code == 500

    async def test_reset_playclock_stopped_endpoint_exception(self, client, test_db):
        """Test reset playclock to stopped with general exception."""
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

        from unittest.mock import patch

        async def mock_update_exception(*args, **kwargs):
            raise Exception("General exception")

        with patch.object(
            PlayClockServiceDB, "update_with_none", side_effect=mock_update_exception
        ):
            response = await client.put(f"/api/playclock/id/{created.id}/stopped/")

        assert response.status_code == 500

    async def test_update_playclock_by_id_endpoint_not_found_response(self, client, test_db):
        """Test update playclock by id returns 404 when not found."""
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

        from unittest.mock import patch

        async def mock_update_none(*args, **kwargs):
            return None

        with patch.object(PlayClockServiceDB, "update", side_effect=mock_update_none):
            response = await client.put(
                f"/api/playclock/id/{created.id}/", json=update_data.model_dump()
            )

        assert response.status_code == 404

    async def test_get_all_playclocks_endpoint_empty(self, client):
        """Test get all playclocks when none exist."""
        response = await client.get("/api/playclock/")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
