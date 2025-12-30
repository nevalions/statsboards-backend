import pytest
from src.player_team_tournament.db_services import PlayerTeamTournamentServiceDB
from src.player_team_tournament.schemas import (
    PlayerTeamTournamentSchemaCreate,
    PlayerTeamTournamentSchemaUpdate,
)
from src.player.db_services import PlayerServiceDB
from src.player.schemas import PlayerSchemaCreate
from src.person.db_services import PersonServiceDB
from src.person.schemas import PersonSchemaCreate
from src.teams.db_services import TeamServiceDB
from src.sports.db_services import SportServiceDB
from src.tournaments.db_services import TournamentServiceDB
from src.seasons.db_services import SeasonServiceDB
from src.positions.db_services import PositionServiceDB
from src.positions.schemas import PositionSchemaCreate
from tests.factories import (
    TeamFactory,
    TournamentFactory,
    SeasonFactorySample,
    SportFactorySample,
    PersonFactory,
    PlayerFactory,
    PositionFactory,
)
from src.logging_config import setup_logging

setup_logging()


@pytest.mark.asyncio
class TestPlayerTeamTournamentServiceDB:
    async def test_create_player_team_tournament(self, test_db):
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

        person_service = PersonServiceDB(test_db)
        person = await person_service.create(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        player = await player_service.create(
            PlayerFactory.build(sport_id=sport.id, person_id=person.id)
        )

        position_service = PositionServiceDB(test_db)
        position = await position_service.create(
            PositionFactory.build(sport_id=sport.id)
        )

        player_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        player_tournament_data = PlayerTeamTournamentSchemaCreate(
            player_id=player.id,
            team_id=team.id,
            tournament_id=tournament.id,
            position_id=position.id,
            player_number="10",
        )

        result = await player_tournament_service.create_new_player_team_tournament(
            player_tournament_data
        )

        assert result is not None
        assert result.id is not None
        assert result.player_id == player.id

    async def test_create_or_update_player_team_tournament_with_eesl_id(self, test_db):
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

        person_service = PersonServiceDB(test_db)
        person = await person_service.create(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        player = await player_service.create(
            PlayerFactory.build(sport_id=sport.id, person_id=person.id)
        )

        player_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        player_tournament_data = PlayerTeamTournamentSchemaCreate(
            player_id=player.id,
            team_id=team.id,
            tournament_id=tournament.id,
            player_team_tournament_eesl_id=100,
        )

        result = (
            await player_tournament_service.create_or_update_player_team_tournament(
                player_tournament_data
            )
        )

        assert result is not None
        assert result.player_team_tournament_eesl_id == 100

    async def test_get_player_team_tournament_by_eesl_id(self, test_db):
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

        person_service = PersonServiceDB(test_db)
        person = await person_service.create(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        player = await player_service.create(
            PlayerFactory.build(sport_id=sport.id, person_id=person.id)
        )

        player_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        player_tournament_data = PlayerTeamTournamentSchemaCreate(
            player_id=player.id,
            team_id=team.id,
            tournament_id=tournament.id,
            player_team_tournament_eesl_id=200,
        )

        created = await player_tournament_service.create_new_player_team_tournament(
            player_tournament_data
        )
        result = await player_tournament_service.get_player_team_tournament_by_eesl_id(
            200
        )

        assert result is not None
        assert result.id == created.id

    async def test_get_player_team_tournaments_by_tournament_id(self, test_db):
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

        person_service = PersonServiceDB(test_db)
        person = await person_service.create(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        player = await player_service.create(
            PlayerFactory.build(sport_id=sport.id, person_id=person.id)
        )

        player_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        player_tournament_data = PlayerTeamTournamentSchemaCreate(
            player_id=player.id, team_id=team.id, tournament_id=tournament.id
        )

        created = await player_tournament_service.create_new_player_team_tournament(
            player_tournament_data
        )
        result = await player_tournament_service.get_player_team_tournaments_by_tournament_id(
            tournament.id, player.id
        )

        assert result is not None
        assert result.id == created.id

    async def test_update_player_team_tournament(self, test_db):
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

        person_service = PersonServiceDB(test_db)
        person = await person_service.create(PersonFactory.build())

        player_service = PlayerServiceDB(test_db)
        player = await player_service.create(
            PlayerFactory.build(sport_id=sport.id, person_id=person.id)
        )

        position_service = PositionServiceDB(test_db)
        position = await position_service.create(
            PositionFactory.build(sport_id=sport.id)
        )

        player_tournament_service = PlayerTeamTournamentServiceDB(test_db)
        player_tournament_data = PlayerTeamTournamentSchemaCreate(
            player_id=player.id,
            team_id=team.id,
            tournament_id=tournament.id,
            player_number="10",
        )

        created = await player_tournament_service.create_new_player_team_tournament(
            player_tournament_data
        )
        update_data = PlayerTeamTournamentSchemaUpdate(
            player_number="15", position_id=position.id
        )

        updated = await player_tournament_service.update(created.id, update_data)

        assert updated.player_number == "15"
        assert updated.position_id == position.id
