import pytest

from src.matches.db_services import MatchServiceDB
from src.matches.schemas import MatchSchemaCreate
from src.person.db_services import PersonServiceDB
from src.person.schemas import PersonSchemaCreate
from src.player.db_services import PlayerServiceDB
from src.player.schemas import PlayerSchemaCreate
from src.player_match.db_services import PlayerMatchServiceDB
from src.player_match.schemas import PlayerMatchSchemaCreate
from src.player_team_tournament.db_services import PlayerTeamTournamentServiceDB
from src.player_team_tournament.schemas import PlayerTeamTournamentSchemaCreate
from src.positions.db_services import PositionServiceDB
from src.positions.schemas import PositionSchemaCreate
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
class TestTeamRostersEndpoint:
    async def test_get_team_rosters_success(self, client, test_db):
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
        match = await match_service.create_or_update_match(match_data)

        person_service = PersonServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)
        ptt_service = PlayerTeamTournamentServiceDB(test_db)
        position_service = PositionServiceDB(test_db)

        position = await position_service.create(
            PositionSchemaCreate(title="QB", sport_id=sport.id)
        )

        person1 = await person_service.create(
            PersonSchemaCreate(first_name="Tom", second_name="Brady")
        )
        player1 = await player_service.create(
            PlayerSchemaCreate(person_id=person1.id, eesl_id=1, height="188", weight="102")
        )
        ptt1 = await ptt_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player1.id,
                team_id=team_a.id,
                tournament_id=tournament.id,
                player_number="12",
                position_id=position.id,
            )
        )

        person2 = await person_service.create(
            PersonSchemaCreate(first_name="Patrick", second_name="Mahomes")
        )
        player2 = await player_service.create(
            PlayerSchemaCreate(person_id=person2.id, eesl_id=2, height="188", weight="104")
        )
        _ = await ptt_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player2.id,
                team_id=team_b.id,
                tournament_id=tournament.id,
                player_number="15",
                position_id=position.id,
            )
        )

        player_match_service = PlayerMatchServiceDB(test_db)
        _ = await player_match_service.create_new_player_match(
            PlayerMatchSchemaCreate(
                match_id=match.id,
                player_team_tournament_id=ptt1.id,
                team_id=team_a.id,
                is_starting=True,
                starting_type="offense",
            )
        )

        response = await client.get(
            f"/api/matches/id/{match.id}/team-rosters/?include_available=true&include_match_players=true"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["match_id"] == match.id
        assert len(data["home_roster"]) == 1
        assert len(data["away_roster"]) == 0
        assert data["home_roster"][0]["player_id"] == player1.id
        assert data["home_roster"][0]["is_home_team"] is True
        assert len(data["available_home"]) == 0
        assert len(data["available_away"]) == 1
        assert data["available_away"][0]["player_id"] == player2.id

    async def test_get_team_rosters_not_found(self, client):
        response = await client.get("/api/matches/id/99999/team-rosters/")

        assert response.status_code == 404

    async def test_get_team_rosters_no_match_players(self, client, test_db):
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
        match = await match_service.create_or_update_match(match_data)

        person_service = PersonServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)
        ptt_service = PlayerTeamTournamentServiceDB(test_db)

        person1 = await person_service.create(
            PersonSchemaCreate(first_name="Tom", second_name="Brady")
        )
        player1 = await player_service.create(
            PlayerSchemaCreate(person_id=person1.id, eesl_id=1, height="188", weight="102")
        )
        await ptt_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player1.id,
                team_id=team_a.id,
                tournament_id=tournament.id,
                player_number="12",
            )
        )

        response = await client.get(
            f"/api/matches/id/{match.id}/team-rosters/?include_available=true&include_match_players=false"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["match_id"] == match.id
        assert len(data["home_roster"]) == 0
        assert len(data["away_roster"]) == 0
        assert len(data["available_home"]) == 1
        assert len(data["available_away"]) == 0

    async def test_get_team_rosters_no_available(self, client, test_db):
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
        match = await match_service.create_or_update_match(match_data)

        person_service = PersonServiceDB(test_db)
        player_service = PlayerServiceDB(test_db)
        ptt_service = PlayerTeamTournamentServiceDB(test_db)
        position_service = PositionServiceDB(test_db)

        position = await position_service.create(
            PositionSchemaCreate(title="QB", sport_id=sport.id)
        )

        person1 = await person_service.create(
            PersonSchemaCreate(first_name="Tom", second_name="Brady")
        )
        player1 = await player_service.create(
            PlayerSchemaCreate(person_id=person1.id, eesl_id=1, height="188", weight="102")
        )
        ptt1 = await ptt_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player1.id,
                team_id=team_a.id,
                tournament_id=tournament.id,
                player_number="12",
                position_id=position.id,
            )
        )

        player_match_service = PlayerMatchServiceDB(test_db)
        await player_match_service.create_new_player_match(
            PlayerMatchSchemaCreate(
                match_id=match.id,
                player_team_tournament_id=ptt1.id,
                team_id=team_a.id,
                is_starting=True,
                starting_type="offense",
            )
        )

        response = await client.get(
            f"/api/matches/id/{match.id}/team-rosters/?include_available=false&include_match_players=true"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["match_id"] == match.id
        assert len(data["home_roster"]) == 1
        assert len(data["away_roster"]) == 0
        assert len(data["available_home"]) == 0
        assert len(data["available_away"]) == 0
