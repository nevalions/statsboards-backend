from io import BytesIO

import pytest
from PIL import Image

from src.seasons.db_services import SeasonServiceDB
from src.sports.db_services import SportServiceDB
from src.teams.db_services import TeamServiceDB
from src.teams.schemas import TeamSchemaCreate as TeamSchemaCreateType
from src.tournaments.db_services import TournamentServiceDB
from src.tournaments.schemas import TournamentSchemaUpdate
from tests.factories import SeasonFactorySample, SportFactorySample, TournamentFactory


def create_test_image():
    img = Image.new("RGB", (100, 100), color="red")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


@pytest.mark.asyncio
class TestTournamentViews:
    async def test_create_tournament_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_data = TournamentFactory.build(sport_id=sport.id, season_id=season.id)

        response = await client.post("/api/tournaments/", json=tournament_data.model_dump())

        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_update_tournament_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament_data = TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        created = await tournament_service.create_or_update_tournament(tournament_data)

        update_data = TournamentSchemaUpdate(title="Updated Title")

        response = await client.put(
            f"/api/tournaments/{created.id}/", json=update_data.model_dump()
        )

        assert response.status_code == 200

    async def test_update_tournament_not_found(self, client):
        update_data = TournamentSchemaUpdate(title="Updated Title")

        response = await client.put("/api/tournaments/99999/", json=update_data.model_dump())

        assert response.status_code == 404

    async def test_get_tournament_by_eesl_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament_data = TournamentFactory.build(
            sport_id=sport.id, season_id=season.id, tournament_eesl_id=100
        )
        created = await tournament_service.create_or_update_tournament(tournament_data)

        response = await client.get("/api/tournaments/eesl_id/100")

        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_tournament_by_eesl_id_not_found(self, client):
        response = await client.get("/api/tournaments/eesl_id/99999")

        assert response.status_code == 404

    async def test_get_teams_by_tournament_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        response = await client.get(f"/api/tournaments/id/{tournament.id}/teams/")

        assert response.status_code == 200

    async def test_get_players_by_tournament_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        response = await client.get(f"/api/tournaments/id/{tournament.id}/players/")

        assert response.status_code == 200

    async def test_get_count_of_matches_by_tournament_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        response = await client.get(f"/api/tournaments/id/{tournament.id}/matches/count")

        assert response.status_code == 200

    async def test_get_matches_by_tournament_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        response = await client.get(f"/api/tournaments/id/{tournament.id}/matches/")

        assert response.status_code == 200

    async def test_get_all_tournaments_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )
        await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        response = await client.get("/api/tournaments/")

        assert response.status_code == 200
        assert len(response.json()) >= 2

    async def test_get_tournament_by_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament_data = TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        created = await tournament_service.create_or_update_tournament(tournament_data)

        response = await client.get(f"/api/tournaments/id/{created.id}")

        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_tournament_by_id_not_found(self, client):
        response = await client.get("/api/tournaments/id/99999")

        assert response.status_code == 404

    async def test_upload_tournament_logo_endpoint(self, client):
        file_content = create_test_image()
        files = {"file": ("test_logo.png", BytesIO(file_content), "image/png")}
        response = await client.post("/api/tournaments/upload_logo", files=files)

        assert response.status_code == 200
        assert "logoUrl" in response.json()
        assert "tournaments/logos" in response.json()["logoUrl"]

    async def test_upload_tournament_logo_with_invalid_file(self, client):
        file_content = b"not a valid image"
        files = {"file": ("test_invalid.txt", BytesIO(file_content), "text/plain")}
        response = await client.post("/api/tournaments/upload_logo", files=files)

        assert response.status_code == 400

    async def test_upload_and_resize_tournament_logo_endpoint(self, client):
        file_content = create_test_image()
        files = {"file": ("test_logo.png", BytesIO(file_content), "image/png")}
        response = await client.post("/api/tournaments/upload_resize_logo", files=files)

        assert response.status_code == 200
        response_data = response.json()
        assert "original" in response_data
        assert "icon" in response_data
        assert "webview" in response_data
        assert "tournaments/logos" in response_data["original"]
        assert "tournaments/logos" in response_data["icon"]
        assert "tournaments/logos" in response_data["webview"]

    async def test_upload_and_resize_tournament_logo_with_invalid_file(self, client):
        file_content = b"not a valid image"
        files = {"file": ("test_invalid.txt", BytesIO(file_content), "text/plain")}
        response = await client.post("/api/tournaments/upload_resize_logo", files=files)

        assert response.status_code == 400

    async def test_get_teams_by_tournament_paginated_endpoint(self, client, test_db):
        """Test GET /api/tournaments/id/{tournament_id}/teams/paginated endpoint."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team1 = await team_service.create_or_update_team(
            TeamSchemaCreateType(
                title="Manchester United",
                sport_id=sport.id,
                team_eesl_id=1001,
            )
        )
        team2 = await team_service.create_or_update_team(
            TeamSchemaCreateType(
                title="Manchester City",
                sport_id=sport.id,
                team_eesl_id=1002,
            )
        )
        team3 = await team_service.create_or_update_team(
            TeamSchemaCreateType(
                title="Liverpool",
                sport_id=sport.id,
                team_eesl_id=1003,
            )
        )

        from src.core.models.team_tournament import TeamTournamentDB

        async with test_db.async_session() as session:
            tt1 = TeamTournamentDB(tournament_id=tournament.id, team_id=team1.id)
            tt2 = TeamTournamentDB(tournament_id=tournament.id, team_id=team2.id)
            tt3 = TeamTournamentDB(tournament_id=tournament.id, team_id=team3.id)
            session.add_all([tt1, tt2, tt3])
            await session.commit()

        response = await client.get(f"/api/tournaments/id/{tournament.id}/teams/paginated")

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        assert "metadata" in response_data
        assert len(response_data["data"]) == 3
        assert response_data["metadata"]["total_items"] == 3
        assert response_data["metadata"]["page"] == 1
        assert response_data["metadata"]["items_per_page"] == 20

    async def test_get_teams_by_tournament_paginated_with_search_endpoint(self, client, test_db):
        """Test GET /api/tournaments/id/{tournament_id}/teams/paginated with search."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team1 = await team_service.create_or_update_team(
            TeamSchemaCreateType(
                title="Manchester United",
                sport_id=sport.id,
                team_eesl_id=1001,
            )
        )
        team2 = await team_service.create_or_update_team(
            TeamSchemaCreateType(
                title="Manchester City",
                sport_id=sport.id,
                team_eesl_id=1002,
            )
        )
        team3 = await team_service.create_or_update_team(
            TeamSchemaCreateType(
                title="Liverpool",
                sport_id=sport.id,
                team_eesl_id=1003,
            )
        )

        from src.core.models.team_tournament import TeamTournamentDB

        async with test_db.async_session() as session:
            tt1 = TeamTournamentDB(tournament_id=tournament.id, team_id=team1.id)
            tt2 = TeamTournamentDB(tournament_id=tournament.id, team_id=team2.id)
            tt3 = TeamTournamentDB(tournament_id=tournament.id, team_id=team3.id)
            session.add_all([tt1, tt2, tt3])
            await session.commit()

        response = await client.get(
            f"/api/tournaments/id/{tournament.id}/teams/paginated?search=Manchester"
        )

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        assert "metadata" in response_data
        assert len(response_data["data"]) == 2
        assert response_data["metadata"]["total_items"] == 2
        team_titles = [team["title"] for team in response_data["data"]]
        assert "Manchester United" in team_titles
        assert "Manchester City" in team_titles
        assert "Liverpool" not in team_titles

    async def test_get_teams_by_tournament_paginated_with_page_2_endpoint(self, client, test_db):
        """Test GET /api/tournaments/id/{tournament_id}/teams/paginated with page 2."""
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        teams_db = []
        for i in range(5):
            team = await team_service.create_or_update_team(
                TeamSchemaCreateType(
                    title=f"Team {i}",
                    sport_id=sport.id,
                    team_eesl_id=2000 + i,
                )
            )
            teams_db.append(team)

        from src.core.models.team_tournament import TeamTournamentDB

        async with test_db.async_session() as session:
            tt_entries = [
                TeamTournamentDB(tournament_id=tournament.id, team_id=team.id) for team in teams_db
            ]
            session.add_all(tt_entries)
            await session.commit()

        response = await client.get(
            f"/api/tournaments/id/{tournament.id}/teams/paginated?page=2&items_per_page=2"
        )

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        assert "metadata" in response_data
        assert len(response_data["data"]) == 2
        assert response_data["metadata"]["total_items"] == 5
        assert response_data["metadata"]["page"] == 2
        assert response_data["metadata"]["has_next"] is True
        assert response_data["metadata"]["has_previous"] is True

    async def test_get_available_players_for_tournament_endpoint(self, client, test_db):
        """Test retrieving available players for a tournament (not connected)."""
        from src.core.models.player_team_tournament import PlayerTeamTournamentDB
        from src.person.schemas import PersonSchemaCreate as PersonSchemaCreateType
        from src.player.schemas import PlayerSchemaCreate as PlayerSchemaCreateType

        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        from src.person.db_services import PersonServiceDB
        from src.player.db_services import PlayerServiceDB

        person_service = PersonServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)

        person1 = await person_service.create(
            PersonSchemaCreateType(first_name="John", second_name="Doe")
        )
        player1 = await player_service.create(
            PlayerSchemaCreateType(sport_id=sport.id, person_id=person1.id)
        )

        person2 = await person_service.create(
            PersonSchemaCreateType(first_name="Jane", second_name="Smith")
        )
        player2 = await player_service.create(
            PlayerSchemaCreateType(sport_id=sport.id, person_id=person2.id)
        )

        person3 = await person_service.create(
            PersonSchemaCreateType(first_name="Bob", second_name="Wilson")
        )
        player3 = await player_service.create(
            PlayerSchemaCreateType(sport_id=sport.id, person_id=person3.id)
        )

        async with test_db.async_session() as session:
            ptt = PlayerTeamTournamentDB(player_id=player1.id, tournament_id=tournament.id)
            session.add(ptt)
            await session.commit()

        response = await client.get(f"/api/tournaments/id/{tournament.id}/players/available")

        assert response.status_code == 200
        players = response.json()

        assert len(players) == 2
        player_ids = [p["id"] for p in players]
        assert player2.id in player_ids
        assert player3.id in player_ids
        assert player1.id not in player_ids
