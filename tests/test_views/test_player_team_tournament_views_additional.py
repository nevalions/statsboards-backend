import pytest

from typing import TypeVar

from src.person.db_services import PersonServiceDB
from src.player.db_services import PlayerServiceDB
from src.player_team_tournament.db_services import PlayerTeamTournamentServiceDB
from src.player_team_tournament.schemas import PlayerTeamTournamentSchemaCreate
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

T = TypeVar("T")


def _require(value: T | None) -> T:
    assert value is not None
    return value


@pytest.mark.asyncio
class TestPlayerTeamTournamentViewsAdditional:
    async def test_get_player_team_tournament_by_eesl_id_endpoint(self, client, test_db):
        """Test get player team tournament by eesl_id endpoint."""
        sport_service = SportServiceDB(test_db)
        sport = _require(await sport_service.create(SportFactorySample.build()))

        season_service = SeasonServiceDB(test_db)
        season = _require(await season_service.create(SeasonFactorySample.build()))

        tournament_service = TournamentServiceDB(test_db)
        tournament = _require(
            await tournament_service.create(
                TournamentFactory.build(sport_id=sport.id, season_id=season.id)
            )
        )

        team_service = TeamServiceDB(test_db)
        team = _require(await team_service.create(TeamFactory.build(sport_id=sport.id)))

        position_service = PositionServiceDB(test_db)
        position = _require(
            await position_service.create(PositionSchemaCreate(title="QB", sport_id=sport.id))
        )

        person_service = PersonServiceDB(test_db)
        person = _require(await person_service.create_or_update_person(PersonFactory.build()))

        player_service = PlayerServiceDB(test_db)
        player = _require(
            await player_service.create_or_update_player(PlayerFactory.build(person_id=person.id))
        )

        ptt_service = PlayerTeamTournamentServiceDB(test_db)
        ptt_data = PlayerTeamTournamentSchemaCreate(
            player_id=player.id,
            position_id=position.id,
            team_id=team.id,
            tournament_id=tournament.id,
            player_team_tournament_eesl_id=100,
        )
        created = await ptt_service.create_or_update_player_team_tournament(ptt_data)

        response = await client.get("/api/players_team_tournament/eesl_id/100")

        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_player_team_tournament_by_eesl_id_not_found(self, client):
        """Test get player team tournament by eesl_id when not found."""
        response = await client.get("/api/players_team_tournament/eesl_id/99999")

        assert response.status_code == 404

    async def test_get_player_team_tournament_by_id_endpoint(self, client, test_db):
        """Test get player team tournament by id endpoint."""
        sport_service = SportServiceDB(test_db)
        sport = _require(await sport_service.create(SportFactorySample.build()))

        season_service = SeasonServiceDB(test_db)
        season = _require(await season_service.create(SeasonFactorySample.build()))

        tournament_service = TournamentServiceDB(test_db)
        tournament = _require(
            await tournament_service.create(
                TournamentFactory.build(sport_id=sport.id, season_id=season.id)
            )
        )

        team_service = TeamServiceDB(test_db)
        team = _require(await team_service.create(TeamFactory.build(sport_id=sport.id)))

        position_service = PositionServiceDB(test_db)
        position = _require(
            await position_service.create(PositionSchemaCreate(title="QB", sport_id=sport.id))
        )

        player_service = PlayerServiceDB(test_db)
        player = _require(await player_service.create_or_update_player(PlayerFactory.build()))

        ptt_service = PlayerTeamTournamentServiceDB(test_db)
        ptt_data = PlayerTeamTournamentSchemaCreate(
            player_id=player.id,
            position_id=position.id,
            team_id=team.id,
            tournament_id=tournament.id,
        )
        created = await ptt_service.create_or_update_player_team_tournament(ptt_data)

        response = await client.get(f"/api/players_team_tournament/id/{created.id}")

        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_player_team_tournament_by_id_not_found(self, client):
        """Test get player team tournament by id when not found."""
        response = await client.get("/api/players_team_tournament/id/99999")

        assert response.status_code == 404

    async def test_delete_player_team_tournament_unauthorized(self, client):
        """Test delete player team tournament without authentication."""
        response = await client.delete("/api/players_team_tournament/id/1")

        assert response.status_code == 401

    async def test_get_parse_player_to_team_tournament_endpoint(self, client, test_db):
        """Test parse player to team tournament endpoint."""
        sport_service = SportServiceDB(test_db)
        sport = _require(await sport_service.create(SportFactorySample.build()))

        season_service = SeasonServiceDB(test_db)
        season = _require(await season_service.create(SeasonFactorySample.build()))

        tournament_service = TournamentServiceDB(test_db)
        tournament = _require(
            await tournament_service.create(
                TournamentFactory.build(sport_id=sport.id, season_id=season.id)
            )
        )

        team_service = TeamServiceDB(test_db)
        team = _require(await team_service.create(TeamFactory.build(sport_id=sport.id)))

        response = await client.get(
            f"/api/players_team_tournament/pars/tournament/{tournament.id}/team/{team.id}"
        )

        assert response.status_code == 200

    async def test_get_tournament_players_paginated_with_search(self, client, test_db):
        """Test paginated tournament players with search filter."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = _require(
            await tournament_service.create(
                TournamentFactory.build(sport_id=sport.id, season_id=season.id)
            )
        )

        team_service = TeamServiceDB(test_db)
        team = _require(await team_service.create(TeamFactory.build(sport_id=sport.id)))

        position_service = PositionServiceDB(test_db)
        position = _require(
            await position_service.create(PositionSchemaCreate(title="QB", sport_id=sport.id))
        )

        person_service = PersonServiceDB(test_db)
        person1 = _require(
            await person_service.create_or_update_person(
                PersonFactory.build(first_name="John", second_name="Doe")
            )
        )
        person2 = _require(
            await person_service.create_or_update_person(
                PersonFactory.build(first_name="Jane", second_name="Smith")
            )
        )

        player_service = PlayerServiceDB(test_db)
        player1 = _require(
            await player_service.create_or_update_player(PlayerFactory.build(person_id=person1.id))
        )
        player2 = _require(
            await player_service.create_or_update_player(PlayerFactory.build(person_id=person2.id))
        )

        ptt_service = PlayerTeamTournamentServiceDB(test_db)
        await ptt_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player1.id,
                position_id=position.id,
                team_id=team.id,
                tournament_id=tournament.id,
                player_number="1",
            )
        )
        await ptt_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player2.id,
                position_id=position.id,
                team_id=team.id,
                tournament_id=tournament.id,
                player_number="2",
            )
        )

        response = await client.get(
            f"/api/players_team_tournament/tournament/{tournament.id}/players/paginated?search=John"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["total_items"] >= 1

    async def test_get_tournament_players_paginated_with_team_filter(self, client, test_db):
        """Test paginated tournament players with team filter."""
        sport_service = SportServiceDB(test_db)
        sport = _require(await sport_service.create(SportFactorySample.build()))

        season_service = SeasonServiceDB(test_db)
        season = _require(await season_service.create(SeasonFactorySample.build()))

        tournament_service = TournamentServiceDB(test_db)
        tournament = _require(
            await tournament_service.create(
                TournamentFactory.build(sport_id=sport.id, season_id=season.id)
            )
        )

        team_service = TeamServiceDB(test_db)
        team1 = _require(
            await team_service.create(TeamFactory.build(sport_id=sport.id, title="Team A"))
        )
        team2 = _require(
            await team_service.create(TeamFactory.build(sport_id=sport.id, title="Team B"))
        )

        position_service = PositionServiceDB(test_db)
        position = _require(
            await position_service.create(PositionSchemaCreate(title="QB", sport_id=sport.id))
        )

        player_service = PlayerServiceDB(test_db)
        player1 = _require(await player_service.create_or_update_player(PlayerFactory.build()))
        player2 = _require(await player_service.create_or_update_player(PlayerFactory.build()))

        ptt_service = PlayerTeamTournamentServiceDB(test_db)
        await ptt_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player1.id,
                position_id=position.id,
                team_id=team1.id,
                tournament_id=tournament.id,
                player_number="1",
            )
        )
        await ptt_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player2.id,
                position_id=position.id,
                team_id=team2.id,
                tournament_id=tournament.id,
                player_number="2",
            )
        )

        response = await client.get(
            f"/api/players_team_tournament/tournament/{tournament.id}/players/paginated?team_title=Team%20A"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["total_items"] >= 1
        for player in data["data"]:
            assert player["team_id"] == team1.id

    async def test_get_tournament_players_paginated_with_sorting(self, client, test_db):
        """Test paginated tournament players with sorting."""
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
        position = _require(
            await position_service.create(PositionSchemaCreate(title="QB", sport_id=sport.id))
        )

        player_service = PlayerServiceDB(test_db)
        player1 = _require(await player_service.create_or_update_player(PlayerFactory.build()))
        player2 = _require(await player_service.create_or_update_player(PlayerFactory.build()))

        ptt_service = PlayerTeamTournamentServiceDB(test_db)
        await ptt_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player1.id,
                position_id=position.id,
                team_id=team.id,
                tournament_id=tournament.id,
                player_number="10",
            )
        )
        await ptt_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player2.id,
                position_id=position.id,
                team_id=team.id,
                tournament_id=tournament.id,
                player_number="5",
            )
        )

        response = await client.get(
            f"/api/players_team_tournament/tournament/{tournament.id}/players/paginated?ascending=false"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["total_items"] >= 2

    async def test_get_tournament_players_paginated_with_pagination(self, client, test_db):
        """Test paginated tournament players with pagination."""
        sport_service = SportServiceDB(test_db)
        sport = _require(await sport_service.create(SportFactorySample.build()))

        season_service = SeasonServiceDB(test_db)
        season = _require(await season_service.create(SeasonFactorySample.build()))

        tournament_service = TournamentServiceDB(test_db)
        tournament = _require(
            await tournament_service.create(
                TournamentFactory.build(sport_id=sport.id, season_id=season.id)
            )
        )

        team_service = TeamServiceDB(test_db)
        team = _require(await team_service.create(TeamFactory.build(sport_id=sport.id)))

        position_service = PositionServiceDB(test_db)
        position = _require(
            await position_service.create(PositionSchemaCreate(title="QB", sport_id=sport.id))
        )

        player_service = PlayerServiceDB(test_db)
        for _ in range(5):
            player = _require(await player_service.create_or_update_player(PlayerFactory.build()))
            await PlayerTeamTournamentServiceDB(test_db).create(
                PlayerTeamTournamentSchemaCreate(
                    player_id=player.id,
                    position_id=position.id,
                    team_id=team.id,
                    tournament_id=tournament.id,
                )
            )

        response = await client.get(
            f"/api/players_team_tournament/tournament/{tournament.id}/players/paginated?page=1&items_per_page=3"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["total_items"] == 5
        assert data["metadata"]["page"] == 1
        assert data["metadata"]["items_per_page"] == 3
        assert len(data["data"]) == 3

    async def test_get_tournament_players_paginated_details_endpoint(self, client, test_db):
        """Test paginated tournament players with details endpoint."""
        sport_service = SportServiceDB(test_db)
        sport = _require(await sport_service.create(SportFactorySample.build()))

        season_service = SeasonServiceDB(test_db)
        season = _require(await season_service.create(SeasonFactorySample.build()))

        tournament_service = TournamentServiceDB(test_db)
        tournament = _require(
            await tournament_service.create(
                TournamentFactory.build(sport_id=sport.id, season_id=season.id)
            )
        )

        team_service = TeamServiceDB(test_db)
        team = _require(await team_service.create(TeamFactory.build(sport_id=sport.id)))

        position_service = PositionServiceDB(test_db)
        position = _require(
            await position_service.create(PositionSchemaCreate(title="QB", sport_id=sport.id))
        )

        player_service = PlayerServiceDB(test_db)
        player = _require(await player_service.create_or_update_player(PlayerFactory.build()))

        ptt_service = PlayerTeamTournamentServiceDB(test_db)
        await ptt_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player.id,
                position_id=position.id,
                team_id=team.id,
                tournament_id=tournament.id,
                player_number="1",
            )
        )

        response = await client.get(
            f"/api/players_team_tournament/tournament/{tournament.id}/players/paginated/details"
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "metadata" in data

    async def test_get_tournament_players_paginated_full_details_endpoint(self, client, test_db):
        """Test paginated tournament players with full details endpoint."""
        sport_service = SportServiceDB(test_db)
        sport = _require(await sport_service.create(SportFactorySample.build()))

        season_service = SeasonServiceDB(test_db)
        season = _require(await season_service.create(SeasonFactorySample.build()))

        tournament_service = TournamentServiceDB(test_db)
        tournament = _require(
            await tournament_service.create(
                TournamentFactory.build(sport_id=sport.id, season_id=season.id)
            )
        )

        team_service = TeamServiceDB(test_db)
        team = _require(await team_service.create(TeamFactory.build(sport_id=sport.id)))

        position_service = PositionServiceDB(test_db)
        position = _require(
            await position_service.create(PositionSchemaCreate(title="QB", sport_id=sport.id))
        )

        player_service = PlayerServiceDB(test_db)
        player = _require(await player_service.create_or_update_player(PlayerFactory.build()))

        ptt_service = PlayerTeamTournamentServiceDB(test_db)
        await ptt_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player.id,
                position_id=position.id,
                team_id=team.id,
                tournament_id=tournament.id,
                player_number="1",
            )
        )

        response = await client.get(
            f"/api/players_team_tournament/tournament/{tournament.id}/players/paginated/full-details"
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "metadata" in data
