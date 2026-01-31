import pytest

from src.person.db_services import PersonServiceDB
from src.player.db_services import PlayerServiceDB
from src.player_team_tournament.db_services import PlayerTeamTournamentServiceDB
from src.player_team_tournament.schemas import (
    PlayerTeamTournamentSchemaCreate,
    PlayerTeamTournamentSchemaUpdate,
)
from src.positions.db_services import PositionServiceDB
from src.positions.schemas import PositionSchemaCreate
from src.seasons.db_services import SeasonServiceDB
from src.sports.db_services import SportServiceDB
from src.teams.db_services import TeamServiceDB
from src.tournaments.db_services import TournamentServiceDB
from tests.factories import (
    PersonFactory,
    PlayerFactory,
    SeasonFactorySample,
    SportFactorySample,
    TeamFactory,
    TournamentFactory,
)


@pytest.mark.asyncio
class TestPlayerTeamTournamentViewsMore:
    async def test_create_player_team_tournament_endpoint_exception(self, client, test_db):
        """Test create player team tournament with general exception."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team = await team_service.create(TeamFactory.build(sport_id=sport.id))

        position_service = PositionServiceDB(test_db)
        position = await position_service.create(
            PositionSchemaCreate(title="QB", sport_id=sport.id)
        )

        player_service = PlayerServiceDB(test_db)
        player = await player_service.create_or_update_player(PlayerFactory.build())

        ptt_data = PlayerTeamTournamentSchemaCreate(
            player_id=player.id,
            position_id=position.id,
            team_id=team.id,
            tournament_id=tournament.id,
            player_team_tournament_eesl_id=100,
        )

        from unittest.mock import patch

        async def mock_create_exception(*args, **kwargs):
            raise Exception("General exception")

        with patch.object(
            PlayerTeamTournamentServiceDB,
            "create_or_update_player_team_tournament",
            side_effect=mock_create_exception,
        ):
            response = await client.post(
                "/api/players_team_tournament/", json=ptt_data.model_dump()
            )

        assert response.status_code == 500

    async def test_create_player_team_tournament_endpoint_creation_fail(self, client, test_db):
        """Test create player team tournament when creation fails."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team = await team_service.create(TeamFactory.build(sport_id=sport.id))

        position_service = PositionServiceDB(test_db)
        position = await position_service.create(
            PositionSchemaCreate(title="QB", sport_id=sport.id)
        )

        player_service = PlayerServiceDB(test_db)
        player = await player_service.create_or_update_player(PlayerFactory.build())

        ptt_data = PlayerTeamTournamentSchemaCreate(
            player_id=player.id,
            position_id=position.id,
            team_id=team.id,
            tournament_id=tournament.id,
            player_team_tournament_eesl_id=100,
        )

        from unittest.mock import patch

        async def mock_create_none(*args, **kwargs):
            return None

        with patch.object(
            PlayerTeamTournamentServiceDB,
            "create_or_update_player_team_tournament",
            side_effect=mock_create_none,
        ):
            response = await client.post(
                "/api/players_team_tournament/", json=ptt_data.model_dump()
            )

        assert response.status_code == 409

    async def test_get_player_team_tournament_by_eesl_id_exception(self, client, test_db):
        """Test get by eesl_id with general exception."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team = await team_service.create(TeamFactory.build(sport_id=sport.id))

        position_service = PositionServiceDB(test_db)
        position = await position_service.create(
            PositionSchemaCreate(title="QB", sport_id=sport.id)
        )

        player_service = PlayerServiceDB(test_db)
        player = await player_service.create_or_update_player(PlayerFactory.build())

        ptt_service = PlayerTeamTournamentServiceDB(test_db)
        ptt_data = PlayerTeamTournamentSchemaCreate(
            player_id=player.id,
            position_id=position.id,
            team_id=team.id,
            tournament_id=tournament.id,
            player_team_tournament_eesl_id=100,
        )
        await ptt_service.create_or_update_player_team_tournament(ptt_data)

        from unittest.mock import patch

        async def mock_get_exception(*args, **kwargs):
            raise Exception("General exception")

        with patch.object(
            PlayerTeamTournamentServiceDB,
            "get_player_team_tournament_by_eesl_id",
            side_effect=mock_get_exception,
        ):
            response = await client.get("/api/players_team_tournament/eesl_id/100")

        assert response.status_code == 500

    async def test_update_player_team_tournament_endpoint_exception(self, client, test_db):
        """Test update player team tournament with general exception."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team = await team_service.create(TeamFactory.build(sport_id=sport.id))

        position_service = PositionServiceDB(test_db)
        position = await position_service.create(
            PositionSchemaCreate(title="QB", sport_id=sport.id)
        )

        player_service = PlayerServiceDB(test_db)
        player = await player_service.create_or_update_player(PlayerFactory.build())

        ptt_service = PlayerTeamTournamentServiceDB(test_db)
        ptt_data = PlayerTeamTournamentSchemaCreate(
            player_id=player.id,
            position_id=position.id,
            team_id=team.id,
            tournament_id=tournament.id,
        )
        created = await ptt_service.create_or_update_player_team_tournament(ptt_data)

        update_data = PlayerTeamTournamentSchemaUpdate(player_number="99")

        from unittest.mock import patch

        async def mock_update_exception(*args, **kwargs):
            raise Exception("General exception")

        with patch.object(
            PlayerTeamTournamentServiceDB,
            "update",
            side_effect=mock_update_exception,
        ):
            response = await client.put(
                f"/api/players_team_tournament/{created.id}/", json=update_data.model_dump()
            )

        assert response.status_code == 500

    async def test_get_player_team_tournament_with_person_not_found(self, client):
        """Test get player team tournament with person when not found."""
        response = await client.get("/api/players_team_tournament/id/99999/person/")

        assert response.status_code == 404

    async def test_get_player_team_tournament_with_person_exception(self, client, test_db):
        """Test get player team tournament with person with exception."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team = await team_service.create(TeamFactory.build(sport_id=sport.id))

        position_service = PositionServiceDB(test_db)
        position = await position_service.create(
            PositionSchemaCreate(title="QB", sport_id=sport.id)
        )

        player_service = PlayerServiceDB(test_db)
        player = await player_service.create_or_update_player(PlayerFactory.build())

        ptt_service = PlayerTeamTournamentServiceDB(test_db)
        ptt_data = PlayerTeamTournamentSchemaCreate(
            player_id=player.id,
            position_id=position.id,
            team_id=team.id,
            tournament_id=tournament.id,
        )
        created = await ptt_service.create_or_update_player_team_tournament(ptt_data)

        from unittest.mock import patch

        async def mock_get_exception(*args, **kwargs):
            raise Exception("General exception")

        with patch.object(
            PlayerTeamTournamentServiceDB,
            "get_player_team_tournament_with_person",
            side_effect=mock_get_exception,
        ):
            response = await client.get(f"/api/players_team_tournament/id/{created.id}/person/")

        assert response.status_code == 500

    async def test_create_parsed_players_to_team_tournament_endpoint_no_players(
        self, client, test_db, monkeypatch
    ):
        """Test create parsed players when no players found."""
        from src.pars_eesl.parse_player_team_tournament import ParsedPlayerTeamTournament

        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team = await team_service.create(TeamFactory.build(sport_id=sport.id))

        async def mock_parse(*args, **kwargs):
            return []

        monkeypatch.setattr(
            "src.player_team_tournament.views.parse_players_from_team_tournament_eesl_and_create_jsons",
            mock_parse,
        )

        response = await client.put(
            f"/api/players_team_tournament/pars_and_create/tournament/{tournament.id}/team/id/{team.id}/players"
        )

        assert response.status_code == 404

    async def test_create_parsed_players_to_team_tournament_endpoint_exception(
        self, client, test_db, monkeypatch
    ):
        """Test create parsed players with exception."""
        from src.pars_eesl.parse_player_team_tournament import ParsedPlayerTeamTournament

        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team = await team_service.create(TeamFactory.build(sport_id=sport.id))

        async def mock_parse_exception(*args, **kwargs):
            raise Exception("Parse error")

        monkeypatch.setattr(
            "src.player_team_tournament.views.parse_players_from_team_tournament_eesl_and_create_jsons",
            mock_parse_exception,
        )

        response = await client.put(
            f"/api/players_team_tournament/pars_and_create/tournament/{tournament.id}/team/id/{team.id}/players"
        )

        assert response.status_code == 500

    async def test_get_tournament_players_paginated_with_empty_result(self, client, test_db):
        """Test paginated tournament players when no players exist."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        response = await client.get(
            f"/api/players_team_tournament/tournament/{tournament.id}/players/paginated"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["total_items"] == 0
        assert len(data["data"]) == 0

    async def test_get_tournament_players_paginated_details_with_empty_result(
        self, client, test_db
    ):
        """Test paginated tournament players with details when no players exist."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        response = await client.get(
            f"/api/players_team_tournament/tournament/{tournament.id}/players/paginated/details"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["total_items"] == 0
        assert len(data["data"]) == 0

    async def test_get_tournament_players_paginated_full_details_with_empty_result(
        self, client, test_db
    ):
        """Test paginated tournament players with full details when no players exist."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        response = await client.get(
            f"/api/players_team_tournament/tournament/{tournament.id}/players/paginated/full-details"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["total_items"] == 0
        assert len(data["data"]) == 0

    async def test_get_tournament_players_paginated_details_with_photos_with_empty_result(
        self, client, test_db
    ):
        """Test paginated tournament players with details and photos when no players exist."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        response = await client.get(
            f"/api/players_team_tournament/tournament/{tournament.id}/players/paginated/details-with-photos"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["total_items"] == 0
        assert len(data["data"]) == 0

    async def test_delete_player_team_tournament_endpoint_not_found(self, client):
        """Test delete player team tournament without auth returns 401."""
        response = await client.delete("/api/players_team_tournament/id/99999")

        assert response.status_code == 401
