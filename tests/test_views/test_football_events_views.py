import pytest

from src.football_events.db_services import FootballEventServiceDB
from src.football_events.schemas import (
    FootballEventSchemaCreate,
    FootballEventSchemaUpdate,
)
from src.matches.db_services import MatchServiceDB
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
class TestFootballEventViews:
    async def test_create_football_event_endpoint(self, client, test_db):
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

        football_event_data = FootballEventSchemaCreate(
            match_id=match.id,
            event_number=1,
            event_qtr=1,
            event_down=1,
            event_distance=10,
        )

        response = await client.post("/api/football_event/", json=football_event_data.model_dump())

        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_update_football_event_endpoint(self, client, test_db):
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

        football_event_service = FootballEventServiceDB(test_db)
        football_event_data = FootballEventSchemaCreate(
            match_id=match.id,
            event_number=1,
            event_qtr=1,
            event_down=1,
            event_distance=10,
        )
        created = await football_event_service.create(football_event_data)

        update_data = FootballEventSchemaUpdate(event_distance=20)

        response = await client.put(
            f"/api/football_event/{created.id}/", json=update_data.model_dump()
        )

        assert response.status_code == 200

    async def test_update_football_event_not_found(self, client):
        update_data = FootballEventSchemaUpdate(event_distance=20)

        response = await client.put("/api/football_event/99999/", json=update_data.model_dump())

        assert response.status_code == 404

    async def test_get_football_events_by_match_id_endpoint(self, client, test_db):
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

        football_event_service = FootballEventServiceDB(test_db)
        await football_event_service.create(
            FootballEventSchemaCreate(match_id=match.id, event_number=1, event_qtr=1)
        )
        await football_event_service.create(
            FootballEventSchemaCreate(match_id=match.id, event_number=2, event_qtr=1)
        )

        response = await client.get(f"/api/football_event/match_id/{match.id}/")

        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_get_football_events_by_match_id_empty(self, client, test_db):
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

        response = await client.get(f"/api/football_event/match_id/{match.id}/")

        assert response.status_code == 200
        assert len(response.json()) == 0

    async def test_get_events_with_players_endpoint(self, client, test_db):
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

        football_event_service = FootballEventServiceDB(test_db)
        await football_event_service.create(
            FootballEventSchemaCreate(
                match_id=match.id,
                event_number=1,
                event_qtr=1,
                play_type="pass",
                play_result="pass_completed",
            )
        )

        response = await client.get(f"/api/football_event/matches/{match.id}/events-with-players/")

        assert response.status_code == 200
        data = response.json()
        assert data["match_id"] == match.id
        assert len(data["events"]) == 1

    async def test_get_events_with_players_empty(self, client, test_db):
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

        response = await client.get(f"/api/football_event/matches/{match.id}/events-with-players/")

        assert response.status_code == 200
        data = response.json()
        assert data["match_id"] == match.id
        assert len(data["events"]) == 0
