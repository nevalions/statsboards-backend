import pytest

from src.matches.db_services import MatchServiceDB
from src.scoreboards.db_services import ScoreboardServiceDB
from src.scoreboards.schemas import ScoreboardSchemaCreate, ScoreboardSchemaUpdate
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
class TestScoreboardViews:
    async def test_create_scoreboard_endpoint(self, client, test_db):
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

        scoreboard_data = ScoreboardSchemaCreate(
            match_id=match.id, is_qtr=True, is_time=True
        )

        response = await client.post(
            "/api/scoreboards/", json=scoreboard_data.model_dump()
        )

        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_update_scoreboard_endpoint(self, client, test_db):
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

        scoreboard_service = ScoreboardServiceDB(test_db)
        scoreboard_data = ScoreboardSchemaCreate(
            match_id=match.id, is_qtr=True, is_time=True
        )
        created = await scoreboard_service.create(scoreboard_data)

        update_data = ScoreboardSchemaUpdate(is_qtr=False)

        response = await client.put(
            f"/api/scoreboards/{created.id}/", json=update_data.model_dump()
        )

        assert response.status_code == 200

    async def test_update_scoreboard_not_found(self, client):
        update_data = ScoreboardSchemaUpdate(is_qtr=False)

        response = await client.put(
            "/api/scoreboards/99999/", json=update_data.model_dump()
        )

        assert response.status_code == 404

    async def test_get_scoreboard_by_match_id_endpoint(self, client, test_db):
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

        scoreboard_service = ScoreboardServiceDB(test_db)
        scoreboard_data = ScoreboardSchemaCreate(
            match_id=match.id, is_qtr=True, is_time=True
        )
        created = await scoreboard_service.create(scoreboard_data)

        response = await client.get(f"/api/scoreboards/match/id/{match.id}")

        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_scoreboard_by_match_id_not_found(self, client):
        response = await client.get("/api/scoreboards/match/id/99999")

        assert response.status_code == 404

    async def test_get_all_scoreboards_endpoint(self, client, test_db):
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
        match1 = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )
        match2 = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team_a.id, team_b_id=team_b.id
            )
        )

        scoreboard_service = ScoreboardServiceDB(test_db)
        await scoreboard_service.create(
            ScoreboardSchemaCreate(match_id=match1.id, is_qtr=True, is_time=True)
        )
        await scoreboard_service.create(
            ScoreboardSchemaCreate(match_id=match2.id, is_qtr=False, is_time=False)
        )

        response = await client.get("/api/scoreboards/")

        assert response.status_code == 200
        assert len(response.json()) >= 2

    async def test_get_scoreboard_by_id_endpoint(self, client, test_db):
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

        scoreboard_service = ScoreboardServiceDB(test_db)
        scoreboard_data = ScoreboardSchemaCreate(
            match_id=match.id, is_qtr=True, is_time=True
        )
        created = await scoreboard_service.create(scoreboard_data)

        response = await client.get(f"/api/scoreboards/id/{created.id}/")

        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_scoreboard_by_id_not_found(self, client):
        response = await client.get("/api/scoreboards/id/99999/")

        assert response.status_code == 404
