from datetime import datetime

import pytest

from src.football_events.db_services import FootballEventServiceDB
from src.football_events.schemas import FootballEventSchemaCreate
from src.matches.db_services import MatchServiceDB
from src.matches.schemas import MatchSchemaCreate, MatchSchemaUpdate
from src.person.db_services import PersonServiceDB
from src.person.schemas import PersonSchemaCreate
from src.player.db_services import PlayerServiceDB
from src.player.schemas import PlayerSchemaCreate
from src.player_match.db_services import PlayerMatchServiceDB
from src.player_match.schemas import PlayerMatchSchemaCreate
from src.player_team_tournament.db_services import PlayerTeamTournamentServiceDB
from src.player_team_tournament.schemas import PlayerTeamTournamentSchemaCreate
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

        response = await client.post("/api/matches/", json=match_data.model_dump(mode="json"))

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

        response = await client.put(f"/api/matches/{created.id}/", json=update_data.model_dump())

        assert response.status_code == 200

    async def test_update_match_not_found(self, client):
        update_data = MatchSchemaUpdate(week=2)

        response = await client.put("/api/matches/99999/", json=update_data.model_dump())

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
                tournament_id=tournament.id,
                team_a_id=team_a.id,
                team_b_id=team_b.id,
                match_date="2025-01-01",
                week=1,
            )
        )
        await match_service.create_or_update_match(
            MatchSchemaCreate(
                tournament_id=tournament.id,
                team_a_id=team_a.id,
                team_b_id=team_b.id,
                match_date="2025-01-01",
                week=2,
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
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date="2025-01-01",
            week=1,
        )
        created = await match_service.create_or_update_match(match_data)

        response = await client.get(f"/api/matches/id/{created.id}")

        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_match_by_id_not_found(self, client):
        response = await client.get("/api/matches/id/99999")

        assert response.status_code == 404

    async def test_get_match_stats_endpoint(self, client, test_db):
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
            MatchSchemaCreate(
                tournament_id=tournament.id,
                team_a_id=team_a.id,
                team_b_id=team_b.id,
                match_date="2025-01-01",
                week=1,
            )
        )

        person_service = PersonServiceDB(test_db)
        person_a = await person_service.create(
            PersonSchemaCreate(
                first_name="John",
                second_name="Doe",
                person_dob=datetime(2000, 1, 1),
            )
        )
        person_b = await person_service.create(
            PersonSchemaCreate(
                first_name="Jane",
                second_name="Smith",
                person_dob=datetime(2000, 1, 1),
            )
        )

        player_service = PlayerServiceDB(test_db)
        player_a = await player_service.create(
            PlayerSchemaCreate(sport_id=sport.id, person_id=person_a.id)
        )
        player_b = await player_service.create(
            PlayerSchemaCreate(sport_id=sport.id, person_id=person_b.id)
        )

        player_team_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        player_tournament_a = await player_team_tournament_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player_a.id,
                team_id=team_a.id,
                tournament_id=tournament.id,
                player_number="10",
            )
        )
        player_tournament_b = await player_team_tournament_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player_b.id,
                team_id=team_b.id,
                tournament_id=tournament.id,
                player_number="20",
            )
        )

        player_match_service = PlayerMatchServiceDB(test_db)
        player_match_a = await player_match_service.create_or_update_player_match(
            PlayerMatchSchemaCreate(
                player_match_eesl_id=100,
                player_team_tournament_id=player_tournament_a.id,
                match_id=match.id,
                team_id=team_a.id,
                match_number="10",
                is_start=True,
            )
        )
        player_match_b = await player_match_service.create_or_update_player_match(
            PlayerMatchSchemaCreate(
                player_match_eesl_id=101,
                player_team_tournament_id=player_tournament_b.id,
                match_id=match.id,
                team_id=team_b.id,
                match_number="20",
                is_start=True,
            )
        )

        football_event_service = FootballEventServiceDB(test_db)
        await football_event_service.create(
            FootballEventSchemaCreate(
                match_id=match.id,
                event_number=1,
                event_qtr=1,
                event_down=1,
                event_distance=10,
                offense_team=team_a.id,
                play_type="run",
                play_result="run",
                ball_on=20,
                ball_moved_to=30,
                run_player=player_match_a.id,
                event_qb=player_match_a.id,
            )
        )
        await football_event_service.create(
            FootballEventSchemaCreate(
                match_id=match.id,
                event_number=2,
                event_qtr=1,
                event_down=1,
                event_distance=15,
                offense_team=team_b.id,
                play_type="pass",
                play_result="completed",
                ball_on=20,
                ball_moved_to=35,
                pass_received_player=player_match_b.id,
                event_qb=player_match_b.id,
            )
        )

        response = await client.get(f"/api/matches/id/{match.id}/stats/")

        assert response.status_code == 200
        stats = response.json()
        assert "match_id" in stats
        assert stats["match_id"] == match.id
        assert "team_a" in stats
        assert "team_b" in stats
        assert "team_stats" in stats["team_a"]
        assert "offense_stats" in stats["team_a"]
        assert "qb_stats" in stats["team_a"]
        assert "defense_stats" in stats["team_a"]
        assert stats["team_a"]["team_stats"]["offence_yards"] == 10

    async def test_get_match_stats_no_events(self, client, test_db):
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
            MatchSchemaCreate(
                tournament_id=tournament.id,
                team_a_id=team_a.id,
                team_b_id=team_b.id,
                match_date="2025-01-01",
                week=1,
            )
        )

        response = await client.get(f"/api/matches/id/{match.id}/stats/")

        assert response.status_code == 200
        stats = response.json()
        assert "match_id" in stats
        assert stats["match_id"] == match.id
        assert "team_a" in stats
        assert "team_b" in stats
        assert stats["team_a"]["team_stats"]["offence_yards"] == 0
        assert stats["team_b"]["team_stats"]["offence_yards"] == 0

    async def test_get_match_stats_not_found(self, client):
        response = await client.get("/api/matches/id/99999/stats/")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
