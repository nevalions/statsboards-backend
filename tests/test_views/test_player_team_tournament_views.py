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
class TestPlayerTeamTournamentViews:
    async def test_create_player_team_tournament_endpoint(self, client_player, test_db):
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

        response = await client_player.post("/api/players_team_tournament/", json=ptt_data.model_dump())

        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_get_player_team_tournament_by_eesl_id_endpoint(self, client_player, test_db):
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

        from src.person.db_services import PersonServiceDB
        from tests.factories import PersonFactory

        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        player = await player_service.create_or_update_player(
            PlayerFactory.build(person_id=person.id)
        )

        ptt_service = PlayerTeamTournamentServiceDB(test_db)
        ptt_data = PlayerTeamTournamentSchemaCreate(
            player_id=player.id,
            position_id=position.id,
            team_id=team.id,
            tournament_id=tournament.id,
        )
        created = await ptt_service.create_or_update_player_team_tournament(ptt_data)

        update_data = PlayerTeamTournamentSchemaUpdate(player_number="99")

        response = await client_player.put(
            f"/api/players_team_tournament/{created.id}/", json=update_data.model_dump()
        )

        assert response.status_code == 200

    async def test_get_all_player_team_tournaments_endpoint(self, client_player, test_db):
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
        player1 = await player_service.create_or_update_player(PlayerFactory.build())
        player2 = await player_service.create_or_update_player(PlayerFactory.build())

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

        response = await client_player.get("/api/players_team_tournament/")

        assert response.status_code == 200
        assert len(response.json()) >= 2

    async def test_get_player_team_tournament_by_id_endpoint(self, client_player, test_db):
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

        response = await client_player.get(f"/api/players_team_tournament/id/{created.id}")

        assert response.status_code == 200

    async def test_get_player_team_tournament_by_id_not_found(self, client_player):
        response = await client_player.get("/api/players_team_tournament/id/99999")

        assert response.status_code == 404

    async def test_get_person_by_player_team_tournament_id_endpoint(self, client_player, test_db):
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

        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        player = await player_service.create_or_update_player(
            PlayerFactory.build(sport_id=sport.id, person_id=person.id)
        )

        ptt_service = PlayerTeamTournamentServiceDB(test_db)
        ptt_data = PlayerTeamTournamentSchemaCreate(
            player_id=player.id,
            position_id=position.id,
            team_id=team.id,
            tournament_id=tournament.id,
        )
        created = await ptt_service.create_or_update_player_team_tournament(ptt_data)

        response = await client_player.get(f"/api/players_team_tournament/id/{created.id}/person/")

        assert response.status_code == 200

    async def test_paginated_players_includes_team_null(self, client_player, test_db):
        """Test that paginated endpoint returns players with team_id: null."""
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
        player1 = await player_service.create_or_update_player(PlayerFactory.build())
        player2 = await player_service.create_or_update_player(PlayerFactory.build())

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
                team_id=None,
                tournament_id=tournament.id,
                player_number="2",
            )
        )

        response = await client_player.get(
            f"/api/players_team_tournament/tournament/{tournament.id}/players/paginated"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["total_items"] == 2
        assert len(data["data"]) == 2

        team_ids = [p["team_id"] for p in data["data"]]
        assert team.id in team_ids
        assert None in team_ids

    async def test_paginated_details_with_photos_includes_team_null(self, client_player, test_db):
        """Test that paginated with details and photos endpoint returns players with team_id: null."""
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
        player1 = await player_service.create_or_update_player(PlayerFactory.build())
        player2 = await player_service.create_or_update_player(PlayerFactory.build())

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
                team_id=None,
                tournament_id=tournament.id,
                player_number="2",
            )
        )

        response = await client_player.get(
            f"/api/players_team_tournament/tournament/{tournament.id}/players/paginated/details-with-photos"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["total_items"] == 2
        assert len(data["data"]) == 2

        team_titles = [p["team_title"] for p in data["data"]]
        assert team.title in team_titles
        assert None in team_titles

    async def test_paginated_full_details_includes_team_null(self, client_player, test_db):
        """Test that paginated with full details endpoint returns players with team_id: null."""
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
        player1 = await player_service.create_or_update_player(PlayerFactory.build())
        player2 = await player_service.create_or_update_player(PlayerFactory.build())

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
                team_id=None,
                tournament_id=tournament.id,
                player_number="2",
            )
        )

        response = await client_player.get(
            f"/api/players_team_tournament/tournament/{tournament.id}/players/paginated/full-details"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["total_items"] == 2
        assert len(data["data"]) == 2

        team_ids = [p["team_id"] for p in data["data"]]
        assert team.id in team_ids
        assert None in team_ids
