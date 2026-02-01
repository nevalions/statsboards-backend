from typing import TypeVar

import pytest

from src.matches.db_services import MatchServiceDB
from src.person.db_services import PersonServiceDB
from src.player.db_services import PlayerServiceDB
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
    MatchFactory,
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
class TestPlayerMatchViewsAdditional:
    async def test_get_player_in_match_full_data_endpoint(self, client, test_db):
        """Test get player in match full data endpoint."""
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
        ptt = _require(
            await ptt_service.create(
                PlayerTeamTournamentSchemaCreate(
                    player_id=player.id,
                    position_id=position.id,
                    team_id=team.id,
                    tournament_id=tournament.id,
                )
            )
        )

        match_service = MatchServiceDB(test_db)
        match = _require(
            await match_service.create(
                MatchFactory.build(
                    tournament_id=tournament.id, team_a_id=team.id, team_b_id=team.id
                )
            )
        )

        player_match_service = PlayerMatchServiceDB(test_db)
        player_match = _require(
            await player_match_service.create_or_update_player_match(
                PlayerMatchSchemaCreate(
                    player_match_eesl_id=100,
                    player_team_tournament_id=ptt.id,
                    match_position_id=position.id,
                    match_id=match.id,
                    team_id=team.id,
                )
            )
        )

        response = await client.get(f"/api/players_match/id/{player_match.id}/full_data/")

        assert response.status_code == 200

    async def test_get_player_in_sport_endpoint_success(self, client, test_db):
        """Test get player in sport endpoint."""
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
        player = _require(
            await player_service.create_or_update_player(PlayerFactory.build(sport_id=sport.id))
        )

        ptt_service = PlayerTeamTournamentServiceDB(test_db)
        ptt = _require(
            await ptt_service.create(
                PlayerTeamTournamentSchemaCreate(
                    player_id=player.id,
                    position_id=position.id,
                    team_id=team.id,
                    tournament_id=tournament.id,
                )
            )
        )

        match_service = MatchServiceDB(test_db)
        match = _require(
            await match_service.create(
                MatchFactory.build(
                    tournament_id=tournament.id, team_a_id=team.id, team_b_id=team.id
                )
            )
        )

        player_match_service = PlayerMatchServiceDB(test_db)
        player_match = _require(
            await player_match_service.create_or_update_player_match(
                PlayerMatchSchemaCreate(
                    player_match_eesl_id=100,
                    player_team_tournament_id=ptt.id,
                    match_position_id=position.id,
                    match_id=match.id,
                    team_id=team.id,
                )
            )
        )

        response = await client.get(f"/api/players_match/id/{player_match.id}/player_in_sport/")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == player.id
        assert data["sport_id"] == sport.id

    async def test_get_player_in_team_tournament_endpoint_success(self, client, test_db):
        """Test get player in team tournament endpoint."""
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
        ptt = _require(
            await ptt_service.create(
                PlayerTeamTournamentSchemaCreate(
                    player_id=player.id,
                    position_id=position.id,
                    team_id=team.id,
                    tournament_id=tournament.id,
                )
            )
        )

        match_service = MatchServiceDB(test_db)
        match = _require(
            await match_service.create(
                MatchFactory.build(
                    tournament_id=tournament.id, team_a_id=team.id, team_b_id=team.id
                )
            )
        )

        player_match_service = PlayerMatchServiceDB(test_db)
        player_match = await player_match_service.create_or_update_player_match(
            PlayerMatchSchemaCreate(
                player_match_eesl_id=100,
                player_team_tournament_id=ptt.id,
                match_position_id=position.id,
                match_id=match.id,
                team_id=team.id,
            )
        )

        response = await client.get(
            f"/api/players_match/id/{player_match.id}/player_in_team_tournament/"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ptt.id
        assert data["team_id"] == team.id
        assert data["tournament_id"] == tournament.id

    async def test_create_player_match_endpoint_error_handling(self, client, test_db):
        """Test create player match endpoint error handling."""
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

        player_service = PlayerServiceDB(test_db)
        player = _require(await player_service.create_or_update_player(PlayerFactory.build()))

        ptt_service = PlayerTeamTournamentServiceDB(test_db)
        ptt = _require(
            await ptt_service.create(
                PlayerTeamTournamentSchemaCreate(
                    player_id=player.id,
                    position_id=position.id,
                    team_id=team.id,
                    tournament_id=tournament.id,
                )
            )
        )

        match_service = MatchServiceDB(test_db)
        match = _require(
            await match_service.create(
                MatchFactory.build(
                    tournament_id=tournament.id, team_a_id=team.id, team_b_id=team.id
                )
            )
        )

        player_match_data = PlayerMatchSchemaCreate(
            player_match_eesl_id=100,
            player_team_tournament_id=ptt.id,
            match_position_id=position.id,
            match_id=match.id,
            team_id=team.id,
        )

        response = await client.post("/api/players_match/", json=player_match_data.model_dump())

        assert response.status_code == 200

    async def test_update_player_match_endpoint_not_found(self, client):
        """Test update player match when not found."""
        from src.player_match.schemas import PlayerMatchSchemaUpdate

        update_data = PlayerMatchSchemaUpdate(match_number="99")

        response = await client.put("/api/players_match/99999/", json=update_data.model_dump())

        assert response.status_code == 404

    async def test_get_all_player_matches_endpoint_empty(self, client):
        """Test get all player matches when none exist."""
        response = await client.get("/api/players_match/")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_player_match_by_id_not_found(self, client):
        """Test get player match by id when not found."""
        response = await client.get("/api/players_match/id/99999")

        assert response.status_code == 404

    async def test_delete_player_match_endpoint_unauthorized(self, client):
        """Test delete player match without authentication."""
        response = await client.delete("/api/players_match/id/1")

        assert response.status_code == 401
