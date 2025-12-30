import pytest
from src.player_match.db_services import PlayerMatchServiceDB
from src.player_match.schemas import PlayerMatchSchemaCreate, PlayerMatchSchemaUpdate
from src.matches.db_services import MatchServiceDB
from src.matches.schemas import MatchSchemaCreate
from src.teams.db_services import TeamServiceDB
from src.sports.db_services import SportServiceDB
from src.tournaments.db_services import TournamentServiceDB
from src.seasons.db_services import SeasonServiceDB
from src.positions.db_services import PositionServiceDB
from src.positions.schemas import PositionSchemaCreate
from src.player_team_tournament.db_services import PlayerTeamTournamentServiceDB
from src.player_team_tournament.schemas import PlayerTeamTournamentSchemaCreate
from src.player.db_services import PlayerServiceDB
from tests.factories import (
    MatchFactory,
    TeamFactory,
    TournamentFactory,
    SeasonFactorySample,
    SportFactorySample,
    PlayerFactory,
)
from src.logging_config import setup_logging

setup_logging()


@pytest.mark.asyncio
class TestPlayerMatchViews:
    async def test_create_player_match_endpoint(self, client, test_db):
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
        ptt = await ptt_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player.id,
                position_id=position.id,
                team_id=team.id,
                tournament_id=tournament.id,
            )
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team.id, team_b_id=team.id
            )
        )

        player_match_data = PlayerMatchSchemaCreate(
            player_match_eesl_id=100,
            player_team_tournament_id=ptt.id,
            match_position_id=position.id,
            match_id=match.id,
            team_id=team.id,
        )

        response = await client.post(
            "/api/players_match/", json=player_match_data.model_dump()
        )

        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_get_player_match_by_eesl_id_endpoint(self, client, test_db):
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
        ptt = await ptt_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player.id,
                position_id=position.id,
                team_id=team.id,
                tournament_id=tournament.id,
            )
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team.id, team_b_id=team.id
            )
        )

        player_match_service = PlayerMatchServiceDB(test_db)
        player_match_data = PlayerMatchSchemaCreate(
            player_match_eesl_id=100,
            player_team_tournament_id=ptt.id,
            match_position_id=position.id,
            match_id=match.id,
            team_id=team.id,
        )
        created = await player_match_service.create_or_update_player_match(
            player_match_data
        )

        response = await client.get("/api/players_match/eesl_id/100")

        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_player_match_by_eesl_id_not_found(self, client):
        response = await client.get("/api/players_match/eesl_id/99999")

        assert response.status_code == 404

    async def test_update_player_match_endpoint(self, client, test_db):
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
        ptt = await ptt_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player.id,
                position_id=position.id,
                team_id=team.id,
                tournament_id=tournament.id,
            )
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team.id, team_b_id=team.id
            )
        )

        player_match_service = PlayerMatchServiceDB(test_db)
        player_match_data = PlayerMatchSchemaCreate(
            player_match_eesl_id=100,
            player_team_tournament_id=ptt.id,
            match_position_id=position.id,
            match_id=match.id,
            team_id=team.id,
        )
        created = await player_match_service.create_or_update_player_match(
            player_match_data
        )

        update_data = PlayerMatchSchemaUpdate(match_number="99")

        response = await client.put(
            f"/api/players_match/{created.id}/", json=update_data.model_dump()
        )

        assert response.status_code == 200

    async def test_get_all_player_matches_endpoint(self, client, test_db):
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
        ptt = await ptt_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player.id,
                position_id=position.id,
                team_id=team.id,
                tournament_id=tournament.id,
            )
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team.id, team_b_id=team.id
            )
        )

        player_match_service = PlayerMatchServiceDB(test_db)
        await player_match_service.create_or_update_player_match(
            PlayerMatchSchemaCreate(
                player_match_eesl_id=100,
                player_team_tournament_id=ptt.id,
                match_position_id=position.id,
                match_id=match.id,
                team_id=team.id,
            )
        )
        await player_match_service.create_or_update_player_match(
            PlayerMatchSchemaCreate(
                player_match_eesl_id=101,
                player_team_tournament_id=ptt.id,
                match_position_id=position.id,
                match_id=match.id,
                team_id=team.id,
            )
        )

        response = await client.get("/api/players_match/")

        assert response.status_code == 200
        assert len(response.json()) >= 2

    async def test_get_player_match_by_id_endpoint(self, client, test_db):
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
        ptt = await ptt_service.create(
            PlayerTeamTournamentSchemaCreate(
                player_id=player.id,
                position_id=position.id,
                team_id=team.id,
                tournament_id=tournament.id,
            )
        )

        match_service = MatchServiceDB(test_db)
        match = await match_service.create(
            MatchFactory.build(
                tournament_id=tournament.id, team_a_id=team.id, team_b_id=team.id
            )
        )

        player_match_service = PlayerMatchServiceDB(test_db)
        player_match_data = PlayerMatchSchemaCreate(
            player_match_eesl_id=100,
            player_team_tournament_id=ptt.id,
            match_position_id=position.id,
            match_id=match.id,
            team_id=team.id,
        )
        created = await player_match_service.create_or_update_player_match(
            player_match_data
        )

        response = await client.get(f"/api/players_match/id/{created.id}")

        assert response.status_code == 200

    async def test_get_player_match_by_id_not_found(self, client):
        response = await client.get("/api/players_match/id/99999")

        assert response.status_code == 404
